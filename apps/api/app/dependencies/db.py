from collections.abc import Generator

from sqlalchemy.orm import Session

from packages.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
