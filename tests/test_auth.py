# tests/test_auth.py
import pytest
from starlette.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import User # Importa o modelo User para validação no DB

# As fixtures `client`, `db_session`, `clean_users_db` serão fornecidas pelo conftest.py

# Teste de registro de usuário (POST /auth/register)
def test_register_user(client: TestClient, db_session: Session, clean_users_db):
    user_data = {
        "email": "newuser@example.com",
        "password": "securepassword123"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

    # Verifique se o usuário foi realmente salvo no banco de dados
    db_user = db_session.query(User).filter(User.email == user_data["email"]).first()
    assert db_user is not None
    assert db_user.email == user_data["email"]

# Teste de registro de usuário com email já existente
def test_register_existing_user(client: TestClient, clean_users_db):
    # Primeiro, registre o usuário
    user_data = {
        "email": "duplicate@example.com",
        "password": "password"
    }
    client.post("/auth/register", json=user_data) # Primeira requisição

    # Tente registrar o mesmo usuário novamente
    response = client.post("/auth/register", json=user_data) # Segunda requisição
    assert response.status_code == 400
    assert response.json() == {"detail": "Email já registrado."} # Ajuste a mensagem de erro se for diferente no seu backend

# Teste de login de usuário (POST /auth/token)
def test_login_user(client: TestClient, db_session: Session, clean_users_db):
    user_data = {
        "email": "loginuser@example.com",
        "password": "loginpassword"
    }
    client.post("/auth/register", json=user_data)

    login_data = {
        "email": "loginuser@example.com",  # username, não email
        "password": "loginpassword"
    }
    response = client.post("/auth/login", json=login_data)  # form-data
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient, clean_users_db):
  
    login_data = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401
    assert response.json() == {"detail": "Credenciais inválidas"} #


def test_protected_route_no_token(client: TestClient):
    response = client.get("/clients") 
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"} 

def test_protected_route_invalid_token(client: TestClient):
    headers = {"Authorization": "Bearer invalid_token_xyz"}
    response = client.get("/clients", headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"} 