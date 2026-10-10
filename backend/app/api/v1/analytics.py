from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from backend.app.core.database import get_db
from backend.app.models.entities import (
    GradingSession, DeliveryOrder, Farmer, PlantationBlock, OERAssessment
)

router = APIRouter(prefix="/analytics", tags=["Analytics & Traceability Audit"])

@router.get("/summary")
def get_factory_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Ringkasan performa grading pabrik kelapa sawit:
    Total truk, total TBS tergrading, rata-rata OER, persentase kematangan, dan total tonase.
    """
    total_sessions = db.query(GradingSession).count()
    total_orders = db.query(DeliveryOrder).count()
    
    total_bunches = db.query(func.sum(GradingSession.total_bunches)).scalar() or 0
    total_unripe = db.query(func.sum(GradingSession.count_unripe)).scalar() or 0
    total_underripe = db.query(func.sum(GradingSession.count_underripe)).scalar() or 0
    total_ripe = db.query(func.sum(GradingSession.count_ripe)).scalar() or 0
    total_overripe = db.query(func.sum(GradingSession.count_overripe)).scalar() or 0
    
    avg_oer = db.query(func.avg(OERAssessment.estimated_oer_percentage)).scalar() or 21.5
    avg_latency = db.query(func.avg(GradingSession.inference_latency_ms)).scalar() or 120.0
    total_tonnage = db.query(func.sum(DeliveryOrder.net_weight_kg)).scalar() or 0.0

    return {
        "total_grading_sessions": total_sessions,
        "total_delivery_trucks": total_orders,
        "total_net_weight_kg": round(total_tonnage, 2),
        "total_tbs_bunches": total_bunches,
        "average_oer_percentage": round(avg_oer, 2),
        "average_latency_ms": round(avg_latency, 1),
        "ripeness_breakdown": {
            "unripe": total_unripe,
            "underripe": total_underripe,
            "ripe": total_ripe,
            "overripe": total_overripe,
            "ripe_ratio": round((total_ripe / total_bunches * 100), 2) if total_bunches > 0 else 0.0
        }
    }

@router.get("/audit/{spb_number}")
def get_traceability_audit(spb_number: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Mengambil data audit ketertelusuran lengkap dari hulu (petani/blok kebun)
    ke hilir (grading, OER, dan harga pembayaran) untuk kepatuhan ISPO/RSPO/EUDR.
    """
    order = db.query(DeliveryOrder).filter(DeliveryOrder.spb_number == spb_number).first()
    if not order:
        raise HTTPException(status_code=404, detail="Nomor SPB tidak ditemukan dalam basis data")

    farmer = order.farmer
    block = order.block
    session = order.grading_session
    oer = session.oer_assessment if session else None

    return {
        "audit_ticket": {
            "spb_number": order.spb_number,
            "truck_plate_number": order.truck_plate_number,
            "driver_name": order.driver_name,
            "net_weight_kg": order.net_weight_kg,
            "arrival_time": order.arrival_time.isoformat(),
            "status": order.status
        },
        "traceability_origin": {
            "farmer_code": farmer.farmer_code if farmer else "-",
            "farmer_name": farmer.name if farmer else "-",
            "nik": farmer.nik if farmer else "-",
            "cooperative": farmer.cooperative_name if farmer else "-",
            "certification_status": farmer.certification_status if farmer else "NONE",
            "block_code": block.block_code if block else "-",
            "geolocation": {
                "latitude": block.latitude if block else 0.0,
                "longitude": block.longitude if block else 0.0
            },
            "planting_year": block.planting_year if block else None,
            "seed_variety": block.variety if block else "-",
            "legal_status": block.legal_status if block else "-"
        },
        "grading_evidence": {
            "session_code": session.session_code if session else None,
            "graded_at": session.graded_at.isoformat() if session else None,
            "total_bunches": session.total_bunches if session else 0,
            "ripeness": {
                "unripe": session.count_unripe if session else 0,
                "underripe": session.count_underripe if session else 0,
                "ripe": session.count_ripe if session else 0,
                "overripe": session.count_overripe if session else 0
            },
            "image_url": f"/uploads/{session.annotated_image_path}" if session and session.annotated_image_path else None
        },
        "oer_and_commercial": {
            "estimated_oer_percentage": oer.estimated_oer_percentage if oer else 0.0,
            "quality_score": oer.quality_score if oer else 0.0,
            "price_penalty_percentage": oer.price_penalty_percentage if oer else 0.0,
            "final_price_per_kg": oer.final_price_per_kg if oer else 0.0,
            "total_payout_rp": oer.total_payout if oer else 0.0,
            "ffa_risk_category": oer.ffa_risk_category if oer else "UNKNOWN"
        },
        "compliance_verification": {
            "eudr_compliant": bool(block and block.latitude and block.longitude),
            "ispo_rspo_aligned": bool(farmer and farmer.certification_status in ["ISPO", "RSPO", "BOTH"]),
            "transparency_guaranteed": True
        }
    }

@router.get("/export/excel")
def export_lhp_excel(db: Session = Depends(get_db)):
    """
    Ekspor Laporan Harian Pengolahan (LHP) & Rekap Mutu TBS (.xlsx)
    Format resmi pabrik kelapa sawit untuk mandor dan accounting.
    """
    from backend.app.services.excel_exporter import FactoryExcelExporter
    from fastapi.responses import Response

    sessions = db.query(GradingSession).order_by(GradingSession.graded_at.desc()).all()
    excel_bytes = FactoryExcelExporter.generate_lhp_excel(sessions)

    filename = f"LHP_Rekap_TBS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/sync/status")
def get_offline_sync_status(db: Session = Depends(get_db)):
    """Mengecek status buffer lokal dan sinkronisasi ke cloud PKS."""
    from backend.app.services.offline_sync import global_sync_manager
    return global_sync_manager.get_sync_summary(db)

@router.post("/sync/trigger")
def trigger_offline_sync(db: Session = Depends(get_db)):
    """Memicu proses sinkronisasi batch dari buffer lokal ke server pusat."""
    from backend.app.services.offline_sync import global_sync_manager
    return global_sync_manager.trigger_batch_sync(db)
