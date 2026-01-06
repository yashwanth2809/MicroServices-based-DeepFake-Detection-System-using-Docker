import cv2
import torch
import httpx
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .model_loader import load_face_detector
from .utils import save_upload_file, extract_audio

app = FastAPI(title="Face Detection & Media Routing Service")

# Configure CORS
auth_origins = ["*"]  # adjust as needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=auth_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
FRONTEND_DIR = Path("/app/frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
app.mount("/static/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_ui():
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found")
    return index_file.read_text()

# Initialize face detector
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
detector = load_face_detector(device)

# Ensure upload directory exists
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Downstream service URLs
IMAGE_SERVICE_URL = "http://image_service:8001/predict_image"
VIDEO_SERVICE_URL = "http://video_service:8002/predict_video"
AUDIO_SERVICE_URL = "http://audio_service:8003/predict_audio"

@app.post("/predict_all")
async def predict_all(file: UploadFile = File(...)):
    # Log incoming file details
    ctype = file.content_type or ""
    ext = Path(file.filename).suffix.lower()
    print(f"[DEBUG] Received: {file.filename}, content_type={ctype}, ext={ext}")

    # Save file locally
    save_path = UPLOAD_DIR / file.filename
    save_upload_file(file, save_path)

    # Determine file type
    if ctype.startswith("image/"):
        ftype = "image"
    elif ctype.startswith("video/"):
        ftype = "video"
    elif ctype.startswith("audio/") or ext in {".wav", ".mp3", ".flac"}:
        ftype = "audio"
    else:
        raise HTTPException(status_code=415, detail=f"Unsupported media type: {ctype}, ext: {ext}")

    # Face detection for image/video
    if ftype in {"image", "video"}:
        if ftype == "image":
            img = cv2.imread(str(save_path))
            if img is None:
                raise HTTPException(status_code=400, detail="Cannot read image.")
        else:
            cap = cv2.VideoCapture(str(save_path))
            ret, img = cap.read()
            cap.release()
            if not ret or img is None:
                raise HTTPException(status_code=400, detail="Cannot extract video frame.")
        boxes = detector.detect(img)
        boxes = boxes[0] if isinstance(boxes, tuple) else boxes
        if len(boxes) == 0:
            raise HTTPException(status_code=400, detail="No face detected.")

    # Forward to appropriate service(s)
    async with httpx.AsyncClient() as client:
        # Handle image
        if ftype == "image":
            files = {"file": (save_path.name, save_path.open("rb"), ctype)}
            resp = await client.post(IMAGE_SERVICE_URL, files=files)
            resp.raise_for_status()
            return {"file_type": ftype, "prediction": resp.json()}

        # Handle audio only
        if ftype == "audio":
            files = {"file": (save_path.name, save_path.open("rb"), ctype or "audio/wav")}
            resp = await client.post(AUDIO_SERVICE_URL, files=files)
            resp.raise_for_status()
            return {"file_type": ftype, "prediction": resp.json()}

        # Handle video
        # 1) Video prediction
        files = {"file": (save_path.name, save_path.open("rb"), ctype)}
        video_resp = await client.post(VIDEO_SERVICE_URL, files=files)
        video_resp.raise_for_status()
        video_pred = video_resp.json()

        # 2) Extract audio and predict
        audio_pred = None
        audio_path = UPLOAD_DIR / (save_path.stem + ".wav")
        extracted = extract_audio(str(save_path), str(audio_path))
        print(f"[DEBUG] Audio extracted: {extracted}")
        if extracted:
            files_audio = {"file": (audio_path.name, audio_path.open("rb"), "audio/wav")}
            audio_raw = (await client.post(AUDIO_SERVICE_URL, files=files_audio)).json()
            # Normalize audio_pred to common schema
            audio_pred = {
                "prediction": audio_raw.get("label", audio_raw.get("prediction")),
                "confidence": audio_raw.get("confidence", audio_raw.get("score"))
            }
        else:
            audio_pred = None

        # Local ensemble (no aggregation_service)
        # majority or higher confidence
        if audio_pred:
            if video_pred["prediction"] == audio_pred["prediction"]:
                final = video_pred["prediction"]
            else:
                final = (
                    video_pred["prediction"]
                    if video_pred["confidence"] >= audio_pred["confidence"]
                    else audio_pred["prediction"]
                )
        else:
            final = video_pred["prediction"]

        return {
            "file_type": "video",
            "prediction": {
                "final": final,
                "video": video_pred,
                "audio": audio_pred,
            }
        }
