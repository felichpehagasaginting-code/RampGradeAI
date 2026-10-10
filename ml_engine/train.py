import os
import torch
from pathlib import Path
from ultralytics import YOLO

# Path direktori
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_CONFIG = ROOT_DIR / "data" / "data.yaml" if (ROOT_DIR / "data" / "data.yaml").exists() else ROOT_DIR / "ml_engine" / "dataset_config.yaml"
WEIGHTS_DIR = ROOT_DIR / "ml_engine" / "weights"

def train_yolo_model(
    model_size: str = "yolov8n.pt",
    epochs: int = 50,
    imgsz: int = 640,
    batch_size: int = 16,
    device: str = "0"  # Gunakan "cpu" jika tanpa GPU NVIDIA
):
    """
    Melatih / fine-tuning model YOLOv8 untuk 4 kelas kematangan TBS (IOPRI 1997)
    Sesuai Tahap 2 Proposal Penelitian BPDP 2026-2027.
    """
    print("=" * 65)
    print("  PELATIHAN MODEL YOLOv8 - DETEKSI KEMATANGAN TBS (SMART GRADE)")
    print("  Politeknik Citra Widya Edukasi (PCWE) - Riset BPDP 2026-2027")
    print("=" * 65)
    print(f"Base Model    : {model_size}")
    print(f"Dataset Config: {DATA_CONFIG}")
    print(f"Epochs        : {epochs} | Image Size: {imgsz} | Batch: {batch_size}")
    print("=" * 65)

    # 1. Inisialisasi model pre-trained (Transfer Learning dari COCO)
    model = YOLO(model_size)

    # 2. Training
    results = model.train(
        data=str(DATA_CONFIG),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch_size,
        device=device,
        project=str(ROOT_DIR / "runs" / "train"),
        name="smart_grade_iopri",
        save=True,
        plots=True,
        workers=0,  # Wajib 0 di Windows untuk mencegah CUDA_ERROR_ALREADY_MAPPED pada laptop WDDM
        exist_ok=True,
        augment=True  # Augmentasi pencahayaan, rotasi sesuai mitigasi risiko proposal
    )

    # 3. Salin bobot terbaik ke ml_engine/weights/best.pt
    best_weight = ROOT_DIR / "runs" / "train" / "smart_grade_iopri" / "weights" / "best.pt"
    if best_weight.exists():
        import shutil
        target_path = WEIGHTS_DIR / "best.pt"
        shutil.copy(best_weight, target_path)
        print(f"\n[SUKSES] Bobot terbaik berhasil disimpan ke: {target_path}")

        # 4. Ekspor ke format ONNX untuk deployment edge/pabrik hemat daya
        print("\nMengekspor model ke format ONNX...")
        model_best = YOLO(str(target_path))
        onnx_file = model_best.export(format="onnx")
        print(f"[SUKSES] Model ONNX siap digunakan: {onnx_file}")

    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    default_device = "0" if torch.cuda.is_available() else "cpu"
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", type=str, default=default_device)
    parser.add_argument("--model", type=str, default="yolov8n.pt")
    args = parser.parse_args()

    train_yolo_model(
        model_size=args.model,
        epochs=args.epochs,
        imgsz=640,
        batch_size=args.batch,
        device=args.device
    )
