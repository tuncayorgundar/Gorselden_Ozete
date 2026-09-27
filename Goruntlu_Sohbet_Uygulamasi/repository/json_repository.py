# Tuncay Bayır - 21.08.2026
from datetime import datetime
import json
import os

DEFAULT_FILE_PATH = "data/detection_records.jsonl"
DECIMAL_PLACES = 4


class JsonRepository:
    def __init__(self, file_path=DEFAULT_FILE_PATH):
        self.file_path = file_path

    def save(self, detections, source):
        record = {"detections": [_sanitize(detection) for detection in detections]}

        directory = os.path.dirname(self.file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(self.file_path, "a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _sanitize(detection):
    sanitized = {
        "timestamp": datetime.now().date().isoformat(),
        "class_name": detection["class_name"],
        "confidence": round(detection["confidence"], DECIMAL_PLACES),
    }

    if "score" in detection:
        sanitized["score"] = round(detection["score"], DECIMAL_PLACES)
    if "keywords" in detection:
        sanitized["keywords"] = detection["keywords"]
    if "summary" in detection:
        sanitized["summary"] = detection["summary"]

    return sanitized
