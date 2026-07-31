import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default to Docker-based PostgreSQL container on port 5434
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5434/banking_db")

# Create engine and session maker
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for SQLAlchemy models
Base = declarative_base()

def get_db():
    """Dependency injection helper for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
