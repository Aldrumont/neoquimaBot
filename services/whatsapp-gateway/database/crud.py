from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional
from datetime import datetime, timezone
from . import models, schemas

class UserCRUD:
    
    @staticmethod
    def create_user(db: Session, user: schemas.UserCreate) -> models.User:
        db_user = models.User(**user.model_dump())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[models.User]:
        return db.query(models.User).filter(models.User.id == user_id).first()
    
    @staticmethod
    def get_user_by_number(db: Session, number: str) -> Optional[models.User]:
        return db.query(models.User).filter(models.User.number == number).first()
    
    @staticmethod
    def get_users(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True,
        search: Optional[str] = None
    ) -> List[models.User]:
        query = db.query(models.User)
        
        if active_only:
            query = query.filter(models.User.active == True)
        
        if search:
            search_filter = or_(
                models.User.name.ilike(f"%{search}%"),
                models.User.company.ilike(f"%{search}%"),
                models.User.number.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> Optional[models.User]:
        db_user = UserCRUD.get_user(db, user_id)
        if not db_user:
            return None
        
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        db_user = UserCRUD.get_user(db, user_id)
        if not db_user:
            return False
        
        db.delete(db_user)
        db.commit()
        return True
    
    @staticmethod
    def deactivate_user(db: Session, user_id: int, reason: str = None) -> Optional[models.User]:
        db_user = UserCRUD.get_user(db, user_id)
        if not db_user:
            return None
        
        db_user.active = False
        db_user.status_reason = reason
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def record_interaction(db: Session, number: str) -> Optional[models.User]:
        db_user = UserCRUD.get_user_by_number(db, number)
        if not db_user:
            return None
        
        db_user.last_interact = datetime.now(timezone.utc)
        db_user.interact_count += 1
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_active_users_count(db: Session) -> int:
        from sqlalchemy import func
        return db.query(func.count(models.User.id)).filter(models.User.active == True).scalar()
    
    @staticmethod
    def get_users_by_role(db: Session, role: str) -> List[models.User]:
        return db.query(models.User).filter(models.User.role == role).all()
    
    @staticmethod
    def get_users_by_tags(db: Session, tags: List[str]) -> List[models.User]:
        # Para JSON, vamos buscar usuários que tenham pelo menos uma das tags
        from sqlalchemy import or_
        return db.query(models.User).filter(
            or_(*[models.User.tags.contains([tag]) for tag in tags])
        ).all()
    
    @staticmethod
    def get_expired_users(db: Session) -> List[models.User]:
        """Retorna usuários que expiraram"""
        from sqlalchemy import and_
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        return db.query(models.User).filter(
            and_(
                models.User.active == True,
                models.User.expires_at.isnot(None),
                models.User.expires_at < now
            )
        ).all()
    
    @staticmethod
    def get_expiring_soon_users(db: Session, days: int = 7) -> List[models.User]:
        """Retorna usuários que expiram em X dias"""
        from sqlalchemy import and_
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=days)
        
        return db.query(models.User).filter(
            and_(
                models.User.active == True,
                models.User.expires_at.isnot(None),
                models.User.expires_at >= now,
                models.User.expires_at <= future
            )
        ).all()
    
    @staticmethod
    def deactivate_expired_users(db: Session) -> int:
        """Desativa automaticamente usuários expirados e retorna quantidade"""
        from sqlalchemy import and_
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        expired_users = db.query(models.User).filter(
            and_(
                models.User.active == True,
                models.User.expires_at.isnot(None),
                models.User.expires_at < now
            )
        ).all()
        
        count = 0
        for user in expired_users:
            user.active = False
            user.status_reason = f"Automatically deactivated - expired on {user.expires_at.isoformat()}"
            count += 1
        
        if count > 0:
            db.commit()
        
        return count 