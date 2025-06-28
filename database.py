import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    content_hash = Column(String, unique=True, nullable=False)
    chunk_count = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=True)
    source_documents = Column(Text, nullable=True)  # JSON string
    model_used = Column(String, default="gpt-3.5-turbo")
    temperature = Column(Float, default=0.1)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    total_questions = Column(Integer, default=0)

# Database operations class
class DatabaseManager:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    def save_document(self, name: str, file_type: str, content_hash: str, chunk_count: int) -> Document:
        """Save document metadata to database"""
        db = self.get_session()
        try:
            # Check if document already exists
            existing_doc = db.query(Document).filter(Document.content_hash == content_hash).first()
            if existing_doc:
                return existing_doc
            
            document = Document(
                name=name,
                file_type=file_type,
                content_hash=content_hash,
                chunk_count=chunk_count,
                processed=True
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            return document
        finally:
            db.close()
    
    def get_or_create_session(self, session_id: str) -> ChatSession:
        """Get existing session or create new one"""
        db = self.get_session()
        try:
            session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if not session:
                session = ChatSession(session_id=session_id)
                db.add(session)
                db.commit()
                db.refresh(session)
            else:
                # Update last activity
                session.last_activity = datetime.utcnow()
                db.commit()
            return session
        finally:
            db.close()
    
    def save_conversation(self, session_id: str, question: str, answer: str, 
                         confidence_score: float = None, source_documents: str = None,
                         model_used: str = "gpt-3.5-turbo", temperature: float = 0.1) -> Conversation:
        """Save a conversation exchange to database"""
        db = self.get_session()
        try:
            # Ensure session exists
            self.get_or_create_session(session_id)
            
            conversation = Conversation(
                session_id=session_id,
                question=question,
                answer=answer,
                confidence_score=confidence_score,
                source_documents=source_documents,
                model_used=model_used,
                temperature=temperature
            )
            db.add(conversation)
            
            # Update session question count
            session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if session:
                session.total_questions += 1
                session.last_activity = datetime.utcnow()
            
            db.commit()
            db.refresh(conversation)
            return conversation
        finally:
            db.close()
    
    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Conversation]:
        """Get conversation history for a session"""
        db = self.get_session()
        try:
            conversations = db.query(Conversation)\
                .filter(Conversation.session_id == session_id)\
                .order_by(Conversation.created_at.desc())\
                .limit(limit)\
                .all()
            return list(reversed(conversations))  # Return in chronological order
        finally:
            db.close()
    
    def get_all_documents(self) -> List[Document]:
        """Get all processed documents"""
        db = self.get_session()
        try:
            return db.query(Document).filter(Document.processed == True).all()
        finally:
            db.close()
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        db = self.get_session()
        try:
            session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if not session:
                return {"total_questions": 0, "created_at": None, "last_activity": None}
            
            return {
                "total_questions": session.total_questions,
                "created_at": session.created_at,
                "last_activity": session.last_activity
            }
        finally:
            db.close()
    
    def clear_session_history(self, session_id: str):
        """Clear conversation history for a session"""
        db = self.get_session()
        try:
            db.query(Conversation).filter(Conversation.session_id == session_id).delete()
            
            # Reset session stats
            session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if session:
                session.total_questions = 0
                session.last_activity = datetime.utcnow()
            
            db.commit()
        finally:
            db.close()

# Global database manager instance
db_manager = DatabaseManager()

def init_database():
    """Initialize the database with all tables"""
    db_manager.create_tables()
    return db_manager
