from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from .config import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    company = Column(String(100), nullable=True)
    note = Column(Text, nullable=True)
    added_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_interact = Column(DateTime(timezone=True), nullable=True)
    interact_count = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    role = Column(String(50), default="user")  # user, admin, moderator
    status_reason = Column(Text, nullable=True)
    tags = Column(JSON, default=list) 