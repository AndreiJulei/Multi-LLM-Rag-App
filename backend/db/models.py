from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON
from sqlaclhemy.orm import relationship
from sqlalchemy.sql import func

try:
    from .database import Base
except ImportError:
    from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key = True, index = True)
    email = Column(String, unique = True, index = True, nullable = False)
    hashed_password = Column(String, nullable = False)
    is_admin = Column(Boolean, default = False)

    collections = relationship("Collection", back_populates="owner", cascade="all, delete-orphan")
    chats = relationship("ChatHistory", back_populates="owner", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")


class Collection(Base):
    __tablename__ = "collections"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="collections")
    documents = relationship("Document", back_populates="collection", cascade="all, delete-orphan")
    chats = relationship("ChatHistory", back_populates="collection", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    status = Column(String, default="pending")
    user_id = Column(Integer, ForeignKey("users.id"))
    collection_id = Column(Integer, ForeignKey("collections.id", ondelete="CASCADE"), nullable=True)

    owner = relationship("User", back_populates="documents")
    collection = relationship("Collection", back_populates="documents")


class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    collection_id = Column(Integer, ForeignKey("collections.id", ondelete="CASCADE"))
    question = Column(Text, nullable=False)
    context = Column(Text)

    final_answer = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="chats")
    collection = relationship("Collection", back_populates="chats")


class SystemSettings(Base):
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True, index=True)
