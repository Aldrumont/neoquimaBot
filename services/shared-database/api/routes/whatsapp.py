from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..core.database import get_db
from ..schemas.user import UserCreate, UserUpdate, UserResponse, UserList
from ..crud.user import UserCRUD

router = APIRouter(prefix="/api/v1/whatsapp", tags=["WhatsApp"])

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