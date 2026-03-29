from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session

from . import models, schemas
from .utils import judge_qualified


def create_detection_record(db: Session, record: schemas.DetectionRecordCreate):
    db_record = models.DetectionRecord(
        device_id=record.device_id,
        batch_id=record.batch_id,
        image_path=record.image_path,
        energy_level=record.energy_level,
        defect_type=record.defect_type,
        confidence=record.confidence,
        is_qualified=judge_qualified(record.energy_level)
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


# =========================
# 原有接口：历史 + 统计
# =========================
def get_history_with_stats(db: Session, skip=0, limit=100, device_id=None, batch_id=None):
    query = db.query(models.DetectionRecord)

    if device_id:
        query = query.filter(models.DetectionRecord.device_id == device_id)
    if batch_id:
        query = query.filter(models.DetectionRecord.batch_id == batch_id)

    total = query.count()
    items = query.order_by(models.DetectionRecord.created_at.desc()).offset(skip).limit(limit).all()

    all_items = query.all()
    total_scanned = len(all_items)
    fail_count = sum(1 for item in all_items if item.is_qualified is False)
    pass_count = total_scanned - fail_count
    pass_rate = round(pass_count / total_scanned, 3) if total_scanned else 0.0

    return {
        "stats": {
            "total_scanned": total_scanned,
            "fail_count": fail_count,
            "pass_count": pass_count,
            "pass_rate": pass_rate
        },
        "records": items,
        "total": total
    }


# =========================
# 前端兼容接口：查询函数
# =========================
def get_latest_record(db: Session):
    return db.query(models.DetectionRecord).order_by(models.DetectionRecord.created_at.desc()).first()


def get_recent_records(db: Session, limit: int = 10):
    return (
        db.query(models.DetectionRecord)
        .order_by(models.DetectionRecord.created_at.desc())
        .limit(limit)
        .all()
    )


def build_filtered_query(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
    status_filter: str = "ALL"
):
    query = db.query(models.DetectionRecord)

    if start_date:
        start_dt = datetime.combine(start_date, time.min)
        query = query.filter(models.DetectionRecord.created_at >= start_dt)

    if end_date:
        # 结束日期按“当天 23:59:59”算，最简单是 < 次日 00:00:00
        end_dt = datetime.combine(end_date + timedelta(days=1), time.min)
        query = query.filter(models.DetectionRecord.created_at < end_dt)

    status_filter = (status_filter or "ALL").upper()

    if status_filter == "OK":
        query = query.filter(models.DetectionRecord.is_qualified.is_(True))
    elif status_filter == "NG":
        query = query.filter(models.DetectionRecord.is_qualified.is_(False))

    return query


def get_frontend_history(
    db: Session,
    page: int = 1,
    page_size: int = 25,
    start_date: date | None = None,
    end_date: date | None = None,
    status_filter: str = "ALL"
):
    query = build_filtered_query(db, start_date, end_date, status_filter)

    total = query.count()
    records = (
        query.order_by(models.DetectionRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return total, records


def get_statistics_records(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None
):
    query = build_filtered_query(db, start_date, end_date, "ALL")

    return (
        query.order_by(models.DetectionRecord.created_at.asc())
        .all()
    )