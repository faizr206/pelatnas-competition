from pathlib import Path


def ensure_storage_root(storage_root: str) -> Path:
    root = Path(storage_root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def submission_artifact_dir(storage_root: str, submission_id: str) -> Path:
    root = ensure_storage_root(storage_root)
    artifact_dir = root / "artifacts" / submission_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return artifact_dir
