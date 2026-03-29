import uuid
import os
import json
from copy import deepcopy

REQUIRED_ENERGY_LEVEL = 1.0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config_store.json")

DEFAULT_CONFIG = {
    "models": [
        {
            "name": "冰箱",
            "model": "BCD-520W",
            "standardLabel": "A++",
            "enabled": True
        }
    ],
    "positionTolerance": 10,
    "sensitivity": "中",
    "lightCompensation": 0,
    "camera": {
        "exposure": 0,
        "resolution": "1280x720"
    }
}


def generate_filename(filename: str) -> str:
    ext = os.path.splitext(filename)[1]
    return f"{uuid.uuid4().hex}{ext}"


def judge_qualified(energy_level: float) -> bool:
    # 你原来这里是 <= 1.0 判合格，我先保留你的逻辑
    return energy_level <= REQUIRED_ENERGY_LEVEL


def normalize_defect_type(defect_type: str) -> str:
    if defect_type is None:
        return "无"

    value = str(defect_type).strip().lower()
    if value in {"", "none", "normal", "ok", "无", "正常"}:
        return "无"

    return defect_type


def build_ocr_text(energy_level: float) -> str:
    """
    临时兼容：
    现在没有真实 OCR 文本，就先用 energy_level 映射成 “x级能效”
    后续 ML 接入后再换成真实 OCR 结果
    """
    try:
        val = float(energy_level)
        if val.is_integer():
            return f"{int(val)}级能效"
        return f"{val}级能效"
    except Exception:
        return "未知"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return deepcopy(DEFAULT_CONFIG)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)