import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Dict, Any
from ml_engine.active_learning import global_active_learning

router = APIRouter(prefix="/active-learning", tags=["Active Learning & Self-Improving MLOps"])

@router.get("/status")
def get_active_learning_status():
    """Mengambil status sampel koreksi dan status retraining otomatis."""
    return global_active_learning.get_status()

@router.post("/submit-correction")
async def submit_grader_correction(
    file: UploadFile = File(...),
    annotations_json: str = Form(...),
    operator_name: str = Form("Operator Grader PKS"),
    session_code: str = Form("")
):
    """
    Menerima koreksi bounding box / label dari grader,
    menyimpan ke dataset active learning dalam format standar YOLO.
    """
    try:
        annotations = json.loads(annotations_json)
    except Exception:
        raise HTTPException(status_code=400, detail="Format JSON anotasi tidak valid.")

    image_bytes = await file.read()
    res = global_active_learning.save_correction(
        image_bytes=image_bytes,
        annotations=annotations,
        operator_name=operator_name,
        session_code=session_code
    )
    return res

@router.post("/trigger-retrain")
def trigger_model_retrain(epochs: int = Form(10), batch_size: int = Form(8)):
    """Memulai proses background fine-tuning model."""
    res = global_active_learning.trigger_retraining(epochs=epochs, batch_size=batch_size)
    return res
