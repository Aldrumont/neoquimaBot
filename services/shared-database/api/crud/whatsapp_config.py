from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from ..models.whatsapp_config import WhatsAppConfig
from ..schemas.whatsapp_config import WhatsAppConfigCreate, WhatsAppConfigUpdate, WhatsAppConfigResponse

class WhatsAppConfigCRUD:
    """CRUD operations para configurações do WhatsApp"""
    
    @staticmethod
    def create_config(db: Session, config_data: WhatsAppConfigCreate) -> WhatsAppConfigResponse:
        """Cria uma nova configuração do WhatsApp"""
        # Desativar configurações existentes
        db.query(WhatsAppConfig).update({"is_active": False})
        
        db_config = WhatsAppConfig(
            access_token=config_data.access_token,
            phone_number_id=config_data.phone_number_id,
            business_account_id=config_data.business_account_id,
            verify_token=config_data.verify_token,
            webhook_url=config_data.webhook_url,
            is_active=True,
            created_by="admin"  # TODO: Pegar do contexto de autenticação
        )
        
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        
        return WhatsAppConfigResponse(
            id=db_config.id,
            access_token=db_config.access_token,
            phone_number_id=db_config.phone_number_id,
            business_account_id=db_config.business_account_id,
            verify_token=db_config.verify_token,
            webhook_url=db_config.webhook_url,
            is_active=db_config.is_active,
            created_at=db_config.created_at,
            updated_at=db_config.updated_at,
            created_by=db_config.created_by
        )
    
    @staticmethod
    def get_active_config(db: Session) -> Optional[WhatsAppConfigResponse]:
        """Obtém a configuração ativa do WhatsApp"""
        db_config = db.query(WhatsAppConfig).filter(WhatsAppConfig.is_active == True).first()
        if db_config:
            return WhatsAppConfigResponse(
                id=db_config.id,
                access_token=db_config.access_token,
                phone_number_id=db_config.phone_number_id,
                business_account_id=db_config.business_account_id,
                verify_token=db_config.verify_token,
                webhook_url=db_config.webhook_url,
                is_active=db_config.is_active,
                created_at=db_config.created_at,
                updated_at=db_config.updated_at,
                created_by=db_config.created_by
            )
        return None
    
    @staticmethod
    def update_config(db: Session, config_data: WhatsAppConfigUpdate) -> Optional[WhatsAppConfigResponse]:
        """Atualiza a configuração ativa do WhatsApp"""
        db_config = db.query(WhatsAppConfig).filter(WhatsAppConfig.is_active == True).first()
        if not db_config:
            return None
        
        # Atualizar apenas campos fornecidos
        if config_data.access_token is not None:
            db_config.access_token = config_data.access_token
        if config_data.phone_number_id is not None:
            db_config.phone_number_id = config_data.phone_number_id
        if config_data.business_account_id is not None:
            db_config.business_account_id = config_data.business_account_id
        if config_data.verify_token is not None:
            db_config.verify_token = config_data.verify_token
        if config_data.webhook_url is not None:
            db_config.webhook_url = config_data.webhook_url
        
        db.commit()
        db.refresh(db_config)
        
        return WhatsAppConfigResponse(
            id=db_config.id,
            access_token=db_config.access_token,
            phone_number_id=db_config.phone_number_id,
            business_account_id=db_config.business_account_id,
            verify_token=db_config.verify_token,
            webhook_url=db_config.webhook_url,
            is_active=db_config.is_active,
            created_at=db_config.created_at,
            updated_at=db_config.updated_at,
            created_by=db_config.created_by
        )
    
    @staticmethod
    def delete_config(db: Session, config_id: int) -> bool:
        """Remove uma configuração do WhatsApp"""
        db_config = db.query(WhatsAppConfig).filter(WhatsAppConfig.id == config_id).first()
        if not db_config:
            return False
        
        db.delete(db_config)
        db.commit()
        return True 