from __future__ import annotations

import json
from pathlib import Path

from apps.api.app.config import get_settings
from packages.core.constants import JobStatus, SubmissionStatus
from packages.core.time import utcnow
from packages.db.models import Competition, Job, Score, Submission, SubmissionArtifact
from packages.db.session import session_scope
from packages.execution.policy import SandboxPolicy, default_sandbox_policy
from packages.leaderboard.service import refresh_leaderboard
from packages.observability.logging import get_logger
from packages.scoring.service import compute_submission_score
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

            competition = session.get(Competition, submission.competition_id)
            if competition is None:
                raise ValueError(f"Competition {submission.competition_id} was not found.")

            _validate_submission(submission=submission, competition=competition)

            job.status = JobStatus.RUNNING.value
            job.started_at = utcnow()
            job.worker_id = settings.worker_id
            submission.status = SubmissionStatus.RUNNING.value
            session.flush()

            artifact_dir = submission_artifact_dir(settings.local_storage_root, submission.id)
            _write_execution_log(
                artifact_dir,
                submission=submission,
                job=job,
                policy=policy,
            )

            submission.status = SubmissionStatus.COLLECTING.value
            job.status = JobStatus.COLLECTING.value
            session.add(
                SubmissionArtifact(
                    submission_id=submission.id,
                    artifact_type="stdout.log",
                    storage_path=str(artifact_dir / "stdout.log"),
                    checksum=None,
                    size_bytes=(artifact_dir / "stdout.log").stat().st_size,
                )
            )
            session.flush()

            submission.status = SubmissionStatus.SCORING.value
            job.status = JobStatus.SCORING.value
            metric_value, score_value = compute_submission_score(
                submission_type=submission.submission_type,
                source_path=submission.source_archive_path,
                scoring_metric=competition.scoring_metric,
                solution_path=competition.solution_path,
                metric_script_path=competition.metric_script_path,
            )
            metrics_path = artifact_dir / "metrics.json"
            metrics_payload = {
                "metric_name": competition.scoring_metric,
                "metric_value": metric_value,
                "score_value": score_value,
                "scoring_direction": competition.scoring_direction,
                "best_submission_rule": competition.best_submission_rule,
            }
            metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")
            session.add(
                SubmissionArtifact(
                    submission_id=submission.id,
                    artifact_type="metrics.json",
                    storage_path=str(metrics_path),
                    checksum=None,
                    size_bytes=metrics_path.stat().st_size,
                )
            )
            session.add(
                Score(
                    submission_id=submission.id,
                    metric_name=competition.scoring_metric,
                    metric_value=metric_value,
                    score_value=score_value,
                    scoring_version="v1",
                )
            )
            session.flush()

            refresh_leaderboard(
                session,
                competition=competition,
                phase_id=submission.phase_id,
                visibility_type="public",
            )
            refresh_leaderboard(
                session,
                competition=competition,
                phase_id=submission.phase_id,
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


def _validate_submission(*, submission: Submission, competition: Competition) -> None:
    suffix = Path(submission.source_original_filename).suffix.lower()
    if submission.submission_type == "csv":
        if not competition.allow_csv_submissions:
            raise ValueError("CSV submissions are disabled for this competition.")
        if suffix != ".csv":
            raise ValueError("CSV submissions must use the .csv extension.")
    elif submission.submission_type == "notebook":
        if not competition.allow_notebook_submissions:
            raise ValueError("Notebook submissions are disabled for this competition.")
        if suffix != ".ipynb":
            raise ValueError("Notebook submissions must use the .ipynb extension.")
    else:
        raise ValueError(f"Unsupported submission type: {submission.submission_type}")


def _write_execution_log(
    artifact_dir: Path,
    *,
    submission: Submission,
    job: Job,
    policy: SandboxPolicy,
) -> None:
    lines = [
        f"submission_id={submission.id}",
        f"job_id={job.id}",
        f"submission_type={submission.submission_type}",
        f"source_original_filename={submission.source_original_filename}",
        f"run_as_non_root={policy.run_as_non_root}",
        f"outbound_network_enabled={policy.outbound_network_enabled}",
        f"cpu_limit={policy.cpu_limit}",
        f"memory_limit_mb={policy.memory_limit_mb}",
        f"timeout_minutes={policy.timeout_minutes}",
        "phase1_status=worker_pipeline_executed",
    ]
    (artifact_dir / "stdout.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
