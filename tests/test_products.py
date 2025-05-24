# tests/test_products.py

import pytest
from starlette.testclient import TestClient

# Adjust test_create_product to handle ID if your API assigns it
def test_create_product(auth_admin_client: TestClient):
    product_data = {
        "description": "Smartphone Teste",
        "sale_value": 999.99,
        "barcode": "1234567890",
        "section": "Eletronicos",
        "initial_stock": 50,
        "expiration_date": None,
        "main_image_url": None
    }
    response = auth_admin_client.post("/products/", json=product_data)
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["description"] == product_data["description"]
    assert response.json()["sale_value"] == product_data["sale_value"]

# Adjust other tests (get_product_by_id, update_product, delete_product) to use the correct product_id
# and add missing required fields for the initial POST requests.

# For example, for test_get_product_by_id:
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

# ... Apply similar changes to test_update_product, test_delete_product, test_get_non_existent_product, test_delete_non_existent_product

# Test para listar todos os produtos (GET /products)
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

def test_delete_non_existent_order(auth_admin_client: TestClient):
    non_existent_id = 999
    response = auth_admin_client.delete(f"/orders/{non_existent_id}")
    assert response.status_code == 404
    # Ajuste a mensagem conforme seu backend, por exemplo: