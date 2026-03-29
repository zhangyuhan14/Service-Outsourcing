from datetime import date
from typing import Optional, List

import os
import shutil

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Request
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..utils import (
    generate_filename,
    build_ocr_text,
    normalize_defect_type,
    load_config,
    save_config
)

router = APIRouter()

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================
# 工具函数：前端字段适配
# =========================
def build_image_url(request: Request, image_path: str) -> str:
    if not image_path:
        return ""

    if image_path.startswith("http://") or image_path.startswith("https://"):
        return image_path

    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/{image_path.lstrip('/')}"


def pick_preset_model(record) -> str:
    """
    你当前数据库没有 presetModel 字段
    这里只能先做兼容映射
    优先用 batch_id，其次 device_id
    后续 ML / 配置完成后再替换成真实型号字段
    """
    return record.batch_id or record.device_id or "未配置"


def to_status(record) -> str:
    return "OK" if record.is_qualified else "NG"


def to_position_status(record) -> str:
    """
    当前位置状态数据库里也没有真实字段
    先临时返回“正常”
    后续嵌入式 / 视觉定位就绪后再换真实值
    """
    return "正常"


def format_current_record(record, request: Request):
    return {
        "status": to_status(record),
        "ocrText": build_ocr_text(record.energy_level),
        "presetModel": pick_preset_model(record),
        "isMatch": bool(record.is_qualified),   # 临时兼容
        "defectType": normalize_defect_type(record.defect_type),
        "positionStatus": to_position_status(record),
        "positionX": 0,   # 临时占位
        "positionY": 0,   # 临时占位
        "timestamp": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "imageUrl": build_image_url(request, record.image_path),
    }


def format_recent_record(record):
    return {
        "timestamp": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "presetModel": pick_preset_model(record),
        "ocrText": build_ocr_text(record.energy_level),
        "status": to_status(record),
        "defectType": normalize_defect_type(record.defect_type),
        "positionStatus": to_position_status(record),
    }


def format_history_record(record, request: Request):
    return {
        "timestamp": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "presetModel": pick_preset_model(record),
        "ocrText": build_ocr_text(record.energy_level),
        "status": to_status(record),
        "defectType": normalize_defect_type(record.defect_type),
        "positionStatus": to_position_status(record),
        "imageUrl": build_image_url(request, record.image_path),
    }


def format_statistics_record(record):
    defect_type = normalize_defect_type(record.defect_type)

    return {
        "timestamp": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "presetModel": pick_preset_model(record),
        "status": to_status(record),
        "hasDefect": defect_type != "无",
        "defectType": defect_type,
        "positionStatus": to_position_status(record),
    }


# =========================
# 你原有接口（保留，别动前面的联调）
# =========================
@router.post("/api/v1/detect/upload_image")
async def upload_image(file: UploadFile = File(...)):
    ALLOWED_EXT = {".jpg", ".jpeg", ".png"}
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {ext}")

    filename = generate_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "image_name": filename,
        "image_url": f"/static/uploads/{filename}"
    }


@router.post("/api/v1/detect/record", response_model=schemas.DetectionRecordOut)
def create_record(record: schemas.DetectionRecordCreate, db: Session = Depends(get_db)):
    return crud.create_detection_record(db, record)


@router.get("/api/v1/detect/history", response_model=schemas.HistoryResponse)
def get_legacy_history(
    page: int = 1,
    size: int = 10,
    device_id: str = None,
    batch_id: str = None,
    db: Session = Depends(get_db)
):
    skip = (page - 1) * size
    return crud.get_history_with_stats(db, skip, size, device_id, batch_id)


# =========================
# 前端新要求接口
# =========================

# 1. 获取当前检测结果
@router.get("/api/current", response_model=schemas.CurrentResultResponse)
def get_current(request: Request, db: Session = Depends(get_db)):
    record = crud.get_latest_record(db)
    if not record:
        raise HTTPException(status_code=404, detail="No detection record found")
    return format_current_record(record, request)


# 2. 获取最近10条记录
@router.get("/api/recent", response_model=List[schemas.RecentRecordResponse])
def get_recent(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    records = crud.get_recent_records(db, limit=limit)
    return [format_recent_record(r) for r in records]


# 3. 历史分页
@router.get("/api/history", response_model=schemas.FrontendHistoryResponse)
def get_history(
    request: Request,
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=100),
    startDate: Optional[date] = Query(None),
    endDate: Optional[date] = Query(None),
    statusFilter: str = Query("ALL"),
    db: Session = Depends(get_db)
):
    total, records = crud.get_frontend_history(
        db=db,
        page=page,
        page_size=pageSize,
        start_date=startDate,
        end_date=endDate,
        status_filter=statusFilter
    )

    return {
        "total": total,
        "records": [format_history_record(r, request) for r in records]
    }


# 4. 获取配置
@router.get("/api/config", response_model=schemas.ConfigResponse)
def get_config():
    return load_config()


# 5. 保存配置
@router.post("/api/config", response_model=schemas.SaveConfigResponse)
def post_config(config: schemas.ConfigResponse):
    save_config(config.model_dump())
    return {
        "success": True,
        "message": "配置保存成功"
    }


# 6. 获取统计数据
@router.get("/api/statistics", response_model=List[schemas.StatisticsItemResponse])
def get_statistics(
    startDate: Optional[date] = Query(None),
    endDate: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    records = crud.get_statistics_records(
        db=db,
        start_date=startDate,
        end_date=endDate
    )
    return [format_statistics_record(r) for r in records]