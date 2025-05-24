# tests/test_clients.py
import pytest
from starlette.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Client # Importe o modelo Client para manipulação do DB

# Os 'clean_clients_db' e 'db_session' já são injetados automaticamente pelo pytest
# se estiverem no conftest.py e tiverem o escopo apropriado.

# ====================================================================
# TESTES DE CLIENTES (AGORA USANDO auth_admin_client DA FIXTURE)
# ====================================================================

def test_create_client(auth_admin_client: TestClient, db_session: Session, clean_clients_db):
    response = auth_admin_client.post(
        "/clients/",
        json={"nome": "Test Client", "email": "test@example.com", "cpf": "12345678901"}
    )
    assert response.status_code == 201  # Corrigido para 201
    assert response.json()["nome"] == "Test Client"
    assert "id" in response.json() # Verifique se um ID foi gerado

    # Verifique no banco de dados
    created_client = db_session.query(Client).filter(Client.email == "test@example.com").first()
    assert created_client is not None
    assert created_client.nome == "Test Client"


def test_get_client_by_id(auth_admin_client: TestClient, db_session: Session, clean_clients_db):
    # Crie o cliente diretamente no DB para garantir um ID conhecido
    new_client = Client(nome="Test Client", email="test@example.com", cpf="12345678901", created_by_user_id=1) # Assumindo um created_by_user_id válido, ou ajuste o seu modelo/lógica
    db_session.add(new_client)
    db_session.commit()
    db_session.refresh(new_client) # Para obter o ID gerado

    response = auth_admin_client.get(f"/clients/{new_client.id}")
    assert response.status_code == 200
    assert response.json()["nome"] == "Test Client"
    assert response.json()["id"] == new_client.id

def test_get_non_existent_client(auth_admin_client: TestClient, clean_clients_db):
    response = auth_admin_client.get("/clients/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Cliente não encontrado"} # Verifique a mensagem exata de erro do seu FastAPI

def test_list_clients_empty(auth_admin_client: TestClient, clean_clients_db):
    response = auth_admin_client.get("/clients/")
    assert response.status_code == 200
    assert response.json() == []

def test_list_clients_basic_pagination(auth_admin_client: TestClient, db_session: Session, clean_clients_db):
    clients_to_add = []
    for i in range(1, 15):
        clients_to_add.append(Client(nome=f"Client {i}", email=f"client{i}@example.com", cpf=f"{10000000000 + i}", created_by_user_id=1))
    db_session.add_all(clients_to_add)
    db_session.commit()

    response = auth_admin_client.get("/clients/?limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 5
    assert response.json()[0]["nome"] == "Client 1"
    assert response.json()[4]["nome"] == "Client 5"

    response = auth_admin_client.get("/clients/?skip=5&limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 5
    assert response.json()[0]["nome"] == "Client 6"
    assert response.json()[4]["nome"] == "Client 10"

    response = auth_admin_client.get("/clients/?skip=20&limit=5")
    assert response.status_code == 200
    assert response.json() == []

    response = auth_admin_client.get("/clients/?limit=100")
    assert response.status_code == 200
    assert len(response.json()) == 14 # Total de clientes

def test_list_clients_filter_by_name(auth_admin_client: TestClient, db_session: Session, clean_clients_db):
    clients_to_add = [
        Client(nome="Alice", email="alice@example.com", cpf="11111111111", created_by_user_id=1),
        Client(nome="Bob", email="bob@example.com", cpf="22222222222", created_by_user_id=1),
        Client(nome="Charlie", email="charlie@example.com", cpf="33333333333", created_by_user_id=1),
        Client(nome="ALEX", email="alex@example.com", cpf="44444444444", created_by_user_id=1)
    ]
    db_session.add_all(clients_to_add)
    db_session.commit()

    response = auth_admin_client.get("/clients/?nome=lice")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["nome"] == "Alice"

    response = auth_admin_client.get("/clients/?nome=AL")
    assert response.status_code == 200
    assert len(response.json()) == 2
    actual_names = {c["nome"] for c in response.json()}
    assert actual_names == {"Alice", "ALEX"} # A ordem pode variar

def test_list_clients_filter_by_email(auth_admin_client: TestClient, db_session: Session, clean_clients_db):
    clients_to_add = [
        Client(nome="Alice", email="alice@example.com", cpf="11111111111", created_by_user_id=1),
        Client(nome="Bob", email="bob@test.com", cpf="22222222222", created_by_user_id=1),
        Client(nome="Charlie", email="charlie@example.com", cpf="33333333333", created_by_user_id=1)
    ]
    db_session.add_all(clients_to_add)
    db_session.commit()

    response = auth_admin_client.get("/clients/?email=alice@example.com")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["email"] == "alice@example.com"

def test_list_clients_filter_combined_and_pagination(auth_admin_client: TestClient, db_session: Session, clean_clients_db):
    clients_to_add = [
        Client(nome="Alice", email="alice@example.com", cpf="11111111111", created_by_user_id=1),
        Client(nome="Bob", email="bob@test.com", cpf="22222222222", created_by_user_id=1),
        Client(nome="Charlie", email="charlie@example.com", cpf="33333333333", created_by_user_id=1),
        Client(nome="David", email="david@test.com", cpf="44444444444", created_by_user_id=1),
        Client(nome="Eva", email="eva@example.com", cpf="55555555555", created_by_user_id=1)
    ]
    db_session.add_all(clients_to_add)
    db_session.commit()

    # O filtro combinado deve ser "nome contendo 'a' E email contendo 'alice@example.com'"
    # e depois pular 1 e limitar a 1.
    # No seu caso, Alice seria a única a atender o nome 'a' e email 'alice@example.com'.
    # Se você pular 1, não haverá resultados.
    response = auth_admin_client.get("/clients/?nome=a&email=alice@example.com&skip=0&limit=1") # Ajustado para skip=0 para encontrar Alice
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["nome"] == "Alice"

    response = auth_admin_client.get("/clients/?nome=a&email=alice@example.com&skip=1&limit=1") # Agora sim, skip=1 deve resultar em []
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_list_clients_invalid_pagination_parameters(auth_admin_client: TestClient, clean_clients_db):
    response = auth_admin_client.get("/clients/?limit=0")
    assert response.status_code == 422
    assert "detail" in response.json()
    assert "greater than or equal to 1" in response.json()["detail"][0]["msg"]  # Corrigido

    response = auth_admin_client.get("/clients/?skip=-1")
    assert response.status_code == 422
    assert "detail" in response.json()
    assert "greater than or equal to 0" in response.json()["detail"][0]["msg"]  # Corrigido

    response = auth_admin_client.get("/clients/?limit=101")
    assert response.status_code == 422
    assert "detail" in response.json()
    assert "less than or equal to 100" in response.json()["detail"][0]["msg"]  # Corrigido


def test_update_client(auth_admin_client: TestClient, db_session: Session, clean_clients_db):
    # Crie o cliente primeiro
    new_client = Client(nome="Original Name", email="original@example.com", cpf="11111111111", created_by_user_id=1)
    db_session.add(new_client)
    db_session.commit()
    db_session.refresh(new_client)

    updated_data = {"nome": "Updated Name", "email": "updated@example.com", "cpf": "99999999999"}
    response = auth_admin_client.put(
        f"/clients/{new_client.id}",
        json=updated_data
    )
    assert response.status_code == 200
    assert response.json()["nome"] == "Updated Name"
    assert response.json()["email"] == "updated@example.com"

    get_response = auth_admin_client.get(f"/clients/{new_client.id}")
    assert get_response.status_code == 200
    assert get_response.json()["nome"] == "Updated Name"

def test_update_non_existent_client(auth_admin_client: TestClient, clean_clients_db):
    response = auth_admin_client.put(
        "/clients/999",
        json={"nome": "Non Existent", "email": "no@example.com", "cpf": "99999999999"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Cliente não encontrado"} # Verifique a mensagem exata do seu FastAPI

def test_delete_client(auth_admin_client: TestClient, db_session: Session, clean_clients_db):
    new_client = Client(nome="Client to Delete", email="delete@example.com", cpf="12345678901", created_by_user_id=1)
    db_session.add(new_client)
    db_session.commit()
    db_session.refresh(new_client)

    response = auth_admin_client.delete(f"/clients/{new_client.id}")
    assert response.status_code == 204  # Corrigido para 204
   

    get_response = auth_admin_client.get(f"/clients/{new_client.id}")
    assert get_response.status_code == 404

def test_delete_non_existent_client(auth_admin_client: TestClient, clean_clients_db):
    response = auth_admin_client.delete("/clients/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Cliente não encontrado"}  # Corrigido para português