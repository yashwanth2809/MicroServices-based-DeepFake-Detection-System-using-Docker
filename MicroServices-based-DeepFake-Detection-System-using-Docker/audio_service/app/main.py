import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.model import AudioDeepFakeModel

app = FastAPI(
    title="Audio Deepfake Detection Service",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs"
)

# Ensure upload directory exists
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize model at startup
model = AudioDeepFakeModel()

@app.post("/predict_audio")
async def predict_audio(file: UploadFile = File(...)):
    # Validate file type
    if not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=415, detail="Unsupported media type. Please upload an audio file.")

    # Save upload
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, 'wb') as f:
        f.write(await file.read())

    # Run prediction
    try:
        result = model.predict(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {e}")

    return JSONResponse(content=result)

# Health check
@app.get("/healthz")
async def health():
    return {"status": "ok"}