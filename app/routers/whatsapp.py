# app/routers/whatsapp.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import requests
import sentry_sdk # Para log de erros
import json # Para converter response_data para string
from typing import Optional, List
# Importe seus modelos SQLAlchemy e Pydantic
from app.database import get_db
from app.models import WhatsAppLog as DBWhatsAppLog
from app.schemas import WhatsAppMessage, WhatsAppLog # Importe o schema para a mensagem e o log
from app.users import get_current_user, admin_required
# Importe suas dependências de autenticação (se necessário proteger este endpoint) # Normalmente, apenas admins ou sistemas internos acionam isso

router = APIRouter(tags=["Notificações WhatsApp"])

# Lembre-se: TOKEN E ID DA INSTÂNCIA DEVEM VIR DE VARIÁVEIS DE AMBIENTE EM PRODUÇÃO!
# Exemplo:
# from decouple import config # pip install python-decouple
# ZAPI_INSTANCE_ID = config("ZAPI_INSTANCE_ID")
# ZAPI_TOKEN = config("ZAPI_TOKEN")

# Por enquanto, vou usar o que você passou, mas COM ESTRESSE para que não use em produção assim.
ZAPI_INSTANCE_ID = "3E1948F9F42F101A7F1D6260F2C0F8BD" # <<< ATENÇÃO: NUNCA HARDCODE ISSO EM PRODUÇÃO!
ZAPI_TOKEN = "3A2716359C0548F1285A905E" # <<< ATENÇÃO: NUNCA HARDCODE ISSO EM PRODUÇÃO!
ZAPI_BASE_URL = "https://api.z-api.io"


@router.post("/send", response_model=WhatsAppLog, summary="Enviar uma mensagem de WhatsApp")
def send_whatsapp_message(
    message_data: WhatsAppMessage,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(admin_required) # Proteja se apenas admins puderem acionar
):
    """
    Envia uma mensagem de texto via Z-API e registra o evento em WhatsAppLog.
    """
    log_status = "failed"
    log_response_data = None
    
    try:
        url = f"{ZAPI_BASE_URL}/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}/send-text"
        payload = {
            "phone": message_data.phone_number,
            "message": message_data.message
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status() # Levanta um erro para status de resposta HTTP 4xx/5xx

        log_status = "sent"
        log_response_data = json.dumps(response.json()) # Armazena a resposta JSON como string

        # Cria o log no banco de dados
        db_log = DBWhatsAppLog(
            phone_number=message_data.phone_number,
            message=message_data.message,
            status=log_status,
            response_data=log_response_data
            # order_id=... # Se você for associar a um pedido específico, passe o ID aqui
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)

        return db_log # Retorna o objeto WhatsAppLog do DB

    except requests.RequestException as e:
        # Captura erros de requisição HTTP (conexão, timeout, status 4xx/5xx)
        sentry_sdk.capture_exception(e) # Envia para o Sentry
        
        log_status = "failed"
        log_response_data = str(e) # Converte o erro para string para log
        if hasattr(e, 'response') and e.response is not None:
            log_response_data += f" | Response: {e.response.text}"

        # Tenta registrar o erro no banco de dados
        try:
            db_log = DBWhatsAppLog(
                phone_number=message_data.phone_number,
                message=message_data.message,
                status=log_status,
                response_data=log_response_data
            )
            db.add(db_log)
            db.commit()
            db.refresh(db_log)
        except Exception as db_e:
            sentry_sdk.capture_exception(db_e) # Loga se falhar ao salvar no DB
            print(f"Erro ao salvar log de WhatsApp no DB: {db_e}") # Print para depuração imediata

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao enviar mensagem WhatsApp")


# Endpoint para listar logs de WhatsApp (protegido por admin)
@router.get("/logs", response_model=List[WhatsAppLog], summary="Listar logs de envio de WhatsApp")
def list_whatsapp_logs(
    db: Session = Depends(get_db),
    phone_number: Optional[str] = Query(None, description="Filtrar por número de telefone"),
    status_filter: Optional[str] = Query(None, description="Filtrar por status de envio (sent, failed)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(admin_required)
):
    query = db.query(DBWhatsAppLog)
    if phone_number:
        query = query.filter(DBWhatsAppLog.phone_number.contains(phone_number))
    if status_filter:
        query = query.filter(DBWhatsAppLog.status == status_filter)

    logs = query.offset(skip).limit(limit).all()
    return logs