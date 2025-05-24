# app/main.py

# Importações Essenciais:
from fastapi import FastAPI, Depends, Query, HTTPException, Request # Componentes principais do FastAPI.
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import status
import sentry_sdk # Para monitoramento de erros.

# Importe APENAS os roteadores, não os modelos ou funções internas de auth/users diretamente aqui.
from app.routers import auth, products, clients, orders, whatsapp

# Inicialização do Sentry SDK:
sentry_sdk.init(dsn=None) # Altere 'None' pelo seu DSN real em produção.

# Instância da Aplicação FastAPI:
app = FastAPI(
        title="API de Gerenciamento de Clientes e Pedidos",
    description="API para gerenciar clientes, produtos e pedidos, com autenticação JWT.",
    version="1.0.0",
    docs_url="/docs") # URL para a documentação Swagger)   

# Manipulador de erros de validação de requisição (opcional, mas bom ter):
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


# A ordem geralmente não importa, mas faz sentido agrupar por funcionalidade.
app.include_router(auth.router, prefix="/auth")
app.include_router(clients.router, prefix="/clients")
app.include_router(products.router, prefix="/products")
app.include_router(orders.router, prefix="/orders")  
app.include_router(whatsapp.router, prefix="/whatsapp")# O prefixo e tags já são definidos dentro de app/routers/orders.py # O prefixo e tags já são definidos dentro de app/routers/whatsapp.py


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Manipulador de exceções para erros de validação de requisição (Pydantic).
    Retorna uma resposta JSON formatada para erros de validação.
    """
    # Você pode personalizar como os erros são apresentados
    errors = [{"loc": err["loc"], "msg": err["msg"], "type": err["type"]} for err in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )