from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    number: str
    name: Optional[str] = None
    company: Optional[str] = None
    note: Optional[str] = None
    expires_at: Optional[datetime] = None
    active: bool = True
    role: str = "user"
    status_reason: Optional[str] = None
    tags: List[str] = []

class UserCreate(UserBase):
    added_by: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    note: Optional[str] = None
    expires_at: Optional[datetime] = None
    active: Optional[bool] = None
    role: Optional[str] = None
    status_reason: Optional[str] = None
    tags: Optional[List[str]] = None

class UserResponse(UserBase):
    id: int
    added_by: Optional[str]
    created_at: datetime
    last_interact: Optional[datetime]
    interact_count: int
    
    model_config = {
        "from_attributes": True
    }

class UserList(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    per_page: int 