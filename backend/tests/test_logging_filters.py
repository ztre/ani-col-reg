import logging

from app.logging_filters import SuppressCoverNotModifiedAccessLogFilter


def make_access_record(method: str, path: str, status_code: int) -> logging.LogRecord:
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='%s - "%s %s HTTP/%s" %s',
        args=("127.0.0.1:12345", method, path, "1.1", status_code),
        exc_info=None,
    )


def test_cover_access_filter_suppresses_cover_304_requests() -> None:
    filter_ = SuppressCoverNotModifiedAccessLogFilter("/api/covers")

    assert not filter_.filter(make_access_record("GET", "/api/covers/example.webp", 304))
    assert not filter_.filter(make_access_record("HEAD", "/api/covers/example.webp?version=1", 304))


def test_cover_access_filter_keeps_other_access_logs() -> None:
    filter_ = SuppressCoverNotModifiedAccessLogFilter("/api/covers")

    assert filter_.filter(make_access_record("GET", "/api/covers/example.webp", 200))
    assert filter_.filter(make_access_record("GET", "/api/anime", 304))
    assert filter_.filter(make_access_record("POST", "/api/covers/example.webp", 304))