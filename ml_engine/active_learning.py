import os
import json
import time
import shutil
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image

class ActiveLearningManager:
    """
    MLOps Engine: Active Learning & Self-Improving Pipeline untuk SMART GRADE.
    Mengumpulkan citra & koreksi label dari operator grader di lapangan,
    menyiapkan dataset format YOLO, dan memicu pelatihan ulang di background.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent / "data" / "active_learning"
        self.images_dir = self.base_dir / "images"
        self.labels_dir = self.base_dir / "labels"
        self.metadata_file = self.base_dir / "metadata.json"
        
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.labels_dir.mkdir(parents=True, exist_ok=True)

        self.class_indices = {
            "unripe": 4,        # TBS mentah
            "underripe": 1,     # Kurang masak
            "ripe": 3,          # TBS masak
            "overripe": 5,      # Terlalu masak
            "empty_bunch": 0,   # Janjang kosong
            "abnormal": 2       # TBS abnormal / buah pasir
        }

        self.is_training = False
        self.last_training_log = "Belum ada riwayat retraining otomatis."
        self.training_thread: Optional[threading.Thread] = None

    def save_correction(
        self,
        image_bytes: bytes,
        annotations: List[Dict[str, Any]],
        operator_name: str = "Grader Lapangan",
        session_code: str = ""
    ) -> Dict[str, Any]:
        """
        Menyimpan citra mentah dan anotasi koreksi dalam format standar YOLO (txt):
        format baris: <class_id> <cx_norm> <cy_norm> <w_norm> <h_norm>
        """
        import io
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = img.size

        timestamp = int(time.time())
        sample_id = f"al_{timestamp}_{session_code or 'manual'}"
        img_path = self.images_dir / f"{sample_id}.jpg"
        label_path = self.labels_dir / f"{sample_id}.txt"

        img.save(img_path, "JPEG", quality=95)

        yolo_lines = []
        for ann in annotations:
            cls_name = ann.get("class_name", "ripe")
            cls_id = self.class_indices.get(cls_name, 3)

            # bbox format [x1, y1, x2, y2]
            x1, y1, x2, y2 = ann["bbox"]
            box_w = max(1.0, x2 - x1)
            box_h = max(1.0, y2 - y1)
            cx = x1 + box_w / 2.0
            cy = y1 + box_h / 2.0

            # Normalisasi ke [0, 1]
            cx_n = min(1.0, max(0.0, cx / w))
            cy_n = min(1.0, max(0.0, cy / h))
            w_n = min(1.0, max(0.0, box_w / w))
            h_n = min(1.0, max(0.0, box_h / h))

            yolo_lines.append(f"{cls_id} {cx_n:.6f} {cy_n:.6f} {w_n:.6f} {h_n:.6f}")

        with open(label_path, "w") as f:
            f.write("\n".join(yolo_lines))

        # Update metadata ledger
        metadata = self.get_status()
        metadata["samples_count"] += 1
        metadata["recent_samples"].append({
            "sample_id": sample_id,
            "operator_name": operator_name,
            "annotations_count": len(annotations),
            "timestamp": timestamp
        })
        if len(metadata["recent_samples"]) > 50:
            metadata["recent_samples"].pop(0)

        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        return {
            "status": "success",
            "sample_id": sample_id,
            "total_samples": metadata["samples_count"],
            "message": "Sampel koreksi grader berhasil dicatat ke Active Learning queue."
        }

    def get_status(self) -> Dict[str, Any]:
        """Mengambil status antrean dan statistik Active Learning."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Hitung langsung dari folder
        sample_files = list(self.images_dir.glob("*.jpg"))
        return {
            "samples_count": len(sample_files),
            "is_training": self.is_training,
            "last_training_log": self.last_training_log,
            "threshold_for_auto_retrain": 20,
            "recent_samples": []
        }

    def trigger_retraining(self, epochs: int = 10, batch_size: int = 8) -> Dict[str, Any]:
        """
        Memicu proses fine-tuning model di thread terpisah.
        """
        if self.is_training:
            return {"status": "already_running", "message": "Proses pelatihan ulang sedang berlangsung."}

        status = self.get_status()
        if status["samples_count"] == 0:
            return {"status": "insufficient_data", "message": "Belum ada sampel koreksi grader yang tersimpan."}

        self.is_running = True
        self.training_thread = threading.Thread(
            target=self._run_retrain_worker,
            args=(epochs, batch_size),
            daemon=True
        )
        self.training_thread.start()

        return {
            "status": "started",
            "message": f"Background fine-tuning dimulai ({epochs} epochs, {status['samples_count']} sampel)."
        }

    def _run_retrain_worker(self, epochs: int, batch: int):
        """Worker internal background training."""
        self.is_training = True
        try:
            from ultralytics import YOLO
            root_dir = Path(__file__).resolve().parent.parent
            base_model_path = root_dir / "ml_engine" / "weights" / "best.pt"
            data_config = root_dir / "data" / "data.yaml"

            self.last_training_log = f"[{time.strftime('%H:%M:%S')}] Memulai fine-tuning transfer learning..."
            
            # Buat instance YOLO dan lakukan fine-tuning
            model = YOLO(str(base_model_path) if base_model_path.exists() else "yolov8n.pt")
            results = model.train(
                data=str(data_config),
                epochs=epochs,
                imgsz=640,
                batch=batch,
                device="cpu",  # Aman di semua mesin lapangan
                workers=0,
                project=str(root_dir / "runs" / "active_learning"),
                name="retrain_run",
                exist_ok=True,
                verbose=False
            )

            # Ekspor bobot baru ke format ONNX
            export_path = root_dir / "ml_engine" / "weights" / "best.onnx"
            model.export(format="onnx")
            
            self.last_training_log = f"[{time.strftime('%H:%M:%S')}] Retraining selesai! Bobot ONNX berhasil diperbarui secara otomatis."
        except Exception as e:
            self.last_training_log = f"[{time.strftime('%H:%M:%S')}] Error saat retraining: {str(e)}"
        finally:
            self.is_training = False

# Global instance
global_active_learning = ActiveLearningManager()
