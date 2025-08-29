#!/usr/bin/env python3
"""
Rotas para o sistema de contexto conversacional
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json

from ..core.database import get_db
from ..models.conversation_session import ConversationSession, ConversationTurn, UserMemory, ConversationAuditLog
from ..schemas.conversation import (
    SessionCreate, SessionUpdate, SessionResponse,
    TurnCreate, TurnResponse,
    MemoryCreate, MemoryResponse,
    AuditCreate, AuditResponse
)

router = APIRouter(prefix="/conversations", tags=["conversations"])

# ========= SESSÕES =========

@router.get("/sessions", response_model=List[SessionResponse])
def get_sessions(
    whatsapp_number: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Lista sessões de conversa com filtros opcionais"""
    query = db.query(ConversationSession)
    
    if whatsapp_number:
        query = query.filter(ConversationSession.whatsapp_number == whatsapp_number)
    
    if active is not None:
        query = query.filter(ConversationSession.is_active == active)
    
    sessions = query.all()
    return [SessionResponse.model_validate(session) for session in sessions]

@router.post("/sessions", response_model=SessionResponse, status_code=201)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    """Cria uma nova sessão de conversa"""
    db_session = ConversationSession(**session.model_dump())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return SessionResponse.model_validate(db_session)

@router.get("/sessions/{session_key}", response_model=SessionResponse)
def get_session(session_key: str, db: Session = Depends(get_db)):
    """Obtém uma sessão específica"""
    session = db.query(ConversationSession).filter(
        ConversationSession.session_key == session_key
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse.model_validate(session)

@router.put("/sessions/{session_key}", response_model=SessionResponse)
def update_session(session_key: str, session_update: SessionUpdate, db: Session = Depends(get_db)):
    """Atualiza uma sessão existente"""
    db_session = db.query(ConversationSession).filter(
        ConversationSession.session_key == session_key
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    for field, value in session_update.model_dump(exclude_unset=True).items():
        setattr(db_session, field, value)
    
    db.commit()
    db.refresh(db_session)
    return SessionResponse.model_validate(db_session)

@router.get("/sessions/{session_key}/context")
def get_session_context(session_key: str, db: Session = Depends(get_db)):
    """Obtém o contexto completo de uma sessão"""
    session = db.query(ConversationSession).filter(
        ConversationSession.session_key == session_key
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Buscar turnos recentes
    turns = db.query(ConversationTurn).filter(
        ConversationTurn.session_key == session_key
    ).order_by(ConversationTurn.turn_number.desc()).limit(6).all()
    
    # Buscar memórias do usuário
    memories = db.query(UserMemory).filter(
        UserMemory.whatsapp_number == session.whatsapp_number
    ).all()
    
    return {
        "session": SessionResponse.model_validate(session),
        "recent_turns": [TurnResponse.model_validate(turn) for turn in turns],
        "user_memories": [MemoryResponse.model_validate(memory) for memory in memories],
        "rolling_summary": session.rolling_summary
    }

# ========= TURNOS =========

@router.post("/turns", response_model=TurnResponse, status_code=201)
def create_turn(turn: TurnCreate, db: Session = Depends(get_db)):
    """Cria um novo turno de conversa"""
    db_turn = ConversationTurn(**turn.model_dump())
    db.add(db_turn)
    db.commit()
    db.refresh(db_turn)
    return TurnResponse.model_validate(db_turn)

@router.get("/turns", response_model=List[TurnResponse])
def get_turns(
    session_key: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """Lista turnos de conversa"""
    query = db.query(ConversationTurn)
    
    if session_key:
        query = query.filter(ConversationTurn.session_key == session_key)
    
    turns = query.order_by(ConversationTurn.turn_number.desc()).limit(limit).all()
    return [TurnResponse.model_validate(turn) for turn in turns]

# ========= MEMÓRIAS =========

@router.post("/memories", response_model=MemoryResponse, status_code=201)
def create_memory(memory: MemoryCreate, db: Session = Depends(get_db)):
    """Cria uma nova memória do usuário"""
    db_memory = UserMemory(**memory.model_dump())
    db.add(db_memory)
    db.commit()
    db.refresh(db_memory)
    return MemoryResponse.model_validate(db_memory)

@router.get("/memories", response_model=List[MemoryResponse])
def get_memories(
    whatsapp_number: str = Query(...),
    db: Session = Depends(get_db)
):
    """Lista memórias de um usuário"""
    memories = db.query(UserMemory).filter(
        UserMemory.whatsapp_number == whatsapp_number
    ).all()
    
    return [MemoryResponse.model_validate(memory) for memory in memories]

# ========= AUDITORIA =========

@router.post("/audit", response_model=AuditResponse, status_code=201)
def create_audit(audit: AuditCreate, db: Session = Depends(get_db)):
    """Cria um novo log de auditoria"""
    db_audit = ConversationAuditLog(**audit.model_dump())
    db.add(db_audit)
    db.commit()
    db.refresh(db_audit)
    return AuditResponse.model_validate(db_audit)

@router.get("/audit", response_model=List[AuditResponse])
def get_audit_logs(
    session_key: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """Lista logs de auditoria"""
    query = db.query(ConversationAuditLog)
    
    if session_key:
        query = query.filter(ConversationAuditLog.session_key == session_key)
    
    logs = query.order_by(ConversationAuditLog.created_at.desc()).limit(limit).all()
    return [AuditResponse.model_validate(log) for log in logs] 