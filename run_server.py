import uvicorn
from backend.app.main import app

if __name__ == "__main__":
    print("[Server] Launching SMART GRADE API on http://127.0.0.1:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
