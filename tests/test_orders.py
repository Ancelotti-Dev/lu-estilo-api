import pytest
from starlette.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Client, Product




# IMPORTANTE:
# Estes testes interagem com o dicionário 'pedidos' em memória no app/main.py.
# Este dicionário é reinicializado a cada vez que o servidor da aplicação é carregado (ou seja, por cada teste),
# então os testes não terão persistência entre si por padrão, o que é bom para isolamento.
# Se você implementar persistência em banco de dados para Pedidos,
# precisará ajustar os testes para usar a sessão de banco de dados (assim como fez para usuários).


# Teste para criar um novo pedido (POST /orders)
def test_create_order(auth_admin_client: TestClient, db_session: Session, clean_orders_db, clean_clients_db, clean_products_db):
    # Crie um cliente e um produto no banco antes
    client = Client(nome="Cliente Pedido", email="pedido@example.com", cpf="12345678900", created_by_user_id=1)
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    product = Product(description="Produto Teste", sale_value=10.0, barcode="123", section="A", initial_stock=10, current_stock=10)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    order_data = {
        "client_id": client.id,
        "products": [
            {"product_id": product.id, "quantity": 2}
        ],
        "notes": "Pedido de teste"
    }

    response = auth_admin_client.post("/orders/", json=order_data)
    assert response.status_code == 201
    assert response.json()["client_id"] == client.id
    assert response.json()["order_products"][0]["product_id"] == product.id
    assert response.json()["order_products"][0]["quantity"] == 2

# Teste para obter um pedido por ID (GET /orders/{id})
def test_get_order_by_id(auth_admin_client: TestClient, db_session: Session, clean_orders_db, clean_clients_db, clean_products_db):
    # Crie cliente, produto e pedido como acima
    client = Client(nome="Cliente Pedido", email="pedido2@example.com", cpf="12345678901", created_by_user_id=1)
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)

    product = Product(description="Produto Teste 2", sale_value=20.0, barcode="124", section="B", initial_stock=5, current_stock=5)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    order_data = {
        "client_id": client.id,
        "products": [
            {"product_id": product.id, "quantity": 1}
        ],
        "notes": "Pedido para teste get"
    }
    create_response = auth_admin_client.post("/orders/", json=order_data)
    assert create_response.status_code == 201
    order_id = create_response.json()["id"]

    # Agora, tente obter o pedido
    response = auth_admin_client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["id"] == order_id

# Teste para obter um pedido que não existe (GET /orders/{id} 404)
def test_get_non_existent_order(auth_admin_client: TestClient):
    non_existent_id = 999
    response = auth_admin_client.get(f"/orders/{non_existent_id}")
    assert response.status_code == 404
    # Ajuste a asserção conforme a mensagem real da sua API:
    assert response.json()["detail"] == "Pedido não encontrado ou você não tem permissão para acessá-lo."

# Teste para atualizar o status de um pedido (PUT /orders/{id})
def test_update_order_status(auth_admin_client: TestClient, db_session: Session, clean_orders_db, clean_clients_db, clean_products_db):
    # Crie cliente, produto e pedido como nos outros testes
    client = Client(nome="Cliente Pedido", email="pedido3@example.com", cpf="12345678902", created_by_user_id=1)
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)

    product = Product(description="Produto Teste 3", sale_value=30.0, barcode="125", section="C", initial_stock=5, current_stock=5)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    order_data = {
        "client_id": client.id,
        "products": [
            {"product_id": product.id, "quantity": 1}
        ],
        "notes": "Pedido para teste update status"
    }
    create_response = auth_admin_client.post("/orders/", json=order_data)
    assert create_response.status_code == 201
    order_id = create_response.json()["id"]

    # Atualize o status
    response = auth_admin_client.put(f"/orders/{order_id}/status", json={"status": "processing"})
    assert response.status_code == 200
    assert response.json()["status"] == "processing"

    # Verifique se o status foi realmente alterado ao obter o pedido novamente
    get_response = auth_admin_client.get(f"/orders/{order_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "processing"

# Teste para deletar um pedido (DELETE /orders/{id})
def test_delete_non_existent_order(auth_admin_client: TestClient):
    non_existent_id = 999
    response = auth_admin_client.delete(f"/orders/{non_existent_id}")
    assert response.status_code == 404
    # Ajuste a mensagem conforme seu backend, por exemplo:
    # assert response.json()["detail"] == "Pedido não encontrado."

# Teste para listar pedidos (GET /orders) - Este endpoint é mais complexo devido aos filtros
def test_list_orders(auth_admin_client: TestClient):
    response = auth_admin_client.get("/orders")

    assert response.status_code == 200

    # Verifique se a resposta é uma lista (dependendo de como você implementou o endpoint)
    assert isinstance(response.json(), list)

    #Verifique se a lista contém dicionários com as chaves esperadas
    for order in response.json():
        assert "id" in order
        assert "produtos" in order
        assert "status" in order

# Teste para criar um novo produto (POST /products)
def test_create_product(auth_admin_client: TestClient):
    product_data = {
        "description": "Um laptop para testes.",
        "sale_value": 1500.00,
        "barcode": "0987654321",
        "section": "Eletronicos",
        "initial_stock": 50,
        "expiration_date": None,
        "main_image_url": None
    }

    response = auth_admin_client.post("/products/", json=product_data)
    assert response.status_code == 201
    assert response.json()["description"] == product_data["description"]
    assert response.json()["sale_value"] == product_data["sale_value"]

# Teste para obter um produto por ID (GET /products/{id})
def test_get_product_by_id(auth_admin_client: TestClient):
    product_data = {
        "description": "Um laptop para testes.",
        "sale_value": 1500.00,
        "barcode": "0987654321",
        "section": "Eletronicos",
        "initial_stock": 50,
        "expiration_date": None,
        "main_image_url": None
    }
    create_response = auth_admin_client.post("/products/", json=product_data)
    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    response = auth_admin_client.get(f"/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["id"] == product_id
    assert response.json()["description"] == product_data["description"]

# Teste para listar produtos (GET /products)
def test_list_products(auth_admin_client: TestClient):
    # Crie alguns produtos para a listagem
    for i in range(3):
        product_data = {
            "description": f"Produto {i}",
            "sale_value": 10.0 + i,
            "barcode": f"barcode{i}",
            "section": "secA",
            "initial_stock": 10 + i,
            "expiration_date": None,
            "main_image_url": None
        }
        auth_admin_client.post("/products/", json=product_data)

    response = auth_admin_client.get("/products/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 3