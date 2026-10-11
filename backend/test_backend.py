import sys
from pathlib import Path
from PIL import Image

# Pastikan path modul root terbaca
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.services.oer_calculator import OERCalculator
from ml_engine.inference import YOLOInferenceEngine
from backend.app.core.config import settings

def test_oer_calculation():
    print("=== Testing OER Calculator ===")
    counts = {
        "ripe": 7,
        "underripe": 2,
        "unripe": 0,
        "overripe": 1
    }
    res = OERCalculator.calculate(counts=counts, net_weight_kg=7500.0, base_price_per_kg=2850.0)
    print(f"Total Buah: {res.total_bunches}")
    print(f"Estimasi OER: {res.estimated_oer_percentage}% (Baseline: {res.baseline_oer_percentage}%)")
    print(f"Variance: {res.oer_variance}%")
    print(f"Quality Score: {res.quality_score}")
    print(f"Harga Final/Kg: Rp {res.final_price_per_kg}")
    print(f"Total Payout (7.5 ton): Rp {res.total_payout:,.2f}")
    print(f"FFA Risk: {res.ffa_risk_category}")
    assert res.total_bunches == 10
    assert res.estimated_oer_percentage > 20.0
    print("[PASS] OER Calculator Test Passed!\n")

def test_inference_integrity():
    print("=== Testing Inference Engine Integrity ===")
    test_img_path = settings.UPLOAD_DIR / "test_sample_tbs.jpg"
    annotated_img_path = settings.UPLOAD_DIR / "test_sample_annotated.jpg"
    
    # 1. Citra kanvas polos tanpa objek TBS
    img = Image.new("RGB", (640, 640), color=(40, 60, 45))
    img.save(test_img_path)
    
    engine = YOLOInferenceEngine(model_path=settings.DEFAULT_MODEL_PATH)
    # Default: allow_fallback=False (wajib mengembalikan list kosong secara jujur)
    detections, latency = engine.predict(str(test_img_path), allow_fallback=False)
    print(f"Hasil inferensi citra polos: {len(detections)} deteksi (latency: {latency} ms)")
    # Pastikan TIDAK mengarang objek palsu pada citra kosong
    assert len(detections) == 0, "Inference engine tidak boleh mengarang deteksi pada citra kosong!"
    print("[PASS] Integritas inferensi jujur terverifikasi: 0 deteksi palsu.")
    
    # 2. Uji fungsi rendering anotasi visual dengan data deteksi eksplisit
    sample_detections = [
        {"class_name": "ripe", "confidence": 0.92, "bbox": [50.0, 50.0, 200.0, 200.0]},
        {"class_name": "underripe", "confidence": 0.85, "bbox": [250.0, 100.0, 420.0, 300.0]}
    ]
    engine.draw_annotations(str(test_img_path), sample_detections, str(annotated_img_path))
    assert annotated_img_path.exists()
    print(f"Anotasi citra tersimpan di: {annotated_img_path}")
    print("[PASS] Rendering anotasi visual berhasil diverifikasi!\n")

if __name__ == "__main__":
    test_oer_calculation()
    test_inference_integrity()
    print("Semua pengujian unit test backend dan integritas ilmiah berhasil!")
