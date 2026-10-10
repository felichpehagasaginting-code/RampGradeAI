import math
import time
from typing import List, Dict, Any, Tuple, Optional

class TrackedBunch:
    """
    Representasi sebuah tandan buah segar (TBS) yang terlacak secara spasial.
    """
    def __init__(self, track_id: int, bbox: List[float], class_name: str, confidence: float):
        self.track_id = track_id
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.class_name = class_name
        self.confidence = confidence
        self.centroid = self._calc_centroid(bbox)
        self.trajectory = [self.centroid]
        self.last_seen = time.time()
        self.has_crossed_tripwire = False
        self.missed_frames = 0

    @staticmethod
    def _calc_centroid(bbox: List[float]) -> Tuple[float, float]:
        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0
        return (cx, cy)

    def update(self, bbox: List[float], class_name: str, confidence: float):
        self.bbox = bbox
        self.class_name = class_name
        self.confidence = confidence
        self.centroid = self._calc_centroid(bbox)
        self.trajectory.append(self.centroid)
        if len(self.trajectory) > 30:
            self.trajectory.pop(0)
        self.last_seen = time.time()
        self.missed_frames = 0


class SpatialByteTracker:
    """
    Spatial Multi-Object Tracker & Virtual Tripwire Counter untuk TBS.
    Mencegah bias double counting pada video konveyor/loading ramp.
    """
    def __init__(
        self,
        iou_threshold: float = 0.35,
        max_dist_px: float = 120.0,
        max_missed_frames: int = 15,
        tripwire_ratio: float = 0.55  # Garis virtual berada di 55% tinggi frame
    ):
        self.iou_threshold = iou_threshold
        self.max_dist_px = max_dist_px
        self.max_missed_frames = max_missed_frames
        self.tripwire_ratio = tripwire_ratio
        
        self.next_track_id = 1
        self.tracks: Dict[int, TrackedBunch] = {}
        
        # Counter agregat kumulatif
        self.counts = {
            "total_counted": 0,
            "unripe": 0,
            "underripe": 0,
            "ripe": 0,
            "overripe": 0
        }

    def reset_counter(self):
        """Reset seluruh hitungan kumulatif tripwire."""
        self.counts = {
            "total_counted": 0,
            "unripe": 0,
            "underripe": 0,
            "ripe": 0,
            "overripe": 0
        }
        self.tracks.clear()
        self.next_track_id = 1

    @staticmethod
    def _calculate_iou(b1: List[float], b2: List[float]) -> float:
        x1 = max(b1[0], b2[0])
        y1 = max(b1[1], b2[1])
        x2 = min(b1[2], b2[2])
        y2 = min(b1[3], b2[3])

        inter_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        if inter_area <= 0:
            return 0.0

        b1_area = (b1[2] - b1[0]) * (b1[3] - b1[1])
        b2_area = (b2[2] - b2[0]) * (b2[3] - b2[1])
        union_area = b1_area + b2_area - inter_area
        return inter_area / union_area if union_area > 0 else 0.0

    @staticmethod
    def _euclidean_dist(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def update(self, detections: List[Dict[str, Any]], frame_height: int = 640) -> Dict[str, Any]:
        """
        Menerima daftar deteksi per frame [{class_name, confidence, bbox}],
        melakukan tracking spasial, dan mengevaluasi crossing garis virtual tripwire.
        """
        tripwire_y = float(frame_height) * self.tripwire_ratio
        matched_track_ids = set()
        matched_det_indices = set()

        # 1. Asosiasi IoU & Euclidean Distance
        for track_id, track in list(self.tracks.items()):
            best_iou = 0.0
            best_det_idx = -1
            best_dist = float("inf")

            for i, det in enumerate(detections):
                if i in matched_det_indices:
                    continue
                iou = self._calculate_iou(track.bbox, det["bbox"])
                dist = self._euclidean_dist(track.centroid, TrackedBunch._calc_centroid(det["bbox"]))

                if iou > best_iou:
                    best_iou = iou
                    best_det_idx = i
                elif best_iou == 0.0 and dist < best_dist and dist <= self.max_dist_px:
                    best_dist = dist
                    best_det_idx = i

            if (best_iou >= self.iou_threshold or best_dist <= self.max_dist_px) and best_det_idx >= 0:
                det = detections[best_det_idx]
                prev_y = track.centroid[1]
                track.update(det["bbox"], det["class_name"], det["confidence"])
                curr_y = track.centroid[1]

                # Periksa apakah memotong garis virtual dari atas ke bawah (conveyor flow downward)
                if not track.has_crossed_tripwire:
                    if (prev_y <= tripwire_y and curr_y >= tripwire_y) or (
                        len(track.trajectory) >= 2 and track.trajectory[0][1] < tripwire_y and curr_y >= tripwire_y
                    ):
                        track.has_crossed_tripwire = True
                        self.counts["total_counted"] += 1
                        cls_key = det["class_name"]
                        if cls_key in self.counts:
                            self.counts[cls_key] += 1
                        else:
                            self.counts["ripe"] += 1

                matched_track_ids.add(track_id)
                matched_det_indices.add(best_det_idx)
            else:
                track.missed_frames += 1

        # 2. Registrasi objek baru
        for i, det in enumerate(detections):
            if i not in matched_det_indices:
                new_track = TrackedBunch(
                    track_id=self.next_track_id,
                    bbox=det["bbox"],
                    class_name=det["class_name"],
                    confidence=det["confidence"]
                )
                self.tracks[self.next_track_id] = new_track
                matched_track_ids.add(self.next_track_id)
                self.next_track_id += 1

        # 3. Pembersihan tracks yang hilang melebihi ambang batas
        to_delete = [
            tid for tid, trk in self.tracks.items()
            if trk.missed_frames > self.max_missed_frames
        ]
        for tid in to_delete:
            del self.tracks[tid]

        # 4. Format hasil objek terlacak untuk visualisasi HUD
        active_tracked_objects = []
        for tid in matched_track_ids:
            if tid in self.tracks:
                t = self.tracks[tid]
                active_tracked_objects.append({
                    "track_id": t.track_id,
                    "class_name": t.class_name,
                    "confidence": t.confidence,
                    "bbox": t.bbox,
                    "centroid": [round(c, 1) for c in t.centroid],
                    "counted": t.has_crossed_tripwire
                })

        return {
            "tripwire_y": round(tripwire_y, 1),
            "counts": dict(self.counts),
            "tracked_objects": active_tracked_objects
        }
