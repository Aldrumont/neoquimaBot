from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from ..models.base import Base

# Configuração do banco
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://neoquima_admin:neoquima_admin_pass_2024@shared-postgres:5432/neoquima_shared"
)

# Criar engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=os.getenv("DEBUG", "false").lower() == "true"
)

# Criar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency para obter sessão do banco"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Inicializar banco de dados"""
    Base.metadata.create_all(bind=engine) 