# app/models.py

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Date, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # Importe func
from datetime import datetime # Mantenha para outros usos, mas não para defaults de Column

from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    # Ajuste aqui:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    clients = relationship("Client", back_populates="created_by_user")

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    cpf = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    address = Column(String, nullable=True)
    # Ajuste aqui:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_by_user = relationship("User", back_populates="clients")
    orders = relationship("Order", back_populates="client")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    sale_value = Column(Float, nullable=False)
    barcode = Column(String, unique=True, index=True, nullable=True)
    section = Column(String, nullable=False)
    initial_stock = Column(Integer, nullable=False)
    current_stock = Column(Integer, default=0, nullable=False)
    expiration_date = Column(Date, nullable=True)
    main_image_url = Column(String, nullable=True)

    # Ajuste aqui:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    order_products = relationship("OrderProduct", back_populates="product")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    order_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) # Ajuste aqui
    status = Column(String, default="pending", nullable=False)
    total_value = Column(Float, default=0.0, nullable=False)
    notes = Column(Text, nullable=True)

    # Ajuste aqui:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    client = relationship("Client", back_populates="orders")
    order_products = relationship("OrderProduct", back_populates="order")

class OrderProduct(Base):
    __tablename__ = "order_products"
    order_id = Column(Integer, ForeignKey("orders.id"), primary_key=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True, nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_order = Column(Float, nullable=False)

    # Ajuste aqui:
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # Adicione created_at
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now()) # Adicione updated_at

    order = relationship("Order", back_populates="order_products")
    product = relationship("Product", back_populates="order_products")

class WhatsAppLog(Base):
    __tablename__ = "whatsapp_logs"
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, nullable=False)
    # Ajuste aqui:
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    response_data = Column(Text, nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    order = relationship("Order")
    # Ajuste aqui:
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # Adicione created_at
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now()) # Adicione updated_at