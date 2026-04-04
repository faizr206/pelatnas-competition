from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.core.time import utcnow
from packages.db.models import WorkerNode
from packages.db.session import session_scope

ONLINE_HEARTBEAT_TTL = timedelta(seconds=90)


def get_worker_node(db: Session, *, worker_id: str) -> WorkerNode | None:
    return db.scalar(select(WorkerNode).where(WorkerNode.worker_id == worker_id))


def upsert_worker_node(
    db: Session,
    *,
    worker_id: str,
    is_enabled: bool | None = None,
    gpu_available: bool | None = None,
    heartbeat: bool = False,
) -> WorkerNode:
    worker = get_worker_node(db, worker_id=worker_id)
    if worker is None:
        worker = WorkerNode(worker_id=worker_id, is_enabled=True, gpu_available=False)
        db.add(worker)
        db.flush()

    if is_enabled is not None:
        worker.is_enabled = is_enabled
    if gpu_available is not None:
        worker.gpu_available = gpu_available
    if heartbeat:
        worker.last_heartbeat_at = utcnow()

    db.add(worker)
    db.flush()
    return worker


def heartbeat_worker(worker_id: str, *, gpu_available: bool | None = None) -> None:
    with session_scope() as session:
        upsert_worker_node(
            session,
            worker_id=worker_id,
            gpu_available=gpu_available,
            heartbeat=True,
        )


def is_worker_enabled(worker_id: str) -> bool:
    with session_scope() as session:
        worker = get_worker_node(session, worker_id=worker_id)
        if worker is None:
            return True
        return worker.is_enabled


def list_worker_nodes(db: Session) -> list[WorkerNode]:
    return list(db.scalars(select(WorkerNode).order_by(WorkerNode.worker_id.asc())).all())


def worker_is_online(worker: WorkerNode) -> bool:
    if worker.last_heartbeat_at is None:
        return False
    heartbeat_at = cast(datetime, worker.last_heartbeat_at)
    if heartbeat_at.tzinfo is None:
        heartbeat_at = heartbeat_at.replace(tzinfo=UTC)
    return bool(heartbeat_at >= utcnow() - ONLINE_HEARTBEAT_TTL)
