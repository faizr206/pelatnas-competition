from pathlib import Path

from apps.api.app.config import get_settings
from packages.core.constants import JobStatus, SubmissionStatus
from packages.core.time import utcnow
from packages.db.models import Job, Score, Submission, SubmissionArtifact
from packages.db.session import session_scope
from packages.execution.policy import SandboxPolicy, default_sandbox_policy
from packages.leaderboard.service import upsert_leaderboard_entry
from packages.observability.logging import get_logger
from packages.scoring.service import compute_placeholder_score
from packages.storage.service import submission_artifact_dir

logger = get_logger(__name__)


def process_submission_job(job_id: str) -> str:
    settings = get_settings()
    policy = default_sandbox_policy()

    try:
        with session_scope() as session:
            job = session.get(Job, job_id)
            if job is None:
                raise ValueError(f"Job {job_id} was not found.")

            submission = session.get(Submission, job.submission_id)
            if submission is None:
                raise ValueError(f"Submission {job.submission_id} was not found.")

            job.status = JobStatus.RUNNING.value
            job.started_at = utcnow()
            job.worker_id = settings.worker_id
            submission.status = SubmissionStatus.RUNNING.value
            session.flush()

            artifact_dir = submission_artifact_dir(settings.local_storage_root, submission.id)
            _write_execution_log(
                artifact_dir,
                submission_id=submission.id,
                job_id=job.id,
                policy=policy,
            )
            session.add(
                SubmissionArtifact(
                    submission_id=submission.id,
                    artifact_type="stdout.log",
                    storage_path=str(artifact_dir / "stdout.log"),
                    checksum=None,
                    size_bytes=(artifact_dir / "stdout.log").stat().st_size,
                )
            )

            job.status = JobStatus.COLLECTING_ARTIFACTS.value
            session.flush()

            metric_value, score_value = compute_placeholder_score(submission.id)
            job.status = JobStatus.SCORING.value
            session.add(
                Score(
                    submission_id=submission.id,
                    metric_name="placeholder_metric",
                    metric_value=metric_value,
                    score_value=score_value,
                    scoring_version="v1",
                )
            )

            upsert_leaderboard_entry(
                session,
                submission=submission,
                score_value=score_value,
                visibility_type="public",
            )
            upsert_leaderboard_entry(
                session,
                submission=submission,
                score_value=score_value,
                visibility_type="private",
            )

            submission.status = SubmissionStatus.COMPLETED.value
            job.status = JobStatus.COMPLETED.value
            job.finished_at = utcnow()
            session.flush()

        logger.info("Processed submission job %s", job_id)
        return job_id
    except Exception as exc:
        with session_scope() as session:
            job = session.get(Job, job_id)
            if job is not None:
                job.status = JobStatus.FAILED.value
                job.failure_reason = str(exc)
                job.finished_at = utcnow()
                submission = session.get(Submission, job.submission_id)
                if submission is not None:
                    submission.status = SubmissionStatus.FAILED.value
                session.flush()
        logger.exception("Submission job %s failed", job_id)
        raise


def _write_execution_log(
    artifact_dir: Path,
    *,
    submission_id: str,
    job_id: str,
    policy: SandboxPolicy,
) -> None:
    lines = [
        f"submission_id={submission_id}",
        f"job_id={job_id}",
        f"run_as_non_root={policy.run_as_non_root}",
        f"outbound_network_enabled={policy.outbound_network_enabled}",
        f"cpu_limit={policy.cpu_limit}",
        f"memory_limit_mb={policy.memory_limit_mb}",
        f"timeout_minutes={policy.timeout_minutes}",
        "phase0_status=worker_skeleton_executed",
    ]
    (artifact_dir / "stdout.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
