import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.main import app

client = TestClient(app)

def run_integration_tests():
    print("=== [1] Testing Health Endpoint ===")
    res = client.get("/health")
    assert res.status_code == 200, res.text
    print(f"Health response: {res.json()}")

    print("\n=== [2] Testing Farmers API ===")
    res = client.get("/api/v1/farmers/")
    assert res.status_code == 200, res.text
    farmers = res.json()
    print(f"Found {len(farmers)} seeded farmers:")
    for f in farmers:
        print(f" - {f['name']} ({f['farmer_code']}) - Cert: {f['certification_status']}")

    print("\n=== [3] Testing Delivery Orders (SPB) API ===")
    res = client.get("/api/v1/delivery-orders/")
    assert res.status_code == 200, res.text
    orders = res.json()
    print(f"Found {len(orders)} delivery orders:")
    target_spb = orders[0]["spb_number"]
    target_order_id = orders[0]["id"]
    print(f" - SPB: {target_spb}, Truk: {orders[0]['truck_plate_number']}, Berat: {orders[0]['net_weight_kg']} Kg")

    print("\n=== [4] Testing YOLO Grading Predict API ===")
    sample_img = Path(__file__).resolve().parent / "uploads" / "test_sample_tbs.jpg"
    with open(sample_img, "rb") as f:
        res = client.post(
            "/api/v1/grading/predict",
            files={"file": ("test_tbs.jpg", f, "image/jpeg")},
            data={"delivery_order_id": str(target_order_id)}
        )
    assert res.status_code == 200, res.text
    pred_data = res.json()
    session_code = pred_data["session_code"]
    assessment = pred_data["assessment"]
    print(f"Prediction Success: Session Code {session_code}")
    print(f"Inference Latency: {pred_data['inference_latency_ms']} ms")
    print(f"Detections Count: {len(pred_data['detections'])}")
    print(f"Estimasi OER: {assessment['estimated_oer_percentage']}%")
    print(f"Harga Final/Kg: Rp {assessment['final_price_per_kg']}")
    print(f"Total Pembayaran TBS: Rp {assessment['total_payout']:,.2f}")

    print("\n=== [5] Testing Commit Grading Session ===")
    res = client.post(
        "/api/v1/grading/commit",
        json={
            "session_code": session_code,
            "delivery_order_id": target_order_id,
            "operator_name": "Grader Mandor 1 - Felich G.",
            "notes": "TBS varietas DxP Marihat, kondisi baik siap olah"
        }
    )
    assert res.status_code == 200, res.text
    print(f"Commit Success: ID {res.json()['id']}, Status: GRADED")

    print("\n=== [6] Testing Factory Analytics Summary ===")
    res = client.get("/api/v1/analytics/summary")
    assert res.status_code == 200, res.text
    print(f"Analytics Summary: {res.json()}")

    print("\n=== [7] Testing Traceability Audit ISPO/RSPO/EUDR ===")
    res = client.get(f"/api/v1/analytics/audit/{target_spb}")
    assert res.status_code == 200, res.text
    audit = res.json()
    print("Traceability Audit Verified:")
    print(f" - Tiket: {audit['audit_ticket']['spb_number']} ({audit['audit_ticket']['status']})")
    print(f" - Pekebun: {audit['traceability_origin']['farmer_name']} ({audit['traceability_origin']['certification_status']})")
    print(f" - Blok: {audit['traceability_origin']['block_code']} (Lat: {audit['traceability_origin']['geolocation']['latitude']}, Long: {audit['traceability_origin']['geolocation']['longitude']})")
    print(f" - Kepatuhan EUDR: {audit['compliance_verification']['eudr_compliant']}")
    print(f" - Kepatuhan ISPO/RSPO: {audit['compliance_verification']['ispo_rspo_aligned']}")

    print("\n>>> ALL API INTEGRATION TESTS PASSED 100%! <<<")

if __name__ == "__main__":
    run_integration_tests()
