from ml_engine.inference import YOLOInferenceEngine
from collections import Counter

detector = YOLOInferenceEngine(model_path="ml_engine/weights/best.pt")

# 1. Test Studio Image
studio_path = r"C:\Users\felich\.gemini\antigravity\brain\0974850b-dd69-4ef3-9597-e6304ba1b11a\.user_uploaded\media_1791688486151_61392ae5.webp"
s_dets, s_lat = detector.predict(studio_path, dense_mode=False)
s_dets.sort(key=lambda x: x["bbox"][0])
print("=== STUDIO INFERENCE ===")
print(f"Latency: {s_lat} ms")
for i, d in enumerate(s_dets):
    cls = d["class_name"]
    conf = d["confidence"]
    bx = d["bbox"]
    print(f"Bunch {i+1}: cls={cls} conf={conf} bbox={bx}")

# 2. Test Heap Image
heap_path = r"C:\Users\felich\.gemini\antigravity\brain\0974850b-dd69-4ef3-9597-e6304ba1b11a\.user_uploaded\media_1791688838722_829bcf9a.jpg"
h_dets, h_lat = detector.predict(heap_path, dense_mode=True)
print("\n=== DENSE HEAP INFERENCE ===")
print(f"Latency: {h_lat} ms | Total detections: {len(h_dets)}")
print("Distribution:", dict(Counter([d["class_name"] for d in h_dets])))

detector.draw_annotations(heap_path, h_dets, "backend/uploads/final_heap_annotated.jpg")
print("Annotated output saved successfully to backend/uploads/final_heap_annotated.jpg")
