from packages.db.models import CompetitionPhase


def phase_accepts_submission(phase: CompetitionPhase) -> bool:
    return phase.submission_limit_per_day > 0
