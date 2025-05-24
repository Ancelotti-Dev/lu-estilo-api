# app/services/user_service.py

from sqlalchemy.orm import Session
from typing import Optional
from app.models import User as DBUser
from app.schemas import UserCreate # Pode importar AdminCreate também se quiser uma função específica para admin
from app.auth import get_password_hash # Importe de onde sua função de hash de senha está

def create_user_in_db(db: Session, user: UserCreate) -> DBUser:
    """
    Cria um novo usuário no banco de dados.
    Esta função é agnóstica a ser admin ou não; o is_admin vem do user:UserCreate.
    """
    hashed_password = get_password_hash(user.password)
    db_user = DBUser(
        email=user.email,
        hashed_password=hashed_password,
        is_active=user.is_active if hasattr(user, 'is_active') else True, # Adicionado is_active
        is_admin=user.is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Você pode adicionar outras funções CRUD aqui, como get_user_by_email, update_user, delete_user
def get_user_by_email(db: Session, email: str) -> Optional[DBUser]:
    return db.query(DBUser).filter(DBUser.email == email).first()

def get_user_by_email(db: Session, email: str) -> Optional[DBUser]:
    """
    Retorna um usuário pelo seu email.
    """
    return db.query(DBUser).filter(DBUser.email == email).first()