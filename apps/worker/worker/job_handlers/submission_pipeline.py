from __future__ import annotations

import json
import tempfile
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
from packages.storage.service import download_file_to_path, save_local_file

logger = get_logger(__name__)


def process_submission_job(job_id: str) -> str:
    settings = get_settings()
    policy = default_sandbox_policy()
    Path(settings.worker_local_tmp_dir).mkdir(parents=True, exist_ok=True)

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

            with tempfile.TemporaryDirectory(
                prefix=f"submission-{submission.id}-",
                dir=settings.worker_local_tmp_dir,
            ) as work_dir:
                work_path = Path(work_dir)
                artifact_dir = work_path / "artifacts"
                artifact_dir.mkdir(parents=True, exist_ok=True)

                local_source_path = _stage_object(
                    object_key=submission.source_archive_path,
                    target_path=work_path / submission.source_original_filename,
                )
                local_solution_path = (
                    None
                    if not competition.solution_path
                    else _stage_optional_competition_object(
                        competition=competition,
                        field_name="solution_path",
                        filename_field_name="solution_filename",
                        object_key=competition.solution_path,
                        target_path=work_path / (competition.solution_filename or "solution.csv"),
                    )
                )
                local_metric_script_path = (
                    None
                    if not competition.metric_script_path
                    else _stage_optional_competition_object(
                        competition=competition,
                        field_name="metric_script_path",
                        filename_field_name="metric_script_filename",
                        object_key=competition.metric_script_path,
                        target_path=work_path
                        / (competition.metric_script_filename or "custom_metric.py"),
                    )
                )

                _write_execution_log(
                    artifact_dir,
                    submission=submission,
                    job=job,
                    policy=policy,
                )

                submission.status = SubmissionStatus.COLLECTING.value
                job.status = JobStatus.COLLECTING.value
                stdout_artifact = save_local_file(
                    category="artifacts",
                    competition_slug=competition.slug,
                    filename=f"{submission.id}-stdout.log",
                    source_path=str(artifact_dir / "stdout.log"),
                    content_type="text/plain; charset=utf-8",
                )
                session.add(
                    SubmissionArtifact(
                        submission_id=submission.id,
                        artifact_type="stdout.log",
                        storage_path=stdout_artifact.absolute_path,
                        checksum=stdout_artifact.checksum,
                        size_bytes=stdout_artifact.size_bytes,
                    )
                )
                session.flush()

                submission.status = SubmissionStatus.SCORING.value
                job.status = JobStatus.SCORING.value
                metric_value, score_value = compute_submission_score(
                    submission_type=submission.submission_type,
                    source_path=local_source_path,
                    scoring_metric=competition.scoring_metric,
                    solution_path=local_solution_path,
                    metric_script_path=local_metric_script_path,
                    artifact_dir=str(artifact_dir),
                )
                if submission.submission_type == "notebook":
                    converted_source = artifact_dir / "participant_submission.py"
                    if converted_source.exists():
                        uploaded_converted = save_local_file(
                            category="artifacts",
                            competition_slug=competition.slug,
                            filename=f"{submission.id}-participant_submission.py",
                            source_path=str(converted_source),
                            content_type="text/x-python",
                        )
                        session.add(
                            SubmissionArtifact(
                                submission_id=submission.id,
                                artifact_type="participant_submission.py",
                                storage_path=uploaded_converted.absolute_path,
                                checksum=uploaded_converted.checksum,
                                size_bytes=uploaded_converted.size_bytes,
                            )
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
                uploaded_metrics = save_local_file(
                    category="artifacts",
                    competition_slug=competition.slug,
                    filename=f"{submission.id}-metrics.json",
                    source_path=str(metrics_path),
                    content_type="application/json",
                )
                session.add(
                    SubmissionArtifact(
                        submission_id=submission.id,
                        artifact_type="metrics.json",
                        storage_path=uploaded_metrics.absolute_path,
                        checksum=uploaded_metrics.checksum,
                        size_bytes=uploaded_metrics.size_bytes,
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


def _stage_object(*, object_key: str, target_path: Path) -> str:
    return download_file_to_path(object_key, str(target_path))


def _stage_optional_competition_object(
    *,
    competition: Competition,
    field_name: str,
    filename_field_name: str,
    object_key: str,
    target_path: Path,
) -> str | None:
    try:
        return _stage_object(object_key=object_key, target_path=target_path)
    except FileNotFoundError:
        logger.warning(
            "Competition %s references missing storage object %s for %s. Clearing stale reference.",
            competition.id,
            object_key,
            field_name,
        )
        setattr(competition, field_name, None)
        setattr(competition, filename_field_name, None)
        return None
