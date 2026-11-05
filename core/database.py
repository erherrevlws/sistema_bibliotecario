from sqlmodel import SQLModel, create_engine, Session
from core.config import DATABASE_URL

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def create_db_and_tables():
    # Asegura que todos los modelos queden registrados en el objeto metadata
    import models.models
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
