# Tuncay Bayır - 18.08.2026
import os

import cv2
import numpy as np
import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
TIMEOUT_SECONDS = 10


def get_source(source):
    if not source:
        raise ValueError("Source must not be empty.")

    if source.lower().startswith(("http://", "https://")):
        frame = _read_from_url(source)
    else:
        frame = _read_from_file(source)

    if frame is None:
        raise ValueError(f"Invalid or unsupported image format: {source}")

    return frame


def _read_from_url(url):
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
    except Exception as error:
        raise ConnectionError(f"Could not open source: {url} ({error})")

    image_bytes = np.frombuffer(response.content, dtype=np.uint8)
    return cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)


def _read_from_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    return cv2.imread(path, cv2.IMREAD_COLOR)
