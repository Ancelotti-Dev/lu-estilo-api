# API Lu Estilo - Gestão Comercial

API RESTful para gerenciamento de clientes, produtos, pedidos e integração com WhatsApp, desenvolvida em FastAPI.

## Funcionalidades

- Autenticação JWT (admin e usuário)
- CRUD de clientes, produtos e pedidos
- Filtros e paginação em todas as listagens
- Validação de estoque em pedidos
- Integração com WhatsApp (envio de mensagens e logs)
- Documentação automática via Swagger

## Como rodar localmente

### Pré-requisitos

- Python 3.10+
- PostgreSQL
- Docker (opcional, recomendado)

### Instalação

```bash
git clone https://github.com/Ancelotti-Dev/lu-estilo-api.git
cd lu-estilo-api
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
```

### Configuração

Crie um arquivo `.env` com as variáveis de ambiente necessárias:

```
DATABASE_URL=postgresql://usuario:senha@localhost:5432/amr
SECRET_KEY=sua_chave_secreta
ZAPI_INSTANCE_ID=...
ZAPI_TOKEN=...
```

### Migrações

```bash
alembic upgrade head
```

### Rodando a API

```bash
uvicorn app.main:app --reload
```

Acesse a documentação em [http://localhost:8000/docs](http://localhost:8000/docs)

### Rodando os testes

```bash
pytest -v
```

### Docker

```bash
docker-compose up --build
```

## Exemplos de uso

### Autenticação

**POST /auth/login**

```json
{
  "email": "admin@luestilo.com",
  "password": "suasenha"
}
```

### Criar Produto

**POST /products**

```json
{
  "description": "Camiseta Polo Masculina",
  "sale_value": 99.90,
  "barcode": "1234567890123",
  "section": "Masculino",
  "initial_stock": 100
}
```

## Integração WhatsApp

Configure as variáveis `ZAPI_INSTANCE_ID` e `ZAPI_TOKEN` no `.env` para ativar o envio de mensagens automáticas para clientes.

## Contribuição

Pull requests são bem-vindos!

