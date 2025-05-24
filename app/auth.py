# app/auth.py

# --- Importações (Ferramentas de Criptografia e Tempo) ---
from jose import JWTError, jwt
from datetime import datetime, timedelta, UTC
from passlib.context import CryptContext
from typing import Optional
import os # Para acessar variáveis de ambiente

# --- Configurações de Segurança do JWT ---
# CRÍTICO: Carregue a SECRET_KEY de uma variável de ambiente em produção!
SECRET_KEY = os.getenv("SECRET_KEY", "!@#%nfon*A$#*@(#%H@$%@!DCLI!@314877¨4ghw91HSUDBd)") # <<< Melhoria para DEV/PROD
# A chave padrão ("sua_chave_secreta_padrao_dev_segura_aqui") deve ser algo complexo e aleatório mesmo em dev.
# Em produção, a variável de ambiente SECRET_KEY deve ser definida.

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Contexto para Hashing de Senhas ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Função para Hash de Senha ---
def get_password_hash(password: str) -> str:
    """
    Hashes a plain-text password using bcrypt.
    """
    return pwd_context.hash(password)

# --- Função para Verificar Senha ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)

# --- Função para Criar Token ---
def criar_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Creates a JSON Web Token (JWT) with the provided data and an expiration time.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Função para Verificar Token ---
def verificar_token(token: str):
    """
    Verifies and decodes a JWT. Returns the payload if valid, None otherwise.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None