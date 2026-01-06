from transformers import pipeline
from threading import Lock

class AudioDeepFakeModel:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(AudioDeepFakeModel, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = "mo-thecreator/Deepfake-audio-detection"):
        if not hasattr(self, 'pipeline'):
            # Load the HuggingFace audio classification pipeline
            self.pipeline = pipeline("audio-classification", model=model_name)

    def predict(self, audio_path: str):
        # Run inference
        raw = self.pipeline(audio_path, top_k=1)[0]
        # Invert label mapping: model id2label {0: "fake", 1: "real"}, semantics reversed
        label = "fake" if raw["label"] == "real" else "real"
        confidence = float(raw["score"])
        return {
            "label": label.upper(),
            "confidence": confidence
        }