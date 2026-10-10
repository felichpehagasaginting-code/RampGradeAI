import json
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.api.v1.grading import inference_engine, tripwire_tracker

router = APIRouter(tags=["WebSocket Real-Time Stream"])

@router.websocket("/grading/ws-stream")
async def websocket_grading_stream(websocket: WebSocket):
    """
    WebSocket endpoint untuk streaming frame biner berkecepatan tinggi (> 30 FPS)
    dengan prapemrosesan CLAHE dan Spatial ByteTrack Tripwire.
    """
    await websocket.accept()
    try:
        while True:
            # Terima frame citra dalam format bytes/binary
            data = await websocket.receive_bytes()
            if not data:
                continue

            t0 = time.time()
            frame_res = inference_engine.predict_frame(data, allow_fallback=True)
            detections = frame_res["detections"]
            height = frame_res["height"]
            width = frame_res["width"]

            # Evaluasi ByteTrack tripwire
            track_res = tripwire_tracker.update(detections, frame_height=height)
            tripwire_y = track_res["tripwire_y"]
            cumulative_counted = track_res["counts"]["total_counted"]

            latency_ms = (time.time() - t0) * 1000.0

            # Kirim kembali payload JSON koordinat dan hitungan
            payload = {
                "tripwire_y": tripwire_y,
                "cumulative_counted": cumulative_counted,
                "total_bunches": len(detections),
                "detections": detections,
                "latency_ms": round(latency_ms, 1),
                "frame_width": width,
                "frame_height": height
            }
            await websocket.send_text(json.dumps(payload))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
