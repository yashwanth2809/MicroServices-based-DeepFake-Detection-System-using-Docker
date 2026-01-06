from transformers import pipeline
from threading import Lock

class DeepFakeImageModel:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(DeepFakeImageModel, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = "prithivMLmods/Deep-Fake-Detector-Model"):
        if not hasattr(self, 'pipeline'):
            # Load the HuggingFace pipeline once
            self.pipeline = pipeline("image-classification", model=model_name)

    def predict(self, image_path: str):
        # Run inference
        outputs = self.pipeline(image_path, top_k=1)
        result = outputs[0]
        return {
            "label": result["label"],
            "confidence": float(result["score"])
        }