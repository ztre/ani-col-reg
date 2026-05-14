from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CollectionItem
from app.routes.common import require_auth
from app.schemas import TagSummaryOut, TagUsageOut


router = APIRouter(prefix='/api', dependencies=[Depends(require_auth)])


@router.get('/tags', response_model=TagSummaryOut)
def list_tags(db: Session = Depends(get_db)) -> TagSummaryOut:
    release_counter: Counter[str] = Counter()
    group_counter: Counter[str] = Counter()

    for release_tags, group_tags in db.execute(select(CollectionItem.release_tags, CollectionItem.group_tags)).all():
        release_counter.update(release_tags or [])
        group_counter.update(group_tags or [])

    return TagSummaryOut(
        release=[TagUsageOut(value=value, count=count) for value, count in release_counter.most_common(30)],
        group=[TagUsageOut(value=value, count=count) for value, count in group_counter.most_common(30)],
    )