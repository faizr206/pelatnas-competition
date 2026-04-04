from packages.storage.service import build_attachment_content_disposition


def test_build_attachment_content_disposition_sanitizes_filename() -> None:
    header = build_attachment_content_disposition('bad"\r\nname.csv')
    assert header == 'attachment; filename="badname.csv"'


def test_build_attachment_content_disposition_uses_fallback_for_empty_filename() -> None:
    header = build_attachment_content_disposition('"\r\n"', fallback="dataset.bin")
    assert header == 'attachment; filename="dataset.bin"'
