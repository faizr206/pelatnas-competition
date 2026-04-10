from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from packages.core.constants import ScoringDirection
from packages.db.models import Competition, LeaderboardEntry, Score, Submission, User


@dataclass(frozen=True)
class SubmissionScoreRow:
    submission: Submission
    score: Score


def refresh_leaderboard(
    db: Session,
    *,
    competition: Competition,
    phase_id: str,
    visibility_type: str,
) -> list[LeaderboardEntry]:
    rows = [
        SubmissionScoreRow(submission=submission, score=score)
        for submission, score in db.execute(
            select(Submission, Score)
            .join(Score, Score.submission_id == Submission.id)
            .join(User, User.id == Submission.user_id)
            .where(Submission.competition_id == competition.id)
            .where(Submission.phase_id == phase_id)
            .where(Submission.is_late_submission.is_(False))
            .where(Submission.display_on_leaderboard.is_(True))
            .where(User.hide_from_leaderboard.is_(False))
        ).all()
    ]

    best_by_user: dict[str, SubmissionScoreRow] = {}
    for row in rows:
        existing = best_by_user.get(row.submission.user_id)
        if existing is None or _is_better(
            candidate=row,
            current=existing,
            scoring_direction=competition.scoring_direction,
            visibility_type=visibility_type,
        ):
            best_by_user[row.submission.user_id] = row

    ranked_rows = sorted(
        best_by_user.values(),
        key=lambda row: _ranking_key(
            row=row,
            scoring_direction=competition.scoring_direction,
            visibility_type=visibility_type,
        ),
    )

    db.execute(
        delete(LeaderboardEntry)
        .where(LeaderboardEntry.competition_id == competition.id)
        .where(LeaderboardEntry.phase_id == phase_id)
        .where(LeaderboardEntry.visibility_type == visibility_type)
    )

    entries: list[LeaderboardEntry] = []
    for rank, row in enumerate(ranked_rows, start=1):
        entry = LeaderboardEntry(
            competition_id=competition.id,
            phase_id=phase_id,
            user_id=row.submission.user_id,
            best_submission_id=row.submission.id,
            score_value=_score_for_visibility(row.score, visibility_type),
            rank=rank,
            visibility_type=visibility_type,
        )
        db.add(entry)
        entries.append(entry)

    db.flush()
    return entries


def _is_better(
    *,
    candidate: SubmissionScoreRow,
    current: SubmissionScoreRow,
    scoring_direction: str,
    visibility_type: str,
) -> bool:
    candidate_score = _score_for_visibility(candidate.score, visibility_type)
    current_score = _score_for_visibility(current.score, visibility_type)

    if candidate_score == current_score:
        if candidate.submission.created_at == current.submission.created_at:
            return candidate.submission.id < current.submission.id
        return cast(bool, candidate.submission.created_at < current.submission.created_at)

    if scoring_direction == ScoringDirection.MIN.value:
        return candidate_score < current_score

    return candidate_score > current_score


def _ranking_key(
    *,
    row: SubmissionScoreRow,
    scoring_direction: str,
    visibility_type: str,
) -> tuple[float, object, str]:
    score = _score_for_visibility(row.score, visibility_type)
    sortable_score = score if scoring_direction == ScoringDirection.MIN.value else -score
    return sortable_score, row.submission.created_at, row.submission.id


def _score_for_visibility(score: Score, visibility_type: str) -> float:
    if visibility_type == "private":
        return score.private_score_value
    return score.public_score_value
