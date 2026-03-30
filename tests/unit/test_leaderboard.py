from packages.db.models import Submission
from packages.leaderboard.service import upsert_leaderboard_entry


class FakeSession:
    def __init__(self) -> None:
        self.entry = None

    def scalar(self, _query):
        return self.entry

    def add(self, entry) -> None:
        self.entry = entry

    def flush(self) -> None:
        return None


def test_upsert_leaderboard_entry_creates_entry() -> None:
    db = FakeSession()
    submission = Submission(
        competition_id="competition-1",
        phase_id="phase-1",
        user_id="user-1",
        submission_type="file",
        source_archive_path="source.zip",
        manifest_path="manifest.json",
        status="completed",
    )
    submission.id = "submission-1"

    entry = upsert_leaderboard_entry(
        db,
        submission=submission,
        score_value=99.0,
        visibility_type="public",
    )

    assert entry.best_submission_id == "submission-1"
    assert entry.score_value == 99.0
