import uvicorn
import webbrowser
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    print("=" * 60)
    print("  SMART GRADE - Deteksi Kematangan TBS & Traceability")
    print("  Politeknik Citra Widya Edukasi (PCWE) - Lomba BPDP 2026-2027")
    print("=" * 60)
    print("  • Web Dashboard & Visualizer: http://127.0.0.1:8000")
    print("  • REST API Documentation:    http://127.0.0.1:8000/docs")
    print("  • Health Endpoint:            http://127.0.0.1:8000/health")
    print("=" * 60)
    
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)
