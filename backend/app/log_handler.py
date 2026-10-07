import logging
import threading


class DBLogHandler(logging.Handler):
    """将应用日志写入 app_log 表的 logging.Handler。

    使用独立 SessionLocal，不依赖 FastAPI 请求上下文；用 _writing 标志防止
    DB 操作本身产生的日志无限递归写入。
    """

    def __init__(self, level: int = logging.NOTSET) -> None:
        super().__init__(level)
        self._local = threading.local()

    def emit(self, record: logging.LogRecord) -> None:
        # 防止递归：若当前线程已在写入则跳过
        if getattr(self._local, "writing", False):
            return
        self._local.writing = True
        try:
            self._write(record)
        except Exception:  # noqa: BLE001
            self.handleError(record)
        finally:
            self._local.writing = False

    def _write(self, record: logging.LogRecord) -> None:
        from app.database import SessionLocal
        from app.models import AppLog

        message = self.format(record)
        log_entry = AppLog(
            level=record.levelname,
            source=record.name,
            message=message,
        )
        with SessionLocal() as session:
            session.add(log_entry)
            session.commit()


def register_db_log_handler(logger_name: str = "app", level: int = logging.INFO) -> None:
    """注册 DBLogHandler 到指定 logger，幂等（避免重复注册）。"""
    logger = logging.getLogger(logger_name)
    for handler in logger.handlers:
        if isinstance(handler, DBLogHandler):
            return
    handler = DBLogHandler(level)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
