from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..core.database import get_db
from ..schemas.user import UserCreate, UserUpdate, UserResponse, UserList
from ..schemas.whatsapp_config import WhatsAppConfigCreate, WhatsAppConfigUpdate, WhatsAppConfigResponse
from ..crud.user import UserCRUD
from ..crud.whatsapp_config import WhatsAppConfigCRUD

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

@router.get("/users", response_model=UserList)
async def list_users(
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
    active_only: bool = Query(True, description="Filtrar apenas usuários ativos"),
    search: Optional[str] = Query(None, description="Buscar por nome, número ou empresa"),
    db: Session = Depends(get_db)
):
    """Lista usuários do módulo WhatsApp"""
    users, total = UserCRUD.get_users(
        db=db,
        skip=skip,
        limit=limit,
        active_only=active_only,
        search=search
    )
    
    has_more = (skip + limit) < total
    
    return UserList(
        users=users,
        total=total,
        skip=skip,
        limit=limit,
        has_more=has_more
    )

@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Cria um novo usuário"""
    # Verificar se usuário já existe
    existing_user = UserCRUD.get_user_by_number(db, user_data.number)
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Usuário já existe",
                "code": "USER_ALREADY_EXISTS",
                "details": {"number": user_data.number}
            }
        )
    
    try:
        user = UserCRUD.create_user(db, user_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Erro ao criar usuário",
                "code": "USER_CREATION_ERROR",
                "details": {"error": str(e)}
            }
        )

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Obtém detalhes de um usuário específico"""
    user = UserCRUD.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Usuário não encontrado",
                "code": "USER_NOT_FOUND",
                "details": {"user_id": user_id}
            }
        )
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza dados de um usuário existente"""
    user = UserCRUD.update_user(db, user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Usuário não encontrado",
                "code": "USER_NOT_FOUND",
                "details": {"user_id": user_id}
            }
        )
    return user

@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Remove um usuário do sistema"""
    success = UserCRUD.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Usuário não encontrado",
                "code": "USER_NOT_FOUND",
                "details": {"user_id": user_id}
            }
        )
    return None

@router.post("/users/{user_id}/interact", response_model=UserResponse)
async def record_user_interaction(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Registra uma interação do usuário"""
    user = UserCRUD.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Usuário não encontrado",
                "code": "USER_NOT_FOUND",
                "details": {"user_id": user_id}
            }
        )
    
    UserCRUD.record_interaction(db, user.number)
    db.refresh(user)
    return user

# ========= Configuração do WhatsApp =========

@router.get("/config", response_model=WhatsAppConfigResponse)
async def get_whatsapp_config(db: Session = Depends(get_db)):
    """Obtém a configuração ativa do WhatsApp"""
    try:
        config = WhatsAppConfigCRUD.get_active_config(db)
        if not config:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Configuração do WhatsApp não encontrada",
                    "code": "WHATSAPP_CONFIG_NOT_FOUND"
                }
            )
        return config
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao obter configuração: {str(e)}"
        )

@router.put("/config", response_model=WhatsAppConfigResponse)
async def update_whatsapp_config(
    config: WhatsAppConfigUpdate, 
    db: Session = Depends(get_db)
):
    """Atualiza a configuração do WhatsApp"""
    try:
        # Se não existir configuração ativa, criar uma nova
        existing_config = WhatsAppConfigCRUD.get_active_config(db)
        if not existing_config:
            # Criar nova configuração
            config_data = WhatsAppConfigCreate(
                access_token=config.access_token or "",
                phone_number_id=config.phone_number_id or "",
                business_account_id=config.business_account_id or "",
                verify_token=config.verify_token or "",
                webhook_url=config.webhook_url
            )
            return WhatsAppConfigCRUD.create_config(db, config_data)
        else:
            # Atualizar configuração existente
            updated_config = WhatsAppConfigCRUD.update_config(db, config)
            if not updated_config:
                raise HTTPException(
                    status_code=500,
                    detail="Erro ao atualizar configuração"
                )
            return updated_config
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao atualizar configuração: {str(e)}"
        )

@router.post("/send")
async def send_whatsapp_message(
    message_data: dict,
    db: Session = Depends(get_db)
):
    """Envia uma mensagem via WhatsApp (endpoint de teste)"""
    try:
        # Verificar se há configuração ativa
        config = WhatsAppConfigCRUD.get_active_config(db)
        if not config:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "WhatsApp não configurado",
                    "code": "WHATSAPP_NOT_CONFIGURED"
                }
            )
        
        # Aqui você implementaria a lógica de envio real
        # Por enquanto, retornamos sucesso simulado
        return {
            "success": True,
            "message_id": f"test_{int(datetime.now().timestamp())}",
            "status": "sent",
            "to": message_data.get("to"),
            "message": message_data.get("message")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao enviar mensagem: {str(e)}"
        ) 