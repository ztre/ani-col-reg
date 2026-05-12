import logging


def _normalize_cover_prefix(cover_public_path: str) -> str:
    prefix = cover_public_path.rstrip("/")
    if not prefix:
        return "/"
    return f"{prefix}/"


class SuppressCoverNotModifiedAccessLogFilter(logging.Filter):
    def __init__(self, cover_public_path: str = "/api/covers") -> None:
        super().__init__()
        self.cover_prefix = _normalize_cover_prefix(cover_public_path)

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if not isinstance(args, tuple) or len(args) != 5:
            return True

        _, method, full_path, _, status_code = args
        try:
            normalized_status = int(status_code)
        except (TypeError, ValueError):
            return True

        if normalized_status != 304 or method not in {"GET", "HEAD"}:
            return True

        request_path = str(full_path).split("?", 1)[0]
        return not request_path.startswith(self.cover_prefix)


def configure_uvicorn_access_log_filters(*, cover_public_path: str = "/api/covers") -> None:
    logger = logging.getLogger("uvicorn.access")
    cover_prefix = _normalize_cover_prefix(cover_public_path)

    for existing_filter in logger.filters:
        if isinstance(existing_filter, SuppressCoverNotModifiedAccessLogFilter) and existing_filter.cover_prefix == cover_prefix:
            return

    logger.addFilter(SuppressCoverNotModifiedAccessLogFilter(cover_public_path))