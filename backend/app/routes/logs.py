from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AppLog
from app.routes.common import require_auth
from app.schemas import AppLogOut, PaginatedAppLogs

router = APIRouter(prefix="/api", dependencies=[Depends(require_auth)])


@router.get("/logs", response_model=PaginatedAppLogs)
def get_logs(
    level: str | None = Query(None, description="日志级别过滤，如 INFO、WARNING、ERROR"),
    source: str | None = Query(None, description="来源模块过滤，支持部分匹配"),
    limit: int = Query(200, ge=1, le=500, description="返回条数上限"),
    offset: int = Query(0, ge=0, description="分页偏移"),
    db: Session = Depends(get_db),
) -> PaginatedAppLogs:
    stmt = select(AppLog)
    count_stmt = select(func.count()).select_from(AppLog)

    if level:
        stmt = stmt.where(AppLog.level == level.upper())
        count_stmt = count_stmt.where(AppLog.level == level.upper())
    if source:
        stmt = stmt.where(AppLog.source.contains(source))
        count_stmt = count_stmt.where(AppLog.source.contains(source))

    total = db.execute(count_stmt).scalar_one()
    items = db.execute(stmt.order_by(AppLog.created_at.desc()).limit(limit).offset(offset)).scalars().all()

    return PaginatedAppLogs(items=list(items), total=total)
