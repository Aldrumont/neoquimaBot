from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..core.database import get_db
from ..models.llm_config import LLMConfig
from ..schemas.llm_config import LLMConfigCreate, LLMConfigUpdate, LLMConfigResponse
from ..crud.llm_config import LLMConfigCRUD

router = APIRouter(prefix="/llm", tags=["LLM Configuration"])

@router.get("/config", response_model=LLMConfigResponse)
async def get_llm_config(db: Session = Depends(get_db)):
    """Obtém a configuração ativa do LLM"""
    try:
        config = LLMConfigCRUD.get_active_config(db)
        if not config:
            # Retornar configuração padrão se não existir
            return LLMConfigResponse(
                provider="ollama",
                model="llama2:3b",
                temperature=0.7,
                max_tokens=1000,
                context_window=4096,
                rag_enabled=True,
                default_rag_collection=None,
                system_prompt="Você é um assistente útil e amigável. Responda de forma clara e concisa.",
                id=0,
                is_active=True,
                created_at=datetime.now()
            )
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter configuração: {str(e)}")

@router.put("/config", response_model=LLMConfigResponse)
async def update_llm_config(config: LLMConfigUpdate, db: Session = Depends(get_db)):
    """Atualiza a configuração do LLM"""
    try:
        # Desativar configuração anterior se existir
        LLMConfigCRUD.deactivate_all_configs(db)
        
        # Criar nova configuração
        new_config = LLMConfigCRUD.create_config(db, config)
        return new_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar configuração: {str(e)}")

@router.get("/configs", response_model=List[LLMConfigResponse])
async def list_llm_configs(db: Session = Depends(get_db)):
    """Lista todas as configurações do LLM"""
    try:
        configs = LLMConfigCRUD.get_all_configs(db)
        return configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar configurações: {str(e)}")

@router.get("/configs/{config_id}", response_model=LLMConfigResponse)
async def get_llm_config_by_id(config_id: int, db: Session = Depends(get_db)):
    """Obtém uma configuração específica por ID"""
    try:
        config = LLMConfigCRUD.get_config_by_id(db, config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuração não encontrada")
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter configuração: {str(e)}")

@router.delete("/configs/{config_id}")
async def delete_llm_config(config_id: int, db: Session = Depends(get_db)):
    """Remove uma configuração do LLM"""
    try:
        success = LLMConfigCRUD.delete_config(db, config_id)
        if not success:
            raise HTTPException(status_code=404, detail="Configuração não encontrada")
        return {"message": "Configuração removida com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover configuração: {str(e)}")

@router.post("/configs/{config_id}/activate")
async def activate_llm_config(config_id: int, db: Session = Depends(get_db)):
    """Ativa uma configuração específica"""
    try:
        success = LLMConfigCRUD.activate_config(db, config_id)
        if not success:
            raise HTTPException(status_code=404, detail="Configuração não encontrada")
        return {"message": "Configuração ativada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ativar configuração: {str(e)}") 