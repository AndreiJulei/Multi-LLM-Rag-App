from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
from datetime import datetime


# USER
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserOut(UserBase):
    id: int
    is_admin: bool

    class Config:
        from_attributes = True


# COLLECTION
class CollectionCreate(BaseModel):
    name: str


class CollectionOut(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# DOCUMENT
class DocumentOut(BaseModel):
    id: int
    filename: str
    file_type: str
    status: str

    class Config:
        from_attributes = True


# CHAT
class ChatRequest(BaseModel):
    collection_id: int
    query: str
    mode: str = "debate"  # 'debate' or a specific model ID


class VoteRequest(BaseModel):
    chat_id: int
    winner: str  # any model ID


class BlindVoteRequest(BaseModel):
    chat_id: int


class ChatResponse(BaseModel):
    id: int
    question: str
    final_answer: Optional[str] = None
    llm_responses: Optional[Dict[str, str]] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# ADMIN SETTINGS
class SystemSettingsUpdate(BaseModel):
    api_keys: Optional[Dict[str, str]] = None   # create dictionary with provider->keys so when adding a key we dont need to change the schema
    active_models: Optional[List[str]] = None


class SystemSettingsOut(BaseModel):
    api_keys: Dict[str, str] = {}
    active_models: List[str] = []

    class Config:
        from_attributes = True