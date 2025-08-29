from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from ..models.llm_config import LLMConfig
from ..schemas.llm_config import LLMConfigCreate, LLMConfigUpdate, LLMConfigResponse

class LLMConfigCRUD:
    """CRUD operations para configurações do LLM"""
    
    @staticmethod
    def create_config(db: Session, config_data: LLMConfigUpdate) -> LLMConfigResponse:
        """Cria uma nova configuração do LLM"""
        # Converter temperatura de float para int (0-200)
        temperature_int = int(config_data.temperature * 100)
        
        db_config = LLMConfig(
            provider=config_data.provider,
            model=config_data.model,
            temperature=temperature_int,
            max_tokens=config_data.max_tokens,
            context_window=config_data.context_window,
            rag_enabled=config_data.rag_enabled,
            default_rag_collection=config_data.default_rag_collection,
            system_prompt=config_data.system_prompt,
            api_key=config_data.api_key,
            base_url=config_data.base_url,
            is_active=True,
            created_by="admin",  # TODO: Pegar do contexto de autenticação
            additional_config=config_data.additional_config
        )
        
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        
        # Converter usando o método to_dict para garantir conversão correta
        config_dict = db_config.to_dict()
        return LLMConfigResponse(**config_dict)
    
    @staticmethod
    def get_active_config(db: Session) -> Optional[LLMConfigResponse]:
        """Obtém a configuração ativa do LLM"""
        db_config = db.query(LLMConfig).filter(LLMConfig.is_active == True).first()
        if db_config:
            # Converter usando o método to_dict para garantir conversão correta
            config_dict = db_config.to_dict()
            return LLMConfigResponse(**config_dict)
        return None
    
    @staticmethod
    def get_config_by_id(db: Session, config_id: int) -> Optional[LLMConfigResponse]:
        """Obtém uma configuração por ID"""
        db_config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if db_config:
            # Converter usando o método to_dict para garantir conversão correta
            config_dict = db_config.to_dict()
            return LLMConfigResponse(**config_dict)
        return None
    
    @staticmethod
    def get_all_configs(db: Session) -> List[LLMConfigResponse]:
        """Lista todas as configurações"""
        db_configs = db.query(LLMConfig).order_by(LLMConfig.created_at.desc()).all()
        return [LLMConfigResponse(**config.to_dict()) for config in db_configs]
    
    @staticmethod
    def update_config(db: Session, config_id: int, config_data: LLMConfigUpdate) -> Optional[LLMConfigResponse]:
        """Atualiza uma configuração existente"""
        db_config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not db_config:
            return None
        
        # Atualizar campos
        for field, value in config_data.dict(exclude_unset=True).items():
            if field == "temperature":
                # Converter temperatura de float para int
                setattr(db_config, field, int(value * 100))
            else:
                setattr(db_config, field, value)
        
        db.commit()
        db.refresh(db_config)
        
        # Converter usando o método to_dict para garantir conversão correta
        config_dict = db_config.to_dict()
        return LLMConfigResponse(**config_dict)
    
    @staticmethod
    def delete_config(db: Session, config_id: int) -> bool:
        """Remove uma configuração"""
        db_config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not db_config:
            return False
        
        db.delete(db_config)
        db.commit()
        return True
    
    @staticmethod
    def deactivate_all_configs(db: Session) -> None:
        """Desativa todas as configurações"""
        db.query(LLMConfig).filter(LLMConfig.is_active == True).update({"is_active": False})
        db.commit()
    
    @staticmethod
    def activate_config(db: Session, config_id: int) -> bool:
        """Ativa uma configuração específica"""
        # Desativar todas as outras
        LLMConfigCRUD.deactivate_all_configs(db)
        
        # Ativar a especificada
        db_config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not db_config:
            return False
        
        db_config.is_active = True
        db.commit()
        return True
    
    @staticmethod
    def get_config_by_provider_and_model(db: Session, provider: str, model: str) -> Optional[LLMConfigResponse]:
        """Obtém configuração por provedor e modelo"""
        db_config = db.query(LLMConfig).filter(
            and_(
                LLMConfig.provider == provider,
                LLMConfig.model == model,
                LLMConfig.is_active == True
            )
        ).first()
        
        if db_config:
            # Converter usando o método to_dict para garantir conversão correta
            config_dict = db_config.to_dict()
            return LLMConfigResponse(**config_dict)
        return None 