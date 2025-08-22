from .config import Base, engine, get_db
from .models import User
from .schemas import UserBase, UserCreate, UserUpdate, UserResponse, UserList
from .crud import UserCRUD

# Criar todas as tabelas
def create_tables():
    Base.metadata.create_all(bind=engine) 