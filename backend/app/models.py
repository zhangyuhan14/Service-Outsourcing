from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime
from .database import Base

class DetectionRecord(Base):
    __tablename__ = "detection_records"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), nullable=False, index=True)
    batch_id = Column(String(64), nullable=False, index=True)
    image_path = Column(String(255), nullable=False)
    energy_level = Column(Float, nullable=False)
    defect_type = Column(String(64), nullable=False)
    confidence = Column(Float, nullable=False)
    is_qualified = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)