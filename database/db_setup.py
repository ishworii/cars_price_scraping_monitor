from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from contextlib import contextmanager

from .models import Base
from settings import DATABASE_URL


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def init_db(logger):
    """Attempt to create tables."""
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully.")
    except OperationalError:
        logger.info("Error occurred during table creation.")
        # Additional error handling/logic can go here


@contextmanager
def get_db_session():
    """Provide a scoped session for database operations."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
