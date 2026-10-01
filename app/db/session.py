from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL)

Session = sessionmaker(
    bind=engine,
    autoflush=False,
)


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()
