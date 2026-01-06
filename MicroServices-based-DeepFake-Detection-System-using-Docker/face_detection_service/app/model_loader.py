import torch
from pathlib import Path
from face_detection import build_detector

# Absolute path inside the container where your model is mounted
LOCAL_CHECKPOINT = Path("/shared/models/WIDERFace_DSFD_RES152.pth")

def load_face_detector(device):
    """
    Build the DSFD detector but override torch.hub's URL loader
    so it pulls from our local checkpoint instead of hitting the internet.
    """
    # --- Monkey-patch Torch Hub downloader ---
    original_loader = torch.hub.load_state_dict_from_url

    def local_loader(url, *args, **kwargs):
        # ignore URL, load local file
        return torch.load(str(LOCAL_CHECKPOINT), map_location=device)

    torch.hub.load_state_dict_from_url = local_loader

    # --- Build the detector as usual ---
    detector = build_detector(
        name='DSFDDetector',
        confidence_threshold=0.5,
        nms_iou_threshold=0.3,
        device=device
    )

    # --- Restore the original loader in case others need it ---
    torch.hub.load_state_dict_from_url = original_loader

    return detector
