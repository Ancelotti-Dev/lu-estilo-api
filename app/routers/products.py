# app/routers/products.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date # Para data de validade
from app.users import get_current_user, admin_required

# Importe seus modelos SQLAlchemy e Pydantic
from app.database import get_db
from app.models import Product as DBProduct # Renomeie para evitar conflito com Pydantic Product
from app.schemas import ProductCreate, ProductUpdate, Product # Seus modelos Pydantic

# Importe suas dependências de autenticação

router = APIRouter(tags=["Produtos"])

# Remova o dicionário em memória: products = {}

@router.get("/", response_model=List[Product], summary="Listar todos os produtos com filtros")
def list_products(
    db: Session = Depends(get_db),
    description: Optional[str] = Query(None, description="Filtrar produtos por descrição (parcial)"),
    category: Optional[str] = Query(None, description="Filtrar produtos por categoria"), # Ajuste para 'section' se for o caso
    min_price: Optional[float] = Query(None, ge=0, description="Filtrar produtos com preço mínimo"),
    max_price: Optional[float] = Query(None, ge=0, description="Filtrar produtos com preço máximo"),
    available: Optional[bool] = Query(None, description="Filtrar produtos por disponibilidade de estoque"),
    skip: int = Query(0, ge=0, description="Número de produtos a pular (offset)"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de produtos por página"),
    current_user: dict = Depends(admin_required)
):
    query = db.query(DBProduct)

    if description:
        query = query.filter(DBProduct.description.ilike(f"%{description}%"))
    if category: # Se você tiver um campo 'category' no seu modelo DBProduct
        query = query.filter(DBProduct.section == category) # Ajuste para o nome correto do campo
    if min_price is not None:
        query = query.filter(DBProduct.sale_value >= min_price)
    if max_price is not None:
        query = query.filter(DBProduct.sale_value <= max_price)
    if available is not None:
        if available:
            query = query.filter(DBProduct.current_stock > 0)
        else:
            query = query.filter(DBProduct.current_stock <= 0) # Ou == 0, dependendo da sua regra

    products_from_db = query.offset(skip).limit(limit).all()
    return products_from_db

@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED, summary="Criar um novo produto")
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    # Validação de código de barras único (se for o caso)
    db_product_by_barcode = db.query(DBProduct).filter(DBProduct.barcode == product.barcode).first()
    if db_product_by_barcode:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Produto com este código de barras já existe."
        )

    # Cria uma instância do modelo SQLAlchemy
    # current_stock pode ser inicializado com initial_stock na criação
    db_product = DBProduct(
        description=product.description,
        sale_value=product.sale_value,
        barcode=product.barcode,
        section=product.section,
        initial_stock=product.initial_stock,
        current_stock=product.initial_stock, # Inicializa estoque atual
        expiration_date=product.expiration_date
        # Para imagens, se for uma lista de URLs, pode ser um JSONB no DB ou outra tabela
    )

    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return db_product

@router.get("/{product_id}", response_model=Product, summary="Obter informações de um produto específico")
def get_product_by_id(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    product = db.query(DBProduct).filter(DBProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    return product

@router.put("/{product_id}", response_model=Product, summary="Atualizar informações de um produto específico")
def update_product(
    product_id: int,
    updated_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    product = db.query(DBProduct).filter(DBProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")

    # Atualiza os campos do produto existente
    for key, value in updated_data.model_dump(exclude_unset=True).items():
        if key == "barcode" and value:
            existing_barcode_product = db.query(DBProduct).filter(DBProduct.barcode == value, DBProduct.id != product_id).first()
            if existing_barcode_product:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código de barras já cadastrado por outro produto")
        setattr(product, key, value)

    db.add(product) # Opcional, SQLAlchemy rastreia mudanças no objeto
    db.commit()
    db.refresh(product)

    return product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir um produto")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    product = db.query(DBProduct).filter(DBProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")

    db.delete(product)
    db.commit()
    # Opcional: return Response(status_code=status.HTTP_204_NO_CONTENT) para um corpo vazio no 204
    return {"message": f"Produto {product_id} deletado."}