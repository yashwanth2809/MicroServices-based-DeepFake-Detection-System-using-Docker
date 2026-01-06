import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.model import VideoDeepFakeModel

app = FastAPI(
    title="Video Deepfake Detection Service",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs"
)

# Ensure upload directory exists
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize model at startup
model = VideoDeepFakeModel()

@app.post("/predict_video")
async def predict_video(file: UploadFile = File(...)):
    # Validate file type
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=415, detail="Unsupported media type. Please upload a video.")

    # Save upload
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, 'wb') as f:
        f.write(await file.read())

    # Run prediction
    try:
        result = model.predict(file_path)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {e}")

    return JSONResponse(content=result)

# Health check
@app.get("/healthz")
async def health():
    return {"status": "ok"}