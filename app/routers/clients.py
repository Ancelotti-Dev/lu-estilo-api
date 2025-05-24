# app/routers/clients.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import EmailStr
from app.users import get_current_user, admin_required
# Importe seus modelos SQLAlchemy e Pydantic
from app.database import get_db
from app.models import Client as DBClient # Renomeie para evitar conflito com Pydantic Client
from app.schemas import ClientCreate, ClientUpdate, Client # Seu modelo Pydantic Client

# Assumindo que você tem essas

router = APIRouter(tags=["Clientes"])

# Remova o dicionário em memória: clients = {}

@router.get("/", response_model=List[Client], summary="Listar todos os clientes com paginação e filtro")
async def list_clients(
    db: Session = Depends(get_db),
    nome: Optional[str] = Query(None, description="Filtrar clientes por nome"),
    email: Optional[EmailStr] = Query(None, description="Filtrar clientes por e-mail"),
    skip: int = Query(0, ge=0, description="Número de clientes a pular (offset)"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de clientes por página"),
    current_user: dict = Depends(admin_required)
):
    query = db.query(DBClient)
    if nome:
        query = query.filter(DBClient.nome.ilike(f"%{nome}%"))  # Corrigido aqui!
    if email:
        query = query.filter(DBClient.email.ilike(f"%{email}%"))
    clients_from_db = query.offset(skip).limit(limit).all()
    return clients_from_db

@router.post("/", response_model=Client, status_code=status.HTTP_201_CREATED, summary="Criar um novo cliente")
def create_client(
    client: ClientCreate, # Usa o modelo Pydantic para criação
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required) # Protege a rota, requer admin
):
    # 1. Validação de Email único
    db_client_by_email = db.query(DBClient).filter(DBClient.email == client.email).first()
    if db_client_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado."
        )

    # 2. Validação de CPF único
    db_client_by_cpf = db.query(DBClient).filter(DBClient.cpf == client.cpf).first()
    if db_client_by_cpf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado."
        )

    # 3. Cria uma instância do modelo SQLAlchemy com os dados do Pydantic
    db_client = DBClient(**client.model_dump()) # Converte Pydantic para SQLAlchemy model

    db.add(db_client) # Adiciona ao sessão
    db.commit()      # Salva no banco de dados
    db.refresh(db_client) # Atualiza o objeto com o ID gerado pelo DB

    return db_client # Retorna o objeto SQLAlchemy, que será convertido para Pydantic pelo response_model

@router.get("/{client_id}", response_model=Client, summary="Obter informações de um cliente específico")
def get_client_by_id(
    client_id: int, # Renomeado para evitar conflito com o parâmetro 'id' do Pydantic
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    # Busca o cliente pelo ID
    client = db.query(DBClient).filter(DBClient.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    return client

@router.put("/{client_id}", response_model=Client, summary="Atualizar informações de um cliente específico")
def update_client(
    client_id: int,
    updated_data: ClientUpdate, # Usa o modelo Pydantic para atualização
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    client = db.query(DBClient).filter(DBClient.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")

    # Atualiza os campos do modelo SQLAlchemy com os dados do Pydantic
    # model_dump(exclude_unset=True) garante que apenas os campos fornecidos na requisição sejam atualizados
    for key, value in updated_data.model_dump(exclude_unset=True).items():
        # Antes de atribuir, você pode adicionar validações específicas para email/cpf se forem alterados
        if key == "email" and value:
            existing_email_client = db.query(DBClient).filter(DBClient.email == value, DBClient.id != client_id).first()
            if existing_email_client:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado por outro cliente")
        if key == "cpf" and value:
            existing_cpf_client = db.query(DBClient).filter(DBClient.cpf == value, DBClient.id != client_id).first()
            if existing_cpf_client:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CPF já cadastrado por outro cliente")
        setattr(client, key, value) # Atualiza o atributo do objeto SQLAlchemy

    db.add(client) # Opcional: sqlalchemy geralmente rastreia mudanças no objeto
    db.commit()
    db.refresh(client)

    return client

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir um cliente")
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    client = db.query(DBClient).filter(DBClient.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")

    db.delete(client) # Marca o objeto para exclusão
    db.commit()      # Executa a exclusão no banco de dados
    return {"message": f"Client {client_id} deleted."} # Para 204, o corpo da resposta geralmente é vazio