# app/routers/orders.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload # Importar joinedload para carregar relacionamentos
from typing import Optional, List
from datetime import datetime
from app.users import get_current_user, admin_required

# Importe seus modelos SQLAlchemy e Pydantic
from app.database import get_db
from app.models import (
    Order as DBOrder,
    Client as DBClient,
    Product as DBProduct,
    OrderProduct as DBOrderProduct
)
from app.schemas import OrderCreate, UpdateOrderStatus, Order, OrderProductCreate # Importe OrderProductCreate aqui

router = APIRouter(tags=["Pedidos"])

# Remova o dicionário em memória: pedidos = {}

@router.get("/", response_model=List[Order], summary="Listar todos os pedidos com filtros e paginação")
def list_orders(
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, description="Filtrar pedidos por status (ex: pending, completed)"),
    client_id: Optional[int] = Query(None, description="Filtrar pedidos por ID do cliente"),
    start_date: Optional[datetime] = Query(None, description="Filtrar pedidos a partir desta data (YYYY-MM-DDTHH:MM:SS)"),
    end_date: Optional[datetime] = Query(None, description="Filtrar pedidos até esta data (YYYY-MM-DDTHH:MM:SS)"),
    min_total_value: Optional[float] = Query(None, description="Filtrar pedidos com valor total mínimo"),
    max_total_value: Optional[float] = Query(None, description="Filtrar pedidos com valor total máximo"),
    skip: int = Query(0, ge=0, description="Número de pedidos a pular (offset)"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de pedidos por página"),
    current_user: dict = Depends(admin_required) # Admin pode ver todos os pedidos
):
    query = db.query(DBOrder).options(joinedload(DBOrder.order_products).joinedload(DBOrderProduct.product))

    if status_filter:
        query = query.filter(DBOrder.status == status_filter)
    if client_id:
        query = query.filter(DBOrder.client_id == client_id)
    if start_date:
        query = query.filter(DBOrder.order_date >= start_date)
    if end_date:
        query = query.filter(DBOrder.order_date <= end_date)
    if min_total_value is not None:
        query = query.filter(DBOrder.total_value >= min_total_value)
    if max_total_value is not None:
        query = query.filter(DBOrder.total_value <= max_total_value)

    orders_from_db = query.offset(skip).limit(limit).all()
    return orders_from_db

# Endpoint para usuários comuns verem seus próprios pedidos
@router.get("/my_orders", response_model=List[Order], summary="Listar pedidos do usuário autenticado")
def list_my_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user) # Requer apenas usuário logado, não necessariamente admin
):
    # Precisa buscar o ID do cliente associado ao usuário logado, se houver
    # Ou, se o seu modelo Order tiver um user_id diretamente, usar isso
    # Por enquanto, assumimos que o cliente_id está diretamente no token ou pode ser inferido
    # Exemplo: se o email do user logado corresponde ao email de um cliente
    user_email = current_user.get("sub")
    db_client = db.query(DBClient).filter(DBClient.email == user_email).first()
    if not db_client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado para o usuário logado.")

    orders_from_db = db.query(DBOrder).options(
        joinedload(DBOrder.order_products).joinedload(DBOrderProduct.product)
    ).filter(DBOrder.client_id == db_client.id).all()
    return orders_from_db


@router.post("/", response_model=Order, status_code=status.HTTP_201_CREATED, summary="Criar um novo pedido")
def create_order(
    order_data: OrderCreate, # Usa o modelo Pydantic para criação do pedido
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user) # Usuários logados podem criar pedidos
):
    # 1. Verificar se o cliente existe
    db_client = db.query(DBClient).filter(DBClient.id == order_data.client_id).first()
    if not db_client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente com ID {order_data.client_id} não encontrado."
        )

    # Opcional: Se a rota for apenas para usuários logados, garantir que o client_id corresponde ao user logado
    # if not current_user.get("is_admin"): # Se não for admin
    #     user_email = current_user.get("sub")
    #     auth_client = db.query(DBClient).filter(DBClient.email == user_email).first()
    #     if not auth_client or auth_client.id != order_data.client_id:
    #         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem permissão para criar pedidos para este cliente.")

    # 2. Criar o objeto Order
    db_order = DBOrder(
        client_id=order_data.client_id,
        notes=order_data.notes,
        status="pending", # Status inicial padrão
        total_value=0.0 # Será calculado
    )
    db.add(db_order)
    db.flush() # Flush para obter o ID do pedido antes de adicionar OrderProducts

    total_order_value = 0.0
    order_products_to_add = []

    # 3. Processar cada produto no pedido, validar estoque e criar OrderProduct
    for item in order_data.products:
        db_product = db.query(DBProduct).filter(DBProduct.id == item.product_id).first()
        if not db_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto com ID {item.product_id} não encontrado."
            )
        if db_product.current_stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estoque insuficiente para o produto '{db_product.description}'. Disponível: {db_product.current_stock}, Solicitado: {item.quantity}"
            )

        # Decrementar estoque
        db_product.current_stock -= item.quantity
        db.add(db_product) # Atualiza o produto no DB

        # Cria o item do pedido
        db_order_product = DBOrderProduct(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_order=db_product.sale_value # Registra o preço do produto no momento do pedido
        )
        order_products_to_add.append(db_order_product)
        total_order_value += item.quantity * db_product.sale_value

    db.add_all(order_products_to_add) # Adiciona todos os itens do pedido
    db_order.total_value = total_order_value # Atualiza o valor total do pedido
    db.add(db_order) # Marca o pedido para ser salvo/atualizado

    db.commit()      # Salva todas as mudanças no banco de dados (pedido, itens de pedido, estoque de produtos)
    db.refresh(db_order) # Atualiza o objeto db_order com seus relacionamentos carregados

    # Carrega os produtos relacionados para o retorno (o joinedload inicial no GET já faz isso, mas aqui para POST)
    db_order_final = db.query(DBOrder).options(
        joinedload(DBOrder.order_products).joinedload(DBOrderProduct.product)
    ).filter(DBOrder.id == db_order.id).first()

    return db_order_final # Retorna o objeto Order completo

@router.get("/{order_id}", response_model=Order, summary="Obter detalhes de um pedido específico")
def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(DBOrder).options(joinedload(DBOrder.order_products).joinedload(DBOrderProduct.product)).filter(DBOrder.id == order_id)

    # Se não for admin, filtre por cliente associado ao usuário logado
    if not current_user.get("is_admin"):
        user_email = current_user.get("sub")
        db_client = db.query(DBClient).filter(DBClient.email == user_email).first()
        if not db_client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado para o usuário logado.")
        query = query.filter(DBOrder.client_id == db_client.id)

    order = query.first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado ou você não tem permissão para acessá-lo.")
    return order

@router.put("/{order_id}/status", response_model=Order, summary="Atualizar o status de um pedido")
def update_order_status(
    order_id: int,
    status_update: UpdateOrderStatus,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required) # Apenas admin pode mudar o status
):
    db_order = db.query(DBOrder).filter(DBOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")

    # Opcional: Adicionar validação de status (ex: status_update.status in ["pending", "completed", "cancelled"])
    if status_update.status not in ["pending", "processing", "shipped", "delivered", "cancelled"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status inválido.")

    db_order.status = status_update.status
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Carrega os produtos relacionados para o retorno
    db_order_final = db.query(DBOrder).options(
        joinedload(DBOrder.order_products).joinedload(DBOrderProduct.product)
    ).filter(DBOrder.id == db_order.id).first()
    
    return db_order_final

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir um pedido")
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required) # Apenas admin pode excluir pedidos
):
    db_order = db.query(DBOrder).filter(DBOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")

    # Importante: Se você tem `ondelete="CASCADE"` configurado no SQLAlchemy para `OrderProduct`
    # na sua tabela `Order`, a exclusão dos itens do pedido será automática.
    # Caso contrário, você precisaria excluir os DBOrderProduct associados manualmente primeiro:
    # db.query(DBOrderProduct).filter(DBOrderProduct.order_id == order_id).delete()

    db.delete(db_order)
    db.commit()
    return {"message": f"Pedido {order_id} deletado."}