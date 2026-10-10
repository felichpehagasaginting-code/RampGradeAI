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

def test_inference_simulator():
    print("=== Testing Inference Engine & Annotator ===")
    # Buat dummy image untuk tes inferensi
    test_img_path = settings.UPLOAD_DIR / "test_sample_tbs.jpg"
    annotated_img_path = settings.UPLOAD_DIR / "test_sample_annotated.jpg"
    
    img = Image.new("RGB", (640, 640), color=(40, 60, 45))
    img.save(test_img_path)
    
    engine = YOLOInferenceEngine(model_path=settings.DEFAULT_MODEL_PATH)
    detections, latency = engine.predict(str(test_img_path))
    print(f"Deteksi ditemukan: {len(detections)} tandan, latency: {latency} ms")
    assert len(detections) > 0
    
    engine.draw_annotations(str(test_img_path), detections, str(annotated_img_path))
    assert annotated_img_path.exists()
    print(f"Anotasi citra tersimpan di: {annotated_img_path}")
    print("[PASS] Inference Engine & Annotator Test Passed!\n")

if __name__ == "__main__":
    test_oer_calculation()
    test_inference_simulator()
    print("Semua pengujian unit test backend dan domain core berhasil!")
