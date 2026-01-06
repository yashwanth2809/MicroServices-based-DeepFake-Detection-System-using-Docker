import ffmpeg
from pathlib import Path
from fastapi import UploadFile

def save_upload_file(upload_file: UploadFile, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as buffer:
        buffer.write(upload_file.file.read())

def extract_audio(video_path: str, output_path: str) -> bool:
    """
    Returns True if audio was extracted, False if
    no audio stream or extraction failed.
    """
    try:
        # Probe for audio stream
        probe = ffmpeg.probe(video_path)
        streams = probe.get("streams", [])
        has_audio = any(s.get("codec_type") == "audio" for s in streams)
        if not has_audio:
            return False

        # Extract audio
        (
            ffmpeg
            .input(video_path)
            .output(output_path, vn=None, acodec="pcm_s16le", ac=1, ar="16k")
            .overwrite_output()
            .run(quiet=True)
        )
        return True

    except ffmpeg.Error:
        # Skip on any ffmpeg error
        return False
