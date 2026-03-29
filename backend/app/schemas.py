from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any
from datetime import datetime


# =========================
# 原有检测记录模型
# =========================
class DetectionRecordBase(BaseModel):
    device_id: str
    batch_id: str
    image_path: str
    energy_level: float
    defect_type: str
    confidence: float
    is_qualified: bool


class DetectionRecordCreate(BaseModel):
    device_id: str
    batch_id: str
    image_path: str
    energy_level: float
    defect_type: str
    confidence: float


class DetectionRecordOut(DetectionRecordBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DetectionStatistics(BaseModel):
    total_scanned: int
    pass_count: int
    fail_count: int
    pass_rate: float


class HistoryResponse(BaseModel):
    stats: DetectionStatistics
    records: List[DetectionRecordOut]
    total: int


# =========================
# 前端兼容接口模型
# =========================
class CurrentResultResponse(BaseModel):
    status: str
    ocrText: str
    presetModel: str
    isMatch: bool
    defectType: str
    positionStatus: str
    positionX: int
    positionY: int
    timestamp: str
    imageUrl: str


class RecentRecordResponse(BaseModel):
    timestamp: str
    presetModel: str
    ocrText: str
    status: str
    defectType: str
    positionStatus: str


class HistoryRecordResponse(BaseModel):
    timestamp: str
    presetModel: str
    ocrText: str
    status: str
    defectType: str
    positionStatus: str
    imageUrl: str


class FrontendHistoryResponse(BaseModel):
    total: int
    records: List[HistoryRecordResponse]


class StatisticsItemResponse(BaseModel):
    timestamp: str
    presetModel: str
    status: str
    hasDefect: bool
    defectType: str
    positionStatus: str


class ConfigResponse(BaseModel):
    models: List[Dict[str, Any]]
    positionTolerance: int
    sensitivity: str
    lightCompensation: int
    camera: Dict[str, Any]


class SaveConfigResponse(BaseModel):
    success: bool
    message: str