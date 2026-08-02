import os

from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Item(Base):
    """Mirrors BeBot's own local `aorefs` table shape (id/ql/icon/name) plus
    a few extra columns the item dump may carry that `aorefs` doesn't - kept
    even though today's AOML output doesn't use them, so a future
    output=json doesn't need a re-import."""

    __tablename__ = "items"

    id = Column(Integer, primary_key=True, autoincrement=False)  # aoid
    name = Column(String(255), nullable=False, index=True)
    ql = Column(Integer, nullable=False, default=0)
    icon = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]
    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = os.environ.get("DB_PORT", "3306")
    name = os.environ.get("DB_NAME", "aodb")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"


def make_session_factory(database_url: str | None = None):
    engine = create_engine(database_url or _database_url(), pool_pre_ping=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
