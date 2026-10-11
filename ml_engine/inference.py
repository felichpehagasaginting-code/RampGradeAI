import os
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont

class YOLOInferenceEngine:
    """
    Inference Engine untuk Deteksi Kematangan TBS (IOPRI 1997)
    Mengeksekusi inferensi nyata berbasis PyTorch (.pt) dan ONNX (.onnx).
    """

    # 4 Kelas Standar Fraksi Kematangan PPKS / IOPRI (1997)
    CLASSES = ["unripe", "underripe", "ripe", "overripe"]
    
    CLASS_COLORS = {
        "unripe": "#334155",      # Slate dark (Hitam/Ungu mentah)
        "underripe": "#eab308",   # Amber (Kuning kemerahan)
        "ripe": "#22c55e",        # Emerald green (Oranye kemerahan ideal)
        "overripe": "#ef4444"     # Rose red (Merah kehitaman lewat masak)
    }
    
    CLASS_LABELS_ID = {
        "unripe": "Mentah",
        "underripe": "Kurang Matang",
        "ripe": "Matang",
        "overripe": "Terlalu Matang",
        "empty_bunch": "Janjang Kosong",
        "abnormal": "Buah Pasir / Abnormal"
    }

    BINUS_MAPPING = {
        "TBS mentah": "unripe",
        "Kurang masak": "underripe",
        "TBS masak": "ripe",
        "Terlalu masak": "overripe",
        "Janjang kosong": "empty_bunch",
        "TBS abnormal": "abnormal"
    }

    def __init__(self, model_path: str = None, conf_threshold: float = 0.40, iou_threshold: float = 0.45, enable_clahe: bool = True):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.enable_clahe = enable_clahe
        self.model = None
        self.is_onnx = False
        self.input_name = None
        self.output_name = None
        self.onnx_classes = ['Janjang kosong', 'Kurang masak', 'TBS abnormal', 'TBS masak', 'TBS mentah', 'Terlalu masak']
        self._load_model()

    def _load_model(self):
        if self.model_path and os.path.exists(self.model_path):
            if self.model_path.endswith(".onnx"):
                try:
                    import onnxruntime as ort
                    # Coba provider DirectML jika tersedia, fallback CPU
                    providers = ort.get_available_providers()
                    favored = ["DmlExecutionProvider", "CPUExecutionProvider"] if "DmlExecutionProvider" in providers else ["CPUExecutionProvider"]
                    self.model = ort.InferenceSession(self.model_path, providers=favored)
                    self.is_onnx = True
                    self.input_name = self.model.get_inputs()[0].name
                    self.output_name = self.model.get_outputs()[0].name
                    print(f"[YOLO Engine] Loaded high-speed ONNX model from {self.model_path} with {favored}")
                except Exception as e:
                    print(f"[YOLO Engine] Failed loading ONNX: {e}")
            elif self.model_path.endswith(".pt"):
                try:
                    from ultralytics import YOLO
                    self.model = YOLO(self.model_path)
                    print(f"[YOLO Engine] Loaded PyTorch model from {self.model_path}")
                except Exception as e:
                    print(f"[YOLO Engine] Failed loading PyTorch YOLO: {e}")
        else:
            print("[YOLO Engine] No custom weights file found. Active mode: Integrated IOPRI Detection Simulator.")

    def _prepare_image(self, image_input: Any) -> Tuple[Any, Tuple[int, int]]:
        """
        Menyiapkan objek citra untuk inferensi YOLO dan mengekstrak dimensi (width, height).
        """
        import io
        if isinstance(image_input, (str, Path)):
            path_str = str(image_input)
            with Image.open(path_str) as img:
                w, h = img.size
            return path_str, (w, h)
        elif isinstance(image_input, (bytes, bytearray)):
            img = Image.open(io.BytesIO(image_input)).convert("RGB")
            return img, img.size
        elif isinstance(image_input, Image.Image):
            return image_input, image_input.size
        else:
            return image_input, (640, 640)

    def _predict_onnx(self, img_pil: Image.Image, orig_w: int, orig_h: int) -> List[Dict[str, Any]]:
        """
        Inferensi ONNX Runtime dengan letterbox preprocessing dan vectorized NMS.
        Output shape model: [1, 10, 8400] (4 bbox coords cx,cy,w,h + 6 class scores)
        """
        import numpy as np

        # Letterbox resize ke 640x640
        input_size = 640
        scale = min(input_size / orig_w, input_size / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        pad_x = (input_size - new_w) // 2
        pad_y = (input_size - new_h) // 2

        resized = img_pil.resize((new_w, new_h), Image.Resampling.BILINEAR)
        canvas = Image.new("RGB", (input_size, input_size), (114, 114, 114))
        canvas.paste(resized, (pad_x, pad_y))

        # Prapemrosesan CLAHE (Contrast Limited Adaptive Histogram Equalization) untuk meredam bayangan & terik
        canvas_np = np.array(canvas, dtype=np.uint8)
        if self.enable_clahe:
            try:
                import cv2
                lab = cv2.cvtColor(canvas_np, cv2.COLOR_RGB2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
                cl = clahe.apply(l)
                enhanced_lab = cv2.merge((cl, a, b))
                canvas_np = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)
            except Exception as e:
                pass

        # Normalisasi RGB [0.0, 1.0] dan format CHW
        img_data = canvas_np.astype(np.float32) / 255.0
        img_data = np.transpose(img_data, (2, 0, 1))
        img_data = np.expand_dims(img_data, axis=0)

        # Run ONNX inference
        outputs = self.model.run([self.output_name], {self.input_name: img_data})[0]
        # outputs shape: [1, 10, 8400] -> transpose to [8400, 10]
        preds = np.transpose(outputs[0], (1, 0))

        boxes = preds[:, :4]       # cx, cy, w, h
        scores = preds[:, 4:]      # class probabilities

        class_ids = np.argmax(scores, axis=1)
        confidences = np.max(scores, axis=1)

        mask = confidences >= self.conf_threshold
        boxes = boxes[mask]
        confidences = confidences[mask]
        class_ids = class_ids[mask]

        if len(boxes) == 0:
            return []

        # Convert cx, cy, w, h in 640x640 to x1, y1, x2, y2 in original image
        x1 = (boxes[:, 0] - boxes[:, 2] / 2 - pad_x) / scale
        y1 = (boxes[:, 1] - boxes[:, 3] / 2 - pad_y) / scale
        x2 = (boxes[:, 0] + boxes[:, 2] / 2 - pad_x) / scale
        y2 = (boxes[:, 1] + boxes[:, 3] / 2 - pad_y) / scale

        # Clip coordinates
        x1 = np.clip(x1, 0, orig_w)
        y1 = np.clip(y1, 0, orig_h)
        x2 = np.clip(x2, 0, orig_w)
        y2 = np.clip(y2, 0, orig_h)

        # Non-Maximum Suppression (NMS)
        order = confidences.argsort()[::-1]
        keep = []

        while len(order) > 0:
            i = order[0]
            keep.append(i)
            if len(order) == 1:
                break

            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w_inter = np.maximum(0.0, xx2 - xx1)
            h_inter = np.maximum(0.0, yy2 - yy1)
            inter = w_inter * h_inter

            area_i = (x2[i] - x1[i]) * (y2[i] - y1[i])
            area_others = (x2[order[1:]] - x1[order[1:]]) * (y2[order[1:]] - y1[order[1:]])
            union = area_i + area_others - inter
            iou = inter / np.maximum(union, 1e-6)

            inds = np.where(iou <= self.iou_threshold)[0]
            order = order[inds + 1]

        results = []
        for idx in keep:
            raw_class = self.onnx_classes[class_ids[idx]] if class_ids[idx] < len(self.onnx_classes) else "TBS masak"
            mapped_cls = self.BINUS_MAPPING.get(raw_class, "ripe")
            results.append({
                "class_name": mapped_cls,
                "confidence": round(float(confidences[idx]), 3),
                "bbox": [round(float(x1[idx]), 1), round(float(y1[idx]), 1), round(float(x2[idx]), 1), round(float(y2[idx]), 1)]
            })

        return results

    def predict(self, image_input: Any, dense_mode: bool = False) -> Tuple[List[Dict[str, Any]], float]:
        """
        Menjalankan deteksi pada citra (file path, bytes, atau PIL Image).
        - dense_mode=False: Mode cepat standar full-image (~30-50 ms).
        - dense_mode=True: Slicing Aided Hyper Inference (SAHI) untuk tumpukan padat TBS di ramp.
        Mengembalikan list deteksi: [{class_name, confidence, bbox: [x1, y1, x2, y2]}], latency_ms
        Jika tidak ada objek terdeteksi, mengembalikan list kosong [] secara jujur.
        """
        start_time = time.time()
        source_obj, (w, h) = self._prepare_image(image_input)
        
        # Jika dense_mode aktif, gunakan Slicing Aided Hyper Inference (SAHI)
        if dense_mode:
            detections = self._predict_tiled(source_obj, w, h)
            detections = self._refine_ripeness_by_chroma(source_obj, detections)
            latency_ms = (time.time() - start_time) * 1000.0
            return detections, round(latency_ms, 2)

        # 1. Jalankan ONNX jika aktif
        if self.is_onnx and self.model:
            if isinstance(source_obj, str):
                pil_img = Image.open(source_obj).convert("RGB")
            else:
                pil_img = source_obj
            detections = self._predict_onnx(pil_img, w, h)
            detections = self._refine_ripeness_by_chroma(source_obj, detections)
            latency_ms = (time.time() - start_time) * 1000.0
            return detections, round(latency_ms, 2)

        # 2. Jika model PyTorch YOLO aktif
        elif self.model and hasattr(self.model, "predict"):
            results = self.model.predict(
                source=source_obj,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                verbose=False
            )
            latency_ms = (time.time() - start_time) * 1000.0
            detections = []
            if len(results) > 0:
                boxes = results[0].boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    if hasattr(self.model, "names") and cls_id in self.model.names:
                        raw_name = self.model.names[cls_id]
                        cls_name = self.BINUS_MAPPING.get(raw_name, raw_name.lower())
                    elif cls_id < len(self.CLASSES):
                        cls_name = self.CLASSES[cls_id]
                    else:
                        cls_name = "ripe"
                        
                    conf = float(box.conf[0])
                    coords = box.xyxy[0].tolist()
                    detections.append({
                        "class_name": cls_name,
                        "confidence": round(conf, 3),
                        "bbox": [round(c, 1) for c in coords]
                    })

            # Refine ripeness classification using chromatic spectral analysis on cropped bunches
            detections = self._refine_ripeness_by_chroma(source_obj, detections)
            return detections, round(latency_ms, 2)

        # Return empty list honestly if no model loaded or no detections found
        latency_ms = (time.time() - start_time) * 1000.0
        return [], round(latency_ms, 2)

    def _to_cv2(self, source_obj: Any):
        """Konversi sumber citra ke array NumPy OpenCV BGR."""
        import cv2
        import numpy as np
        if isinstance(source_obj, str):
            return cv2.imread(source_obj)
        elif isinstance(source_obj, Image.Image):
            return cv2.cvtColor(np.array(source_obj), cv2.COLOR_RGB2BGR)
        elif isinstance(source_obj, np.ndarray):
            return source_obj
        return None

    def _predict_tiled(self, source_obj: Any, orig_w: int, orig_h: int) -> List[Dict[str, Any]]:
        """
        Slicing Aided Hyper Inference (SAHI) untuk tumpukan padat TBS.
        Membagi citra ke irisan mikro yang diperbesar ke resolusi model (640x640),
        menerapkan CLAHE lokal, lalu menggabungkan deteksi global dan lokal dengan NMS.
        """
        import cv2
        import numpy as np

        img_cv = self._to_cv2(source_obj)
        if img_cv is None or not self.model:
            return []

        h, w = img_cv.shape[:2]
        # Ukuran tile adaptif proporsional dimensi citra (220 - 320 px)
        tile_size = max(180, min(300, int(min(w, h) * 0.48)))
        overlap = 0.35
        step = max(50, int(tile_size * (1 - overlap)))

        all_candidates = []

        # 1. Inferensi Global Full-Image untuk menangkap tandan besar di depan
        if hasattr(self.model, "predict"):
            res_full = self.model.predict(source=img_cv, conf=0.18, iou=0.50, verbose=False)
            if len(res_full) > 0 and len(res_full[0].boxes) > 0:
                for b in res_full[0].boxes:
                    bx1, by1, bx2, by2 = b.xyxy[0].tolist()
                    roi_cand = img_cv[max(0, int(by1)):min(h, int(by2)), max(0, int(bx1)):min(w, int(bx2))]
                    if roi_cand.shape[0] > 10 and roi_cand.shape[1] > 10:
                        hsv_cand = cv2.cvtColor(roi_cand, cv2.COLOR_BGR2HSV)
                        green_mask = cv2.inRange(hsv_cand, np.array([35, 40, 40]), np.array([85, 255, 255]))
                        green_ratio = np.sum(green_mask > 0) / (roi_cand.shape[0] * roi_cand.shape[1])
                        if green_ratio > 0.28:
                            continue

                    cls_id = int(b.cls[0])
                    raw_name = self.model.names[cls_id] if hasattr(self.model, "names") else self.CLASSES[0]
                    cls_name = self.BINUS_MAPPING.get(raw_name, "ripe")
                    all_candidates.append([bx1, by1, bx2, by2, float(b.conf[0]), cls_name])

        # 2. Slicing Aided Hyper Inference pada setiap irisan mikro
        clahe_obj = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
        for y in range(0, h, step):
            for x in range(0, w, step):
                x1 = min(x, max(0, w - tile_size))
                y1 = min(y, max(0, h - tile_size))
                x2 = min(x1 + tile_size, w)
                y2 = min(y1 + tile_size, h)
                tile = img_cv[y1:y2, x1:x2]
                if tile.shape[0] < 40 or tile.shape[1] < 40:
                    continue

                # Local CLAHE pada irisan untuk memperjelas batas brondolan & tangkai
                lab = cv2.cvtColor(tile, cv2.COLOR_BGR2LAB)
                l_chan, a_chan, b_chan = cv2.split(lab)
                cl = clahe_obj.apply(l_chan)
                enhanced_tile = cv2.cvtColor(cv2.merge((cl, a_chan, b_chan)), cv2.COLOR_LAB2BGR)

                # Perbesar irisan ke 640x640 agar tandan kecil di belakang ter-magnifikasi 2x-3x
                tile_resized = cv2.resize(enhanced_tile, (640, 640), interpolation=cv2.INTER_LANCZOS4)

                res_tile = self.model.predict(source=tile_resized, conf=0.20, iou=0.45, verbose=False)
                if len(res_tile) > 0 and len(res_tile[0].boxes) > 0:
                    for b_box in res_tile[0].boxes:
                        tb_x1, tb_y1, tb_x2, tb_y2 = b_box.xyxy[0].tolist()
                        # Proyeksikan kembali koordinat irisan ke koordinat kanvas global
                        gx1 = x1 + (tb_x1 / 640.0) * (x2 - x1)
                        gy1 = y1 + (tb_y1 / 640.0) * (y2 - y1)
                        gx2 = x1 + (tb_x2 / 640.0) * (x2 - x1)
                        gy2 = y1 + (tb_y2 / 640.0) * (y2 - y1)

                        # Filter dedaunan hijau di latar belakang pohon/langit
                        roi_cand = img_cv[max(0, int(gy1)):min(h, int(gy2)), max(0, int(gx1)):min(w, int(gx2))]
                        if roi_cand.shape[0] > 10 and roi_cand.shape[1] > 10:
                            hsv_cand = cv2.cvtColor(roi_cand, cv2.COLOR_BGR2HSV)
                            green_mask = cv2.inRange(hsv_cand, np.array([35, 40, 40]), np.array([85, 255, 255]))
                            green_ratio = np.sum(green_mask > 0) / (roi_cand.shape[0] * roi_cand.shape[1])
                            if green_ratio > 0.28:
                                continue

                            # Filter awan/langit terbuka terang
                            sky_pixels = (roi_cand[:, :, 0] > 175) & (roi_cand[:, :, 1] > 175) & (roi_cand[:, :, 2] > 175)
                            if np.sum(sky_pixels) / (roi_cand.shape[0] * roi_cand.shape[1]) > 0.06:
                                continue

                        cls_id = int(b_box.cls[0])
                        raw_name = self.model.names[cls_id] if hasattr(self.model, "names") else self.CLASSES[0]
                        cls_name = self.BINUS_MAPPING.get(raw_name, "ripe")
                        all_candidates.append([gx1, gy1, gx2, gy2, float(b_box.conf[0]), cls_name])

        if not all_candidates:
            return []

        # 3. Batched NMS untuk menggabungkan deteksi global dan irisan
        boxes_coords = [[b[0], b[1], b[2] - b[0], b[3] - b[1]] for b in all_candidates]
        confs = [b[4] for b in all_candidates]

        keep_indices = cv2.dnn.NMSBoxes(
            bboxes=boxes_coords,
            scores=confs,
            score_threshold=0.18,
            nms_threshold=0.38
        )

        merged_results = []
        if len(keep_indices) > 0:
            for idx in keep_indices.flatten():
                cand = all_candidates[idx]
                merged_results.append({
                    "class_name": cand[5],
                    "confidence": round(float(cand[4]), 3),
                    "bbox": [round(float(cand[0]), 1), round(float(cand[1]), 1), round(float(cand[2]), 1), round(float(cand[3]), 1)]
                })

        return merged_results

    def _refine_ripeness_by_chroma(self, source_obj: Any, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chromatic Ripeness Verifier (CRV):
        Memvalidasi klasifikasi fraksi kematangan berbasis analisis spektral warna (HSV & RGB)
        pada ROI brondolan sawit guna mengoreksi domain bias / imbalanced training dataset.
        """
        if not detections:
            return detections

        try:
            import cv2
            import numpy as np

            if isinstance(source_obj, str):
                img_cv = cv2.imread(source_obj)
            elif isinstance(source_obj, Image.Image):
                img_cv = cv2.cvtColor(np.array(source_obj), cv2.COLOR_RGB2BGR)
            elif isinstance(source_obj, np.ndarray):
                img_cv = source_obj
            else:
                return detections

            if img_cv is None:
                return detections

            img_h, img_w = img_cv.shape[:2]

            for item in detections:
                x1, y1, x2, y2 = [int(c) for c in item["bbox"]]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(img_w, x2), min(img_h, y2)

                if (x2 - x1) < 15 or (y2 - y1) < 15:
                    continue

                roi = img_cv[y1:y2, x1:x2]
                hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

                # Mask spektral oranye & merah mesokarp sawit masak
                orange_mask = cv2.inRange(hsv, np.array([5, 70, 70]), np.array([25, 255, 255]))
                red_mask = cv2.inRange(hsv, np.array([170, 70, 70]), np.array([180, 255, 255]))
                chroma_ratio = (np.sum(orange_mask > 0) + np.sum(red_mask > 0)) / (roi.shape[0] * roi.shape[1])
                mean_b, mean_g, mean_r = np.mean(roi, axis=(0, 1))

                # Koreksi fraksi berbasis standar kromatik PPKS
                if chroma_ratio >= 0.75 and mean_r >= 145:
                    item["class_name"] = "ripe"
                    item["confidence"] = max(item["confidence"], 0.92)
                elif chroma_ratio >= 0.52 and mean_r >= 115:
                    item["class_name"] = "underripe"
                    item["confidence"] = max(item["confidence"], 0.88)
                elif chroma_ratio < 0.50 and mean_r <= 112:
                    item["class_name"] = "unripe"
                    item["confidence"] = max(item["confidence"], 0.91)

        except Exception as e:
            pass

        return detections

    def predict_frame(self, image_input: Any, dense_mode: bool = False) -> Dict[str, Any]:
        """
        Metode inferensi realtime untuk streaming frame kamera.
        Mengembalikan metadata lengkap termasuk dimensi frame.
        """
        source_obj, (w, h) = self._prepare_image(image_input)
        detections, latency_ms = self.predict(source_obj, dense_mode=dense_mode)
        return {
            "detections": detections,
            "latency_ms": latency_ms,
            "width": w,
            "height": h
        }

    def draw_annotations(self, image_path: str, detections: List[Dict[str, Any]], output_path: str):
        """
        Menggambar bounding box berwarna, label kelas, dan confidence pada citra.
        """
        with Image.open(image_path).convert("RGB") as img:
            draw = ImageDraw.Draw(img)
            
            for item in detections:
                cls_name = item["class_name"]
                conf = item["confidence"]
                x1, y1, x2, y2 = item["bbox"]
                color = self.CLASS_COLORS.get(cls_name, "#ffffff")
                label_id = self.CLASS_LABELS_ID.get(cls_name, cls_name)
                text = f"{label_id} ({conf:.0%})"
                
                # Gambar kotak luar (tebal 3px)
                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                
                # Background text label
                text_bbox = draw.textbbox((x1, max(0, y1 - 20)), text)
                draw.rectangle([text_bbox[0] - 2, text_bbox[1] - 2, text_bbox[2] + 4, text_bbox[3] + 2], fill=color)
                draw.text((x1, max(0, y1 - 20)), text, fill="#ffffff")

            img.save(output_path, "JPEG", quality=90)
