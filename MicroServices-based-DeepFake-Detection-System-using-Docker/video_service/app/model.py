import cv2
import numpy as np
from PIL import Image
from transformers import pipeline
from threading import Lock

class VideoDeepFakeModel:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(VideoDeepFakeModel, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = "prithivMLmods/Deep-Fake-Detector-Model", sample_fps: int = 1):
        if not hasattr(self, 'pipeline'):
            self.pipeline = pipeline("image-classification", model=model_name)
            self.sample_fps = sample_fps

    def predict(self, video_path: str):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or self.sample_fps
        interval = max(1, int(fps / self.sample_fps))

        frame_idx = 0
        fake_scores = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % interval == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb)
                out = self.pipeline(pil_img, top_k=1)[0]
                score = out['score']
                label = out['label'].lower()
                fake_prob = score if label == 'fake' else 1.0 - score
                fake_scores.append(fake_prob)
            frame_idx += 1

        cap.release()

        if not fake_scores:
            raise RuntimeError("No frames extracted from video for prediction.")

        avg_fake = float(np.mean(fake_scores))
        prediction = "FAKE" if avg_fake > 0.5 else "REAL"
        confidence = avg_fake if prediction == "FAKE" else 1.0 - avg_fake

        return {
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "frames_evaluated": len(fake_scores)
        }