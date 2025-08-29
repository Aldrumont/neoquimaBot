import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..models.conversation_config import ConversationConfig
from ..models.conversation_session import ConversationSession, ConversationTurn, UserMemory, ConversationAuditLog
from ..core.database import get_db


class ConversationManager:
    def __init__(self, db: Session):
        self.db = db
        self.config = self._get_active_config()
    
    def _get_active_config(self) -> ConversationConfig:
        """Busca configuração ativa de conversa"""
        return self.db.query(ConversationConfig).filter(ConversationConfig.is_active == True).first()
    
    def _generate_session_key(self, whatsapp_number: str, session_id: str) -> str:
        """Gera chave única da sessão"""
        return f"{whatsapp_number}:{session_id}"
    
    def _is_session_expired(self, session: ConversationSession) -> bool:
        """Verifica se a sessão expirou"""
        if not session.last_activity:
            return True
        
        ttl_minutes = self.config.session_ttl_minutes if self.config else 30
        expiry_time = session.last_activity + timedelta(minutes=ttl_minutes)
        return datetime.utcnow() > expiry_time
    
    def get_or_create_session(self, whatsapp_number: str, session_id: str = None) -> ConversationSession:
        """Obtém ou cria uma nova sessão"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session_key = self._generate_session_key(whatsapp_number, session_id)
        
        # Buscar sessão existente
        session = self.db.query(ConversationSession).filter(
            ConversationSession.session_key == session_key
        ).first()
        
        if session and not self._is_session_expired(session):
            # Atualizar atividade
            session.last_activity = datetime.utcnow()
            self.db.commit()
            return session
        
        # Criar nova sessão
        new_session = ConversationSession(
            session_key=session_key,
            whatsapp_number=whatsapp_number,
            session_id=session_id,
            config_id=self.config.id if self.config else None,
            rolling_summary="",
            current_turn_count=0,
            total_tokens_used=0
        )
        
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        
        return new_session
    
    def add_conversation_turn(self, session_key: str, role: str, content: str, 
                             rag_context: Dict = None, correlation_id: str = None) -> ConversationTurn:
        """Adiciona um turno à conversa"""
        session = self.db.query(ConversationSession).filter(
            ConversationSession.session_key == session_key
        ).first()
        
        if not session:
            raise ValueError(f"Sessão não encontrada: {session_key}")
        
        # Preparar dados do turno
        turn_data = {
            "session_key": session_key,
            "turn_number": session.current_turn_count + 1,
            "role": role,
            "content": content,
            "correlation_id": correlation_id or str(uuid.uuid4())
        }
        
        # Adicionar contexto RAG se disponível
        if rag_context:
            turn_data.update({
                "rag_citations": rag_context.get("citations", []),
                "rag_collection": rag_context.get("collection"),
                "rag_query": rag_context.get("query")
            })
        
        # Criar turno
        turn = ConversationTurn(**turn_data)
        self.db.add(turn)
        
        # Atualizar sessão
        session.current_turn_count += 1
        session.last_activity = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(turn)
        
        return turn
    
    def get_conversation_context(self, session_key: str, max_tokens: int = None) -> Dict:
        """Obtém contexto da conversa respeitando limites de tokens"""
        if not max_tokens:
            max_tokens = self.config.conversation_window_tokens if self.config else 800
        
        # Buscar turnos recentes
        turns = self.db.query(ConversationTurn).filter(
            ConversationTurn.session_key == session_key
        ).order_by(desc(ConversationTurn.turn_number)).limit(10).all()
        
        # Buscar resumo da sessão
        session = self.db.query(ConversationSession).filter(
            ConversationSession.session_key == session_key
        ).first()
        
        context = {
            "recent_turns": [],
            "rolling_summary": session.rolling_summary if session else "",
            "total_tokens": 0
        }
        
        # Adicionar turnos respeitando limite de tokens
        for turn in reversed(turns):  # Ordem cronológica
            estimated_tokens = len(turn.content.split()) * 1.3  # Estimativa aproximada
            
            if context["total_tokens"] + estimated_tokens <= max_tokens:
                context["recent_turns"].append(turn.to_dict())
                context["total_tokens"] += estimated_tokens
            else:
                break
        
        return context
    
    def update_rolling_summary(self, session_key: str, new_turn: ConversationTurn) -> str:
        """Atualiza o resumo acumulado da sessão"""
        session = self.db.query(ConversationSession).filter(
            ConversationSession.session_key == session_key
        ).first()
        
        if not session:
            return ""
        
        # Lógica simples de resumo (pode ser melhorada com LLM)
        current_summary = session.rolling_summary or ""
        new_content = f"{new_turn.role}: {new_turn.content}"
        
        # Manter resumo dentro do limite de tokens
        max_summary_tokens = self.config.summary_tokens if self.config else 200
        
        if len(current_summary.split()) * 1.3 + len(new_content.split()) * 1.3 > max_summary_tokens:
            # Cortar resumo antigo se necessário
            words = current_summary.split()
            if len(words) > max_summary_tokens * 0.7:
                current_summary = " ".join(words[-int(max_summary_tokens * 0.7):])
        
        # Adicionar novo conteúdo
        if current_summary:
            new_summary = f"{current_summary}\n{new_content}"
        else:
            new_summary = new_content
        
        session.rolling_summary = new_summary
        self.db.commit()
        
        return new_summary
    
    def handle_reset_command(self, whatsapp_number: str, session_id: str) -> bool:
        """Processa comando de reset da conversa"""
        session_key = self._generate_session_key(whatsapp_number, session_id)
        
        # Marcar sessão como inativa
        session = self.db.query(ConversationSession).filter(
            ConversationSession.session_key == session_key
        ).first()
        
        if session:
            session.is_active = False
            self.db.commit()
        
        # Criar nova sessão
        new_session = self.get_or_create_session(whatsapp_number, str(uuid.uuid4()))
        
        return True
    
    def extract_user_memories(self, whatsapp_number: str, turn: ConversationTurn) -> List[UserMemory]:
        """Extrai memórias do usuário do turno (implementação básica)"""
        if not self.config or not self.config.enable_user_memories:
            return []
        
        memories = []
        
        # Lógica simples de extração (pode ser melhorada com LLM)
        content = turn.content.lower()
        
        # Detectar empresa
        if "empresa" in content or "companhia" in content:
            memory = UserMemory(
                whatsapp_number=whatsapp_number,
                memory_type="company",
                memory_value=content,
                confidence=0.7,
                source_turn_id=turn.id,
                opt_in_status=False,  # Requer opt-in explícito
                expires_at=datetime.utcnow() + timedelta(days=self.config.memory_retention_days)
            )
            memories.append(memory)
        
        # Detectar produto de interesse
        if "produto" in content or "serviço" in content:
            memory = UserMemory(
                whatsapp_number=whatsapp_number,
                memory_type="product_interest",
                memory_value=content,
                confidence=0.6,
                source_turn_id=turn.id,
                opt_in_status=False,
                expires_at=datetime.utcnow() + timedelta(days=self.config.memory_retention_days)
            )
            memories.append(memory)
        
        # Salvar memórias
        for memory in memories:
            self.db.add(memory)
        
        self.db.commit()
        return memories
    
    def log_audit(self, session_key: str, action: str, details: Dict, 
                  total_tokens: int = 0, rag_score_avg: float = 0, latency_ms: int = 0):
        """Registra log de auditoria"""
        if not self.config or not self.config.enable_audit_log:
            return
        
        audit_log = ConversationAuditLog(
            session_key=session_key,
            correlation_id=details.get("correlation_id", str(uuid.uuid4())),
            action=action,
            details=details,
            total_tokens=total_tokens,
            rag_score_average=rag_score_avg,
            latency_ms=latency_ms
        )
        
        self.db.add(audit_log)
        self.db.commit()
    
    def cleanup_expired_sessions(self):
        """Limpa sessões expiradas"""
        if not self.config:
            return
        
        ttl_minutes = self.config.session_ttl_minutes
        expiry_time = datetime.utcnow() - timedelta(minutes=ttl_minutes)
        
        expired_sessions = self.db.query(ConversationSession).filter(
            and_(
                ConversationSession.last_activity < expiry_time,
                ConversationSession.is_active == True
            )
        ).all()
        
        for session in expired_sessions:
            session.is_active = False
        
        self.db.commit()
    
    def get_user_memories(self, whatsapp_number: str, memory_types: List[str] = None) -> List[UserMemory]:
        """Obtém memórias do usuário"""
        if not self.config or not self.config.enable_user_memories:
            return []
        
        query = self.db.query(UserMemory).filter(
            and_(
                UserMemory.whatsapp_number == whatsapp_number,
                UserMemory.opt_in_status == True,
                UserMemory.expires_at > datetime.utcnow()
            )
        )
        
        if memory_types:
            query = query.filter(UserMemory.memory_type.in_(memory_types))
        
        return query.all() 