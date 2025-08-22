from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.params import Query, Header
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel
import os, re, logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

# Importações do banco de dados
from database import get_db, create_tables, UserCRUD
from database.schemas import UserCreate, UserUpdate, UserResponse, UserList
from database.models import User

# ========= Config =========
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "changeme")      # usado no GET /webhook (handshake)
ADMIN_TOKEN  = os.getenv("ADMIN_TOKEN", "adminchangeme")  # header X-Admin-Token
# allowlist inicial via env, sep por vírgula
ALLOWLIST_ENV = os.getenv("ALLOWLIST", "").strip()

# Normaliza números para E.164 (simples)
E164 = re.compile(r"^\+?[1-9]\d{6,14}$")
def norm(num: str) -> str:
    n = num.strip().replace(" ", "").replace("-", "")
    if not n.startswith("+"): n = "+" + n
    return n

# ========= Estado (simples, memória) =========
allow = set()
if ALLOWLIST_ENV:
    for n in ALLOWLIST_ENV.split(","):
        n = n.strip()
        if n:
            allow.add(norm(n))

app = FastAPI(title="WhatsApp Gateway", version="0.1.0")
log = logging.getLogger("uvicorn.error")

# Criar tabelas na inicialização
@app.on_event("startup")
async def startup_event():
    create_tables()

# ========= Modelos =========
class AdminAdd(BaseModel):
    number: str

# ========= Health =========
@app.get("/health")
def health():
    return {"status": "ok", "allow_count": len(allow)}

# ========= Verificação do Webhook (GET) =========
@app.get("/webhook", response_class=PlainTextResponse)
def verify(
    hub_mode: str = Query("", alias="hub.mode"), 
    hub_verify_token: str = Query("", alias="hub.verify_token"), 
    hub_challenge: str = Query("", alias="hub.challenge")
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return PlainTextResponse(hub_challenge or "", status_code=200)
    return PlainTextResponse("forbidden", status_code=403)

# ========= Recebimento de mensagens (POST) =========
@app.post("/webhook")
async def webhook(req: Request, db: Session = Depends(get_db)):
    body = await req.json()
    # Extrair números de quem enviou (depende do payload do WhatsApp)
    # Ex.: body["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
    try:
        entries = body.get("entry", [])
        changes = entries[0]["changes"][0]["value"]
        wa_from = changes["messages"][0]["from"]
        sender = norm(wa_from)
    except Exception:
        # Mesmo com erro de parsing, retorne 200 para evitar re-entregas infinitas
        log.warning("payload inesperado: %s", body)
        return {"status": "ignored"}

    # Verificar se o usuário está ativo no banco de dados
    db_user = UserCRUD.get_user_by_number(db, sender)
    
    if not db_user:
        log.info("bloqueado %s (usuário não encontrado)", sender)
        return {"status": "blocked", "reason": "user_not_found"}
    
    if not db_user.active:
        log.info("bloqueado %s (usuário inativo)", sender)
        return {"status": "blocked", "reason": "user_inactive"}
    
    # Verificar se o usuário expirou
    if db_user.expires_at and db_user.expires_at < datetime.now(timezone.utc):
        log.info("bloqueado %s (usuário expirado em %s)", sender, db_user.expires_at.isoformat())
        return {"status": "blocked", "reason": "user_expired", "expired_at": db_user.expires_at.isoformat()}
    
    # Registrar interação
    UserCRUD.record_interaction(db, sender)
    
    # >>> AQUI entraria o repasse para o Chat Orchestrator <<<
    # Exemplo fake:
    log.info("autorizado %s -> encaminhar ao orchestrator", sender)
    # requests.post(ORCHESTRATOR_URL, json={...})
    return {"status": "accepted", "user_id": db_user.id}

# ========= Admin (API key simples) =========
def check_admin(token: str = None):
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")

@app.get("/admin/allowlist")
def list_allowlist():
    return {"allow": sorted(list(allow))}

@app.post("/admin/allowlist", status_code=201)
def add_allow(item: AdminAdd, x_admin_token: str = Header(None)):
    check_admin(x_admin_token)
    n = norm(item.number)
    if not E164.match(n):
        raise HTTPException(400, "invalid_number_format (use E.164: +5511999998888)")
    allow.add(n)
    return {"added": n, "count": len(allow)}

@app.delete("/admin/allowlist", status_code=204)
def del_allow(number: str, x_admin_token: str = Header(None)):
    check_admin(x_admin_token)
    n = norm(number)
    allow.discard(n)
    return PlainTextResponse("")

# ========= CRUD de Usuários =========

@app.post("/admin/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, x_admin_token: str = Header(None), db: Session = Depends(get_db)):
    check_admin(x_admin_token)
    
    # Verificar se o número já existe
    existing_user = UserCRUD.get_user_by_number(db, user.number)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this number already exists")
    
    # Normalizar número
    user.number = norm(user.number)
    
    # Validar formato E.164
    if not E164.match(user.number):
        raise HTTPException(status_code=400, detail="Invalid number format (use E.164: +5511999998888)")
    
    return UserCRUD.create_user(db, user)

@app.get("/admin/users", response_model=UserList)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None),
    active_only: bool = Query(True),
    expired_only: bool = Query(False),
    expiring_soon: bool = Query(False),
    days_ahead: int = Query(7, ge=1, le=90),
    x_admin_token: str = Header(None),
    db: Session = Depends(get_db)
):
    check_admin(x_admin_token)
    
    # Aplicar filtros específicos
    if expired_only:
        users = UserCRUD.get_expired_users(db)
        total = len(users)
    elif expiring_soon:
        users = UserCRUD.get_expiring_soon_users(db, days_ahead)
        total = len(users)
    else:
        users = UserCRUD.get_users(db, skip=skip, limit=limit, active_only=active_only, search=search)
        total = UserCRUD.get_active_users_count(db) if active_only else db.query(func.count(User.id)).scalar()
    
    return UserList(
        users=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )

@app.get("/admin/users/stats")
def get_user_stats(x_admin_token: str = Header(None), db: Session = Depends(get_db)):
    check_admin(x_admin_token)
    
    total_users = db.query(func.count(User.id)).scalar()
    active_users = UserCRUD.get_active_users_count(db)
    inactive_users = total_users - active_users
    
    # Estatísticas de expiração
    expired_users = UserCRUD.get_expired_users(db)
    expiring_soon_users = UserCRUD.get_expiring_soon_users(db, 7)  # próximos 7 dias
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "expiration_stats": {
            "expired_users": len(expired_users),
            "expiring_soon": len(expiring_soon_users),
            "expiring_in_7_days": len(expiring_soon_users)
        }
    }

@app.get("/admin/users/expired")
def get_expired_users(x_admin_token: str = Header(None), db: Session = Depends(get_db)):
    """Lista usuários que expiraram"""
    check_admin(x_admin_token)
    
    expired_users = UserCRUD.get_expired_users(db)
    return {
        "expired_users": [UserResponse.model_validate(user) for user in expired_users],
        "count": len(expired_users)
    }

@app.get("/admin/users/expiring-soon")
def get_expiring_soon_users(
    days: int = Query(7, ge=1, le=90, description="Dias para considerar 'expirando em breve'"),
    x_admin_token: str = Header(None), 
    db: Session = Depends(get_db)
):
    """Lista usuários que expiram em X dias"""
    check_admin(x_admin_token)
    
    expiring_users = UserCRUD.get_expiring_soon_users(db, days)
    return {
        "expiring_users": [UserResponse.model_validate(user) for user in expiring_users],
        "count": len(expiring_users),
        "days_ahead": days
    }

@app.post("/admin/users/deactivate-expired")
def deactivate_expired_users(x_admin_token: str = Header(None), db: Session = Depends(get_db)):
    """Desativa automaticamente todos os usuários expirados"""
    check_admin(x_admin_token)
    
    count = UserCRUD.deactivate_expired_users(db)
    return {
        "message": f"Deactivated {count} expired users",
        "deactivated_count": count
    }

@app.get("/admin/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, x_admin_token: str = Header(None), db: Session = Depends(get_db)):
    check_admin(x_admin_token)
    
    user = UserCRUD.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.model_validate(user)

@app.put("/admin/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    x_admin_token: str = Header(None), 
    db: Session = Depends(get_db)
):
    check_admin(x_admin_token)
    
    user = UserCRUD.update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.model_validate(user)

@app.delete("/admin/users/{user_id}", status_code=204)
def delete_user(user_id: int, x_admin_token: str = Header(None), db: Session = Depends(get_db)):
    check_admin(x_admin_token)
    
    success = UserCRUD.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return PlainTextResponse("")

@app.patch("/admin/users/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int, 
    reason: str = Query(..., description="Reason for deactivation"),
    x_admin_token: str = Header(None), 
    db: Session = Depends(get_db)
):
    check_admin(x_admin_token)
    
    user = UserCRUD.deactivate_user(db, user_id, reason)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.model_validate(user)
