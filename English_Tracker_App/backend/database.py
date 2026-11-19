from sqlalchemy import URL, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from settings import STATE_DIR


STATE_DIR.mkdir(parents=True, exist_ok=True)
SQLALCHEMY_DATABASE_URL = URL.create("sqlite", database=str(STATE_DIR / "english_tracker.db"))

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 10}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    with SessionLocal() as db:
        yield db
