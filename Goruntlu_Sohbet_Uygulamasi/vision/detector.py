# Tuncay Bayır - 19.08.2026
import json
import os

from ultralytics import YOLOE
from ultralytics import settings as ultralytics_settings

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "models")

DEFAULT_MODEL_PATH = os.path.join(MODELS_DIR, "yoloe-26l-seg.pt")
DEFAULT_NAMES_PATH = os.path.join(os.path.dirname(MODELS_DIR), "lvis_synsets.json")
DEFAULT_PROMPT_CACHE_PATH = os.path.join(MODELS_DIR, "lvis1203_prompts.npz")

DEFAULT_CONFIDENCE_THRESHOLD = 0.5
DEFAULT_LOW_CONFIDENCE_THRESHOLD = 0.3
DEFAULT_UNCERTAIN_GUESS_COUNT = 3


ultralytics_settings.update({"weights_dir": MODELS_DIR})


class ObjectDetector:
    def __init__(self, model_path=DEFAULT_MODEL_PATH, names_path=DEFAULT_NAMES_PATH,
                 prompt_cache_path=DEFAULT_PROMPT_CACHE_PATH):
        self._model_path = model_path
        self._names_path = names_path
        self._prompt_cache_path = prompt_cache_path
        self._model = None
        self._lvis = None

    @property
    def model(self):
        if self._model is None:
            model = YOLOE(self._model_path)

            if os.path.exists(self._prompt_cache_path):
                model.load_prompt_embeddings(self._prompt_cache_path)
            else:
                model.set_classes(self._lvis_names())
                model.save_prompt_embeddings(self._prompt_cache_path)

            self._model = model
        return self._model

    def _lvis_names(self):
        return [entry["name"] for entry in self._lvis_data().values()]

    def _lvis_data(self):
        if self._lvis is None:
            if not os.path.exists(self._names_path):
                raise FileNotFoundError(
                    f"LVIS synset map not found: {self._names_path}."
                )
            with open(self._names_path, encoding="utf-8") as f:
                self._lvis = json.load(f)
        return self._lvis

    def detect(
        self,
        frame,
        confidence_threshold=DEFAULT_CONFIDENCE_THRESHOLD,
        low_confidence_threshold=DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    ):
        prediction = self.model(frame, verbose=False)[0]
        all_detections = [self._to_detection(box, prediction.names) for box in prediction.boxes]

        confident_detections = [d for d in all_detections if d["confidence"] >= confidence_threshold]
        if confident_detections:
            return {"confident": True, "detections": confident_detections}

        uncertain_guesses = sorted(
            (d for d in all_detections if d["confidence"] >= low_confidence_threshold),
            key=lambda d: d["confidence"],
            reverse=True,
        )[:DEFAULT_UNCERTAIN_GUESS_COUNT]

        return {"confident": False, "detections": uncertain_guesses}

    @staticmethod
    def _to_detection(box, class_names):
        return {
            "class_name": class_names[int(box.cls[0])],
            "confidence": float(box.conf[0]),
            "box": tuple(box.xyxy[0].tolist()),
        }
