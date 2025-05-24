# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Importe Base e get_db do seu app.database
from app.database import Base, get_db
# Seu aplicativo FastAPI
from app.main import app
# IMPORTANTE: Importe todos os seus modelos para que Base.metadata os encontre
from app import models
# Importe o get_password_hash de onde ele está (assumindo app.auth)
from app.auth import get_password_hash

# Use um banco de dados SQLite em memória para testes (mais rápido e isolado)
# Usar ":memory:" é o mais isolado para testes, pois cada teste tem seu próprio DB.
# Se você usar um arquivo .db, ele precisa ser limpo entre os testes.
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:" # Mude para ":memory:" para maior isolamento entre execuções

# Setup do engine de teste para o banco de dados
engine_test = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Fixture para configurar e limpar o banco de dados antes e depois da sessão de testes
@pytest.fixture(scope="session", autouse=True)
def setup_all_tables():
    """
    Cria todas as tabelas no início da sessão de testes e as descarta no final.
    Usando autouse=True para garantir que seja executado antes de qualquer teste.
    """
    # Garante que todos os modelos são carregados para que Base.metadata os conheça
    _ = models.User, models.Client, models.Product, models.Order, models.OrderProduct, models.WhatsAppLog
    print("\n--- Criando tabelas do banco de dados em memória ---")
    Base.metadata.create_all(bind=engine_test)
    yield
    print("--- Descartando tabelas do banco de dados em memória ---")
    Base.metadata.drop_all(bind=engine_test)

# Fixture que fornece uma sessão de banco de dados para cada teste
# Renomeado de 'test_db_session' para 'db_session' para corresponder aos testes
@pytest.fixture(scope="function", name="db_session")
def db_session_fixture():
    """
    Fornece uma sessão de banco de dados para cada teste,
    garantindo um estado limpo e transacional.
    """
    connection = engine_test.connect()
    transaction = connection.begin()
    db = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    try:
        yield db
    finally:
        db.close()
        transaction.rollback() # Desfaz as alterações do teste
        connection.close()

# Fixture para o TestClient FastAPI genérico
# Renomeado de 'client_fixture' para 'client' para corresponder aos testes
@pytest.fixture(scope="function", name="client")
def client_fixture(db_session: Session): # Use db_session aqui
    """
    Fixture para o TestClient FastAPI, sobrescrevendo a dependência do banco de dados.
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client_instance:
        yield test_client_instance
    app.dependency_overrides.clear() # Limpar overrides após o teste

# Fixtures para limpar tabelas específicas
@pytest.fixture(scope="function")
def clean_users_db(db_session: Session):
    """Limpa a tabela de usuários antes e depois de cada teste."""
    db_session.query(models.User).delete()
    db_session.commit()
    yield
    db_session.query(models.User).delete()
    db_session.commit()

@pytest.fixture(scope="function")
def clean_clients_db(db_session: Session):
    """Limpa a tabela de clientes antes e depois de cada teste."""
    db_session.query(models.Client).delete()
    db_session.commit()
    yield
    db_session.query(models.Client).delete()
    db_session.commit()

@pytest.fixture(scope="function")
def clean_products_db(db_session: Session):
    """Limpa a tabela de produtos antes e depois de cada teste."""
    db_session.query(models.Product).delete()
    db_session.commit()
    yield
    db_session.query(models.Product).delete()
    db_session.commit()

@pytest.fixture(scope="function")
def clean_orders_db(db_session: Session):
    """Limpa as tabelas de pedidos e produtos de pedidos antes e depois de cada teste."""
    # Limpa order_products primeiro devido à dependência de chave estrangeira
    db_session.query(models.OrderProduct).delete()
    db_session.query(models.Order).delete()
    db_session.commit()
    yield
    db_session.query(models.OrderProduct).delete()
    db_session.query(models.Order).delete()
    db_session.commit()


# Fixture para autenticação de administrador
@pytest.fixture(scope="function", name="admin_auth_headers")
def admin_auth_headers_fixture(client: TestClient, db_session: Session):
    admin_email = "admin_test@example.com"
    admin_password = "test_admin_password"

    db_session.query(models.User).delete()
    db_session.commit()

    from app.auth import get_password_hash
    hashed_password = get_password_hash(admin_password)
    admin_user = models.User(email=admin_email, hashed_password=hashed_password, is_admin=True, is_active=True)
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)

    login_data = {"email": admin_email, "password": admin_password}
    response = client.post("/auth/login", json=login_data)  # Use json, não data
    assert response.status_code == 200, f"Erro ao fazer login do admin: {response.json()}"
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

# Fixture que fornece um TestClient autenticado com headers de admin
@pytest.fixture(name="auth_admin_client")
def auth_admin_client_fixture(client: TestClient, admin_auth_headers):
    """
    Retorna um TestClient já autenticado como admin.
    """
    client.headers.update(admin_auth_headers)
    yield client
    client.headers.clear()  # Limpa para não afetar outros testes