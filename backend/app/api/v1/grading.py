from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import shutil
import uuid
from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.entities import (
    GradingSession, DetectionItem, OERAssessment, DeliveryOrder
)
from backend.app.schemas.schemas import (
    GradingPredictionResponse, GradingSessionCommit, GradingSessionResponse,
    BoundingBox, OERCalculationResult, CameraFramePredictionResponse
)
from backend.app.services.oer_calculator import OERCalculator
from ml_engine.inference import YOLOInferenceEngine

router = APIRouter(prefix="/grading", tags=["Grading & ML Inference"])

# Inisialisasi engine
from backend.app.services.certificate_generator import DigitalCertificateGenerator
from backend.app.services.rtsp_worker import global_rtsp_worker
from ml_engine.tracker import SpatialByteTracker
from fastapi.responses import Response

# Inisialisasi engine & tracker
model_to_use = settings.ONNX_MODEL_PATH if settings.INFERENCE_BACKEND == "onnx" and Path(settings.ONNX_MODEL_PATH).exists() else settings.DEFAULT_MODEL_PATH
inference_engine = YOLOInferenceEngine(
    model_path=model_to_use,
    conf_threshold=settings.CONFIDENCE_THRESHOLD,
    iou_threshold=settings.IOU_THRESHOLD
)
tripwire_tracker = SpatialByteTracker(tripwire_ratio=0.55)

@router.post("/tripwire/reset")
def reset_tripwire_counter():
    """Reset akumulasi hitungan garis virtual tripwire."""
    tripwire_tracker.reset_counter()
    return {"status": "success", "message": "Tripwire counter reset successfully", "counts": tripwire_tracker.counts}

@router.post("/predict", response_model=GradingPredictionResponse)
async def predict_grading(
    file: UploadFile = File(...),
    delivery_order_id: Optional[int] = Form(None),
    long_stalk_count: int = Form(0),
    dense_mode: bool = Form(False),
    db: Session = Depends(get_db)
):
    """
    Menerima citra TBS, melakukan inferensi YOLO/ONNX, menghitung estimasi OER & harga beli,
    dan mengembalikan bounding box serta visualisasi teranotasi.
    dense_mode=True mengaktifkan Slicing Aided Hyper Inference (SAHI) untuk tumpukan padat TBS.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File harus berformat citra (jpg/png)")

    # Buat session code unik
    session_id = uuid.uuid4().hex[:8].upper()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    session_code = f"GRD-{timestamp}-{session_id}"
    
    file_ext = Path(file.filename).suffix or ".jpg"
    orig_filename = f"{session_code}_orig{file_ext}"
    annotated_filename = f"{session_code}_annotated{file_ext}"
    
    orig_path = settings.UPLOAD_DIR / orig_filename
    annotated_path = settings.UPLOAD_DIR / annotated_filename

    try:
        # Simpan citra asli
        with open(orig_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Jalankan inferensi YOLO / ONNX (dengan opsi dense_mode SAHI)
        detections, latency_ms = inference_engine.predict(str(orig_path), dense_mode=dense_mode)

        # Gambar bounding box dan anotasi
        inference_engine.draw_annotations(str(orig_path), detections, str(annotated_path))

        # Agregasi hitungan kelas
        counts = {"unripe": 0, "underripe": 0, "ripe": 0, "overripe": 0, "empty_bunch": 0, "abnormal": 0, "long_stalk": int(long_stalk_count)}
        for item in detections:
            cls = item["class_name"]
            if cls in counts:
                counts[cls] += 1

        # Ambil bobot SPB jika delivery_order_id disediakan
        net_weight = None
        if delivery_order_id:
            order = db.query(DeliveryOrder).filter(DeliveryOrder.id == delivery_order_id).first()
            if order:
                net_weight = order.net_weight_kg

        # Hitung OER
        assessment = OERCalculator.calculate(counts=counts, net_weight_kg=net_weight, long_stalk_count=int(long_stalk_count))

        bbox_results = [
            BoundingBox(class_name=d["class_name"], confidence=d["confidence"], bbox=d["bbox"])
            for d in detections
        ]

        return GradingPredictionResponse(
            session_code=session_code,
            inference_latency_ms=latency_ms,
            image_url=f"/uploads/{orig_filename}",
            annotated_image_url=f"/uploads/{annotated_filename}",
            detections=bbox_results,
            assessment=assessment
        )
    except Exception as e:
        import traceback
        err_msg = f"Grading prediction error: {str(e)}\n{traceback.format_exc()}"
        print(err_msg)
        raise HTTPException(status_code=500, detail=err_msg)

@router.post("/predict-frame", response_model=CameraFramePredictionResponse)
async def predict_camera_frame(
    file: UploadFile = File(...),
    allow_demo_fallback: bool = Form(False),
    use_tripwire: bool = Form(True)
):
    """
    Endpoint inferensi berkecepatan tinggi untuk streaming frame kamera realtime
    dengan integrasi Spatial ByteTrack & Virtual Tripwire Counter.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Frame harus berformat citra")

    frame_bytes = await file.read()
    frame_res = inference_engine.predict_frame(frame_bytes, allow_fallback=allow_demo_fallback)

    detections = frame_res["detections"]
    latency_ms = frame_res["latency_ms"]
    width = frame_res["width"]
    height = frame_res["height"]

    tripwire_y = None
    cumulative_counted = None

    if use_tripwire:
        track_res = tripwire_tracker.update(detections, frame_height=height)
        tripwire_y = track_res["tripwire_y"]
        cumulative_counted = track_res["counts"]["total_counted"]

    counts = {"unripe": 0, "underripe": 0, "ripe": 0, "overripe": 0, "empty_bunch": 0, "abnormal": 0}
    for item in detections:
        cls = item["class_name"]
        if cls in counts:
            counts[cls] += 1

    assessment = OERCalculator.calculate(counts=counts)

    bbox_results = [
        BoundingBox(class_name=d["class_name"], confidence=d["confidence"], bbox=d["bbox"])
        for d in detections
    ]

    return CameraFramePredictionResponse(
        total_bunches=assessment.total_bunches,
        unripe_count=assessment.unripe_count,
        underripe_count=assessment.underripe_count,
        ripe_count=assessment.ripe_count,
        overripe_count=assessment.overripe_count,
        empty_bunch_count=assessment.empty_bunch_count,
        abnormal_count=assessment.abnormal_count,
        long_stalk_count=assessment.long_stalk_count,
        unripe_percentage=assessment.unripe_percentage,
        underripe_percentage=assessment.underripe_percentage,
        ripe_percentage=assessment.ripe_percentage,
        overripe_percentage=assessment.overripe_percentage,
        empty_bunch_percentage=assessment.empty_bunch_percentage,
        abnormal_percentage=assessment.abnormal_percentage,
        long_stalk_percentage=assessment.long_stalk_percentage,
        estimated_oer_percentage=assessment.estimated_oer_percentage,
        quality_score=assessment.quality_score,
        ffa_risk_category=assessment.ffa_risk_category,
        inference_latency_ms=latency_ms,
        frame_width=width,
        frame_height=height,
        detections=bbox_results,
        tripwire_y=tripwire_y,
        cumulative_counted=cumulative_counted
    )

@router.post("/commit", response_model=GradingSessionResponse)
def commit_grading_session(
    payload: GradingSessionCommit,
    db: Session = Depends(get_db)
):
    """
    Menyimpan hasil grading secara permanen ke database relasional
    dan mengaitkannya dengan tiket SPB.
    """
    orig_filename = f"{payload.session_code}_orig.jpg"
    annotated_filename = f"{payload.session_code}_annotated.jpg"
    
    # Cek apakah session code sudah ada
    existing = db.query(GradingSession).filter(GradingSession.session_code == payload.session_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Sesi grading ini sudah tersimpan")

    # Ambil SPB jika ada
    net_weight = None
    if payload.delivery_order_id:
        order = db.query(DeliveryOrder).filter(DeliveryOrder.id == payload.delivery_order_id).first()
        if order:
            net_weight = order.net_weight_kg
            order.status = "GRADED"

    orig_path = settings.UPLOAD_DIR / orig_filename
    if not orig_path.exists():
        candidates = list(settings.UPLOAD_DIR.glob(f"{payload.session_code}_orig.*"))
        if candidates:
            orig_path = candidates[0]
            annotated_candidates = list(settings.UPLOAD_DIR.glob(f"{payload.session_code}_annotated.*"))
            annotated_path = annotated_candidates[0] if annotated_candidates else orig_path
        else:
            orig_path = Path(f"/uploads/{orig_filename}")
            annotated_path = Path(f"/uploads/{annotated_filename}")
    else:
        annotated_path = settings.UPLOAD_DIR / annotated_filename

    # Jalankan re-evaluasi cepat untuk hitungan
    detections, latency = inference_engine.predict(str(orig_path))
    counts = {"unripe": 0, "underripe": 0, "ripe": 0, "overripe": 0}
    for item in detections:
        counts[item["class_name"]] = counts.get(item["class_name"], 0) + 1

    assessment_res = OERCalculator.calculate(counts=counts, net_weight_kg=net_weight)

    # Buat GradingSession
    session_obj = GradingSession(
        session_code=payload.session_code,
        delivery_order_id=payload.delivery_order_id,
        operator_name=payload.operator_name,
        image_path=str(orig_path.name),
        annotated_image_path=str(annotated_path.name),
        total_bunches=assessment_res.total_bunches,
        count_unripe=assessment_res.unripe_count,
        count_underripe=assessment_res.underripe_count,
        count_ripe=assessment_res.ripe_count,
        count_overripe=assessment_res.overripe_count,
        count_long_stalk=assessment_res.long_stalk_count,
        inference_latency_ms=latency,
        model_version="YOLOv8-ONNX-IOPRI",
        notes=payload.notes
    )
    db.add(session_obj)
    db.flush()

    # Simpan Bounding Boxes
    for item in detections:
        det = DetectionItem(
            grading_session_id=session_obj.id,
            class_name=item["class_name"],
            confidence=item["confidence"],
            bbox_x1=item["bbox"][0],
            bbox_y1=item["bbox"][1],
            bbox_x2=item["bbox"][2],
            bbox_y2=item["bbox"][3]
        )
        db.add(det)

    # Simpan OER Assessment
    oer_obj = OERAssessment(
        grading_session_id=session_obj.id,
        estimated_oer_percentage=assessment_res.estimated_oer_percentage,
        baseline_oer_percentage=assessment_res.baseline_oer_percentage,
        oer_variance=assessment_res.oer_variance,
        quality_score=assessment_res.quality_score,
        price_per_kg_base=assessment_res.price_per_kg_base,
        price_penalty_percentage=assessment_res.price_penalty_percentage,
        stalk_penalty_percentage=assessment_res.stalk_penalty_percentage,
        effective_net_weight_kg=assessment_res.effective_net_weight_kg,
        final_price_per_kg=assessment_res.final_price_per_kg,
        total_payout=assessment_res.total_payout or 0.0,
        ffa_risk_category=assessment_res.ffa_risk_category
    )
    db.add(oer_obj)
    db.commit()
    db.refresh(session_obj)

    return GradingSessionResponse(
        id=session_obj.id,
        session_code=session_obj.session_code,
        operator_name=session_obj.operator_name,
        delivery_order_id=session_obj.delivery_order_id,
        image_path=f"/uploads/{session_obj.image_path}",
        annotated_image_path=f"/uploads/{session_obj.annotated_image_path}",
        total_bunches=session_obj.total_bunches,
        count_unripe=session_obj.count_unripe,
        count_underripe=session_obj.count_underripe,
        count_ripe=session_obj.count_ripe,
        count_overripe=session_obj.count_overripe,
        count_long_stalk=session_obj.count_long_stalk,
        inference_latency_ms=session_obj.inference_latency_ms,
        model_version=session_obj.model_version,
        graded_at=session_obj.graded_at,
        assessment=assessment_res
    )

@router.get("/sessions/{session_id}/pdf")
def download_grading_certificate_pdf(session_id: int, db: Session = Depends(get_db)):
    """
    Menghasilkan dan mengunduh sertifikat digital mutu TBS resmi berformat PDF
    dengan QR-Code verifikasi kepatuhan EUDR/ISPO.
    """
    s = db.query(GradingSession).filter(GradingSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Sesi grading tidak ditemukan")

    counts = {
        "unripe": s.count_unripe,
        "underripe": s.count_underripe,
        "ripe": s.count_ripe,
        "overripe": s.count_overripe,
        "long_stalk": s.count_long_stalk
    }
    net_wt = s.delivery_order.net_weight_kg if s.delivery_order else 5000.0
    assessment_res = OERCalculator.calculate(counts=counts, net_weight_kg=net_wt, long_stalk_count=s.count_long_stalk)

    session_data = {
        "session_code": s.session_code,
        "operator_name": s.operator_name,
        "model_version": s.model_version,
        "total_bunches": s.total_bunches,
        "graded_at": s.graded_at.strftime("%d-%m-%Y %H:%M:%S WIB"),
        "assessment": assessment_res.model_dump()
    }

    farmer_data = {
        "name": s.delivery_order.farmer.name if s.delivery_order and s.delivery_order.farmer else "Pekebun Swadaya Binaan PCWE",
        "farmer_code": s.delivery_order.farmer.farmer_code if s.delivery_order and s.delivery_order.farmer else "FMR-PCWE-001",
        "certification_status": s.delivery_order.farmer.certification_status if s.delivery_order and s.delivery_order.farmer else "ISPO"
    }

    block_data = {
        "block_code": s.delivery_order.block.block_code if s.delivery_order and s.delivery_order.block else "BLK-PCWE-01",
        "legal_status": s.delivery_order.block.legal_status if s.delivery_order and s.delivery_order.block else "SHM",
        "latitude": s.delivery_order.block.latitude if s.delivery_order and s.delivery_order.block else 0.5386,
        "longitude": s.delivery_order.block.longitude if s.delivery_order and s.delivery_order.block else 101.4485,
        "area_hectares": s.delivery_order.block.area_hectares if s.delivery_order and s.delivery_order.block else 4.5,
        "variety": s.delivery_order.block.variety if s.delivery_order and s.delivery_order.block else "DxP",
        "eudr_compliant": s.delivery_order.block.eudr_compliant if s.delivery_order and s.delivery_order.block else "VERIFIED"
    }

    order_data = {
        "spb_number": s.delivery_order.spb_number if s.delivery_order else "SPB-DIRECT-SAMPLE",
        "truck_plate_number": s.delivery_order.truck_plate_number if s.delivery_order else "BM 8421 AU",
        "net_weight_kg": net_wt
    }

    pdf_bytes = DigitalCertificateGenerator.generate_pdf(session_data, farmer_data, block_data, order_data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="Certificate_{s.session_code}.pdf"'
        }
    )

@router.post("/rtsp/connect")
def connect_rtsp_stream(rtsp_url: str = Form(...)):
    """Menghubungkan background worker ke kamera IP / CCTV loading ramp PKS."""
    global_rtsp_worker.connect(rtsp_url)
    return {"status": "connected", "rtsp_url": rtsp_url}

@router.post("/rtsp/disconnect")
def disconnect_rtsp_stream():
    """Memutuskan koneksi feed RTSP."""
    global_rtsp_worker.disconnect()
    return {"status": "disconnected"}

@router.get("/rtsp/live-frame")
def get_rtsp_live_frame():
    """Mengambil frame terkini dari kamera IP industrial."""
    jpeg_bytes = global_rtsp_worker.get_latest_frame_jpeg()
    if not jpeg_bytes:
        raise HTTPException(status_code=503, detail="RTSP stream belum terhubung atau tidak ada frame")
    return Response(content=jpeg_bytes, media_type="image/jpeg")

@router.get("/sessions", response_model=List[GradingSessionResponse])
def get_grading_sessions(limit: int = 50, db: Session = Depends(get_db)):
    sessions = db.query(GradingSession).order_by(GradingSession.graded_at.desc()).limit(limit).all()
    results = []
    for s in sessions:
        counts = {
            "unripe": s.count_unripe,
            "underripe": s.count_underripe,
            "ripe": s.count_ripe,
            "overripe": s.count_overripe,
            "long_stalk": s.count_long_stalk
        }
        net_wt = s.delivery_order.net_weight_kg if s.delivery_order else None
        assessment_res = OERCalculator.calculate(counts=counts, net_weight_kg=net_wt, long_stalk_count=s.count_long_stalk)
        results.append(GradingSessionResponse(
            id=s.id,
            session_code=s.session_code,
            operator_name=s.operator_name,
            delivery_order_id=s.delivery_order_id,
            image_path=f"/uploads/{s.image_path}" if s.image_path else None,
            annotated_image_path=f"/uploads/{s.annotated_image_path}" if s.annotated_image_path else None,
            total_bunches=s.total_bunches,
            count_unripe=s.count_unripe,
            count_underripe=s.count_underripe,
            count_ripe=s.count_ripe,
            count_overripe=s.count_overripe,
            count_long_stalk=s.count_long_stalk,
            inference_latency_ms=s.inference_latency_ms,
            model_version=s.model_version,
            graded_at=s.graded_at,
            assessment=assessment_res
        ))
    return results
