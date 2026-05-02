from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
import os

load_dotenv()

class Base(DeclarativeBase):
    pass

DB = os.getenv("SUPABASE_DB") or ""
engine = create_engine(DB)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def connect():
    import models
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()