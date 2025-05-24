# app/schemas.py

from pydantic import BaseModel, EmailStr, Field
from pydantic import ConfigDict
from typing import Optional, List
from datetime import date, datetime # Importar date e datetime juntos

# --- Schemas de Autenticação ---
class UserCreate(BaseModel): 
    email: EmailStr = Field(..., description="E-mail do usuário")
    password: str = Field(..., description="Senha do usuário")
    is_admin: bool = Field(False, description="Se o usuário é administrador")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "admin@luestilo.com",
                    "password": "SenhaForte123",
                    "is_admin": True
                }
            ]
        }
    )

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="E-mail do usuário")
    password: str = Field(..., description="Senha do usuário")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "admin@luestilo.com",
                    "password": "SenhaForte123"
                }
            ]
        }
    )

class AdminCreate(UserCreate):
    # Ao herdar, ele já terá email, password, is_active
    # Apenas sobrescrevemos o valor padrão de is_admin para True
    is_admin: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- Schemas de Refresh Token (se você precisar de um schema específico para a entrada do refresh)
class RefreshTokenInput(BaseModel):
    token: str # O token de refresh a ser enviado

# --- Schemas de Clientes ---
# app/schemas.py
# ...
class ClientBase(BaseModel):
    nome: str
    email: EmailStr
    cpf: str
    phone_number: Optional[str] = None 
    address: Optional[str] = None     
# ...

class ClientCreate(BaseModel):
    nome: str = Field(..., description="Nome completo do cliente")
    email: EmailStr = Field(..., description="E-mail do cliente")
    cpf: str = Field(..., description="CPF do cliente (somente números)")
    phone_number: Optional[str] = Field(None, description="Telefone do cliente")
    address: Optional[str] = Field(None, description="Endereço do cliente")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nome": "Maria da Silva",
                    "email": "maria@email.com",
                    "cpf": "12345678900",
                    "phone_number": "11999999999",
                    "address": "Rua das Flores, 123"
                }
            ]
        }
    )

class ClientUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    cpf: Optional[str] = None

class Client(ClientBase):
    id: int
    # Adicionar outros campos de retorno do DB, como datas de criação/atualização
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Schemas de Produtos ---
class ProductBase(BaseModel):
    description: str
    sale_value: float
    barcode: str
    section: str
    initial_stock: int
    expiration_date: Optional[date] = None
    main_image_url: Optional[str] = None

class ProductCreate(BaseModel):
    description: str = Field(..., description="Descrição do produto")
    sale_value: float = Field(..., description="Valor de venda")
    barcode: str = Field(..., description="Código de barras")
    section: str = Field(..., description="Seção ou categoria")
    initial_stock: int = Field(..., description="Estoque inicial")
    expiration_date: Optional[date] = Field(None, description="Data de validade (opcional)")
    main_image_url: Optional[str] = Field(None, description="URL da imagem principal (opcional)")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "description": "Camiseta Polo Masculina",
                    "sale_value": 99.90,
                    "barcode": "1234567890123",
                    "section": "Masculino",
                    "initial_stock": 100,
                    "expiration_date": "2025-12-31",
                    "main_image_url": "https://cdn.exemplo.com/produto.jpg"
                }
            ]
        }
    )

class ProductUpdate(BaseModel):
    description: Optional[str] = None
    sale_value: Optional[float] = None
    barcode: Optional[str] = None
    section: Optional[str] = None
    initial_stock: Optional[int] = None
    expiration_date: Optional[date] = None
    main_image_url: Optional[str] = None

class Product(ProductBase):
    id: int
    current_stock: int # Estoque atual
    # Adicionar outros campos de retorno do DB, como datas de criação/atualização
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
        

# --- Schemas de Pedidos ---
class OrderProductCreate(BaseModel):
    product_id: int = Field(..., description="ID do produto")
    quantity: int = Field(..., description="Quantidade do produto")

class OrderCreate(BaseModel):
    client_id: int = Field(..., description="ID do cliente")
    products: List[OrderProductCreate] = Field(..., description="Lista de produtos do pedido")
    notes: Optional[str] = Field(None, description="Observações do pedido")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "client_id": 1,
                    "products": [
                        {"product_id": 1, "quantity": 2},
                        {"product_id": 2, "quantity": 1}
                    ],
                    "notes": "Entregar após as 18h"
                }
            ]
        }
    )

class UpdateOrderStatus(BaseModel):
    status: str

class OrderProduct(BaseModel):
    product_id: int
    quantity: int
    price_at_order: float # Preço do produto no momento da compra
    # Se quiser detalhes do produto aninhados aqui no retorno do pedido:
    # product: Product # Isso exigiria um joinedload do product_id para o objeto Product

    model_config = ConfigDict(from_attributes=True)

class Order(BaseModel):
    id: int
    client_id: int
    order_date: datetime
    status: str
    total_value: float
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    order_products: List[OrderProduct] = [] # Lista de OrderProduct

    model_config = ConfigDict(from_attributes=True)

# --- Schemas de WhatsApp ---
class WhatsAppMessage(BaseModel):
    phone_number: str = Field(..., description="Número do cliente no WhatsApp (com DDD)")
    message: str = Field(..., description="Mensagem a ser enviada")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "phone_number": "5511999999999",
                    "message": "Seu pedido foi enviado!"
                }
            ]
        }
    )

class WhatsAppLog(BaseModel):
    id: int
    phone_number: str
    message: str
    status: str
    sent_at: datetime
    response_data: Optional[str] = None
    order_id: Optional[int] = None # FK para Order, se o log estiver associado a um pedido

    model_config = ConfigDict(from_attributes=True)
