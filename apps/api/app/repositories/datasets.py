from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.db.models import Dataset


def list_datasets(db: Session, *, competition_id: str) -> list[Dataset]:
    return list(
        db.scalars(
            select(Dataset)
            .where(Dataset.competition_id == competition_id)
            .order_by(Dataset.version.desc(), Dataset.created_at.desc())
        ).all()
    )


def get_dataset_by_id(db: Session, dataset_id: str) -> Dataset | None:
    return db.scalar(select(Dataset).where(Dataset.id == dataset_id))


def get_next_dataset_version(db: Session, *, competition_id: str) -> int:
    datasets = list_datasets(db, competition_id=competition_id)
    if not datasets:
        return 1
    return max(dataset.version for dataset in datasets) + 1
