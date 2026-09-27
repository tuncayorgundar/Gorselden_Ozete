# Tuncay Bayır - 19.08.2026
import os

import requests
import torch
from ultralytics.nn.text_model import build_text_model

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "models")
DEFAULT_POOL_PATH = os.path.join(MODELS_DIR, "keyword_pool.pt")

DEFAULT_MAX_WORDS = 3
OBJECT_TEMPLATES = ["a photo of a {}", "a close-up photo of a {}", "{}"]

MOBILECLIP_WEIGHTS_NAME = "mobileclip2_b.ts"
MOBILECLIP_WEIGHTS_URL = (
    "https://github.com/ultralytics/assets/releases/download/v8.4.0/" + MOBILECLIP_WEIGHTS_NAME
)


def _ensure_mobileclip_weights():
    target_path = os.path.join(MODELS_DIR, MOBILECLIP_WEIGHTS_NAME)
    if os.path.exists(target_path):
        return

    response = requests.get(MOBILECLIP_WEIGHTS_URL, stream=True, timeout=60)
    response.raise_for_status()
    total_bytes = int(response.headers.get("content-length", 0))
    downloaded_bytes = 0

    print(f"Downloading MobileCLIP weights ({MOBILECLIP_WEIGHTS_NAME}, {total_bytes / 1e6:.0f} MB)...")
    with open(target_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
            downloaded_bytes += len(chunk)
            if total_bytes:
                percent = downloaded_bytes / total_bytes * 100
                print(f"\r  {percent:5.1f}%  ({downloaded_bytes / 1e6:.0f}/{total_bytes / 1e6:.0f} MB)", end="", flush=True)
    print()


class KeywordExtractor:
    def __init__(self, pool_path=DEFAULT_POOL_PATH, device=None):
        self._pool_path = pool_path
        self._device = device or torch.device("cpu")
        self._model = None
        self._pool = None
        self._pool_emb = None
        self._baseline = None

    @property
    def _loaded_model(self):
        if self._model is None:
            if not os.path.exists(self._pool_path):
                raise FileNotFoundError(
                    f"Keyword pool not found: {self._pool_path}. "
                    "Please place keyword_pool.pt at this location."
                )
            _ensure_mobileclip_weights()
            self._model = build_text_model("mobileclip2:b", device=self._device)

            cache = torch.load(self._pool_path, map_location=self._device)
            self._pool = cache["pool"]
            self._pool_emb = cache["pool_emb"]
            self._baseline = cache["baseline"]
        return self._model

    def tag(self, object_name, max_words=DEFAULT_MAX_WORDS, exclude=frozenset()):
        model = self._loaded_model

        object_embedding = self._embed_ensemble(model, [object_name], OBJECT_TEMPLATES)
        raw_scores = (object_embedding @ self._pool_emb.T).squeeze(0)

        calibrated_scores = raw_scores - self._baseline

        ranked_indices = calibrated_scores.argsort(descending=True).tolist()
        selected = []
        for i in ranked_indices:
            word = self._pool[i]
            if word in exclude:
                continue
            selected.append(word)
            if len(selected) >= max_words:
                break
        return selected

    @staticmethod
    def _embed_ensemble(model, texts, templates):
        accumulated = None
        for template in templates:
            prompts = [template.format(text) for text in texts]
            embedding = torch.nn.functional.normalize(model.encode_text(model.tokenize(prompts)), dim=-1)
            accumulated = embedding if accumulated is None else accumulated + embedding
        return torch.nn.functional.normalize(accumulated, dim=-1)
