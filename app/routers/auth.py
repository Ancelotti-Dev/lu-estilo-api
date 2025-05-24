from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User as DBUser
from app.schemas import UserCreate, UserLogin, Token, RefreshTokenInput # Importa os schemas Pydantic
from app.auth import get_password_hash, verify_password, criar_token, ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from jose import jwt, JWTError
from datetime import timedelta
from app.users import get_current_user, admin_required
from app.crud import create_user_in_db, get_user_by_email

# Cria uma instância do APIRouter para agrupar as rotas de autenticação
router = APIRouter(tags=["Autenticação"])

@router.post("/register", response_model=Token, summary="Registra um novo usuário")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registra um novo usuário na aplicação.
    - **email**: O endereço de e-mail do usuário.
    - **password**: A senha do usuário.
    - **is_admin**: (Opcional) Define se o usuário é um administrador. Padrão é False.
    Retorna um token de acesso para o usuário recém-registrado.
    """
    # Verifica se já existe um usuário com o e-mail fornecido
    db_user = db.query(DBUser).filter(DBUser.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado."
        )

    # Gera o hash da senha para armazenamento seguro
    hashed_password = get_password_hash(user_data.password)

    # Cria uma nova instância do modelo de usuário do SQLAlchemy
    new_user = create_user_in_db(db, user_data)
    
    # Adiciona o novo usuário à sessão do banco de dados, salva e atualiza o objeto
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Cria um token de acesso para o novo usuário
    access_token = criar_token(data={"sub": new_user.email, "is_admin": new_user.is_admin})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token, summary="Autentica um usuário existente")
def login_for_access_token(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Autentica um usuário e retorna um token de acesso JWT.
    - **email**: O e-mail do usuário.
    - **password**: A senha do usuário.
    """
    # Busca o usuário no banco de dados pelo e-mail
    user = db.query(DBUser).filter(DBUser.email == user_data.email).first()
    
    # Verifica se o usuário existe e se a senha está correta
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"}, # Indica que a autenticação Bearer é esperada
        )
    
    # Cria um token de acesso para o usuário autenticado
    access_token = criar_token(data={"sub": user.email, "is_admin": user.is_admin})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh-token", response_model=Token, summary="Renovar um token de acesso expirado")
async def refresh_token(token_input: RefreshTokenInput):
    """
    Renova um token de acesso JWT.
    - **token**: O token JWT a ser renovado.
    """
    try:
        # Decodifica o token JWT para extrair o payload
        payload = jwt.decode(token_input.token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub") # Obtém o e-mail do payload
        is_admin: bool = payload.get("is_admin") # Obtém o status de admin do payload (importante para manter privilégios)
        
        # Verifica se o e-mail está presente no payload do token
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido: email ausente no payload")

        # Calcula o tempo de expiração para o novo token
        new_access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Cria um novo token de acesso com o mesmo e-mail e status de admin, mas com nova validade
        new_access_token = criar_token(data={"sub": email, "is_admin": is_admin}, expires_delta=new_access_token_expires)
        
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        # Captura erros de JWT (token inválido, assinatura errada, expirado)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de refresh inválido ou expirado")
