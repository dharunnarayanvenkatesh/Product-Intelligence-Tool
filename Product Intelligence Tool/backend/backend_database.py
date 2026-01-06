from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, DateTime, Integer, JSON, Float, Index, text
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/cxm_intelligence")

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=20, max_overflow=40)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=True)
    event_name = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    source = Column(String, nullable=False, index=True)
    properties = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_event_timestamp', 'event_name', 'timestamp'),
    )

class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String, nullable=False, index=True)
    metric_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    metadata = Column(JSON, nullable=True)
    computed_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_metric_date', 'metric_name', 'date'),
    )

class Insight(Base):
    __tablename__ = "insights"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    insight_type = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False)
    title = Column(String, nullable=False)
    detected_at = Column(DateTime, nullable=False, index=True)
    data = Column(JSON, nullable=False)
    llm_explanation = Column(String, nullable=True)
    resolved = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

class SyncState(Base):
    __tablename__ = "sync_state"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, unique=True, nullable=False)
    last_sync = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)
    metadata = Column(JSON, nullable=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session