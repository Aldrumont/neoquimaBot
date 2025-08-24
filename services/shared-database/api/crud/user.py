from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional
from datetime import datetime, timezone
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate

class UserCRUD:
    """Operações CRUD para usuários"""
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Cria um novo usuário"""
        db_user = User(
            number=user_data.number,
            name=user_data.name,
            company=user_data.company,
            note=user_data.note,
            role=user_data.role,
            active=user_data.active,
            expires_at=user_data.expires_at,
            tags=user_data.tags
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Obtém usuário por ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_number(db: Session, number: str) -> Optional[User]:
        """Obtém usuário por número de telefone"""
        return db.query(User).filter(User.number == number).first()
    
    @staticmethod
    def get_users(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True,
        search: Optional[str] = None
    ) -> tuple[List[User], int]:
        """Lista usuários com paginação e filtros"""
        query = db.query(User)
        
        # Filtro por status ativo
        if active_only:
            query = query.filter(User.active == True)
        
        # Filtro de busca
        if search:
            search_filter = or_(
                User.name.ilike(f"%{search}%"),
                User.number.ilike(f"%{search}%"),
                User.company.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Contar total
        total = query.count()
        
        # Aplicar paginação
        users = query.offset(skip).limit(limit).all()
        
        return users, total
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Atualiza um usuário existente"""
        db_user = UserCRUD.get_user_by_id(db, user_id)
        if not db_user:
            return None
        
        # Atualizar apenas campos fornecidos
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db_user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Remove um usuário"""
        db_user = UserCRUD.get_user_by_id(db, user_id)
        if not db_user:
            return False
        
        db.delete(db_user)
        db.commit()
        return True
    
    @staticmethod
    def record_interaction(db: Session, number: str) -> bool:
        """Registra uma interação do usuário"""
        db_user = UserCRUD.get_user_by_number(db, number)
        if not db_user:
            return False
        
        db_user.last_interact = datetime.now(timezone.utc)
        db_user.interact_count += 1
        db.commit()
        return True
    
    @staticmethod
    def get_expired_users(db: Session) -> List[User]:
        """Retorna usuários que expiraram"""
        now = datetime.now(timezone.utc)
        return db.query(User).filter(
            and_(
                User.active == True,
                User.expires_at.isnot(None),
                User.expires_at < now
            )
        ).all()
    
    @staticmethod
    def deactivate_expired_users(db: Session) -> int:
        """Desativa usuários expirados automaticamente"""
        expired_users = UserCRUD.get_expired_users(db)
        count = 0
        
        for user in expired_users:
            user.active = False
            user.status_reason = f"Automatically deactivated - expired on {user.expires_at.isoformat()}"
            count += 1
        
        if count > 0:
            db.commit()
        
        return count 