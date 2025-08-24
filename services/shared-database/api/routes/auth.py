from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..schemas.auth import LoginRequest, LoginResponse
from ..crud.user import UserCRUD

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Autentica um usuário e retorna token JWT"""
    # TODO: Implementar autenticação real com JWT
    # Por enquanto, apenas simula o login
    
    # Verificar se usuário existe
    user = UserCRUD.get_user_by_number(db, login_data.username)
    if not user:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Credenciais inválidas",
                "code": "INVALID_CREDENTIALS"
            }
        )
    
    # TODO: Verificar senha hash
    # Por enquanto, aceita qualquer senha
    
    # TODO: Gerar JWT real
    # Por enquanto, retorna token mock
    mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    return LoginResponse(
        access_token=mock_token,
        token_type="bearer",
        expires_in=3600,
        user=user
    ) 