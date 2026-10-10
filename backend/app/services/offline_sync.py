import time
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal
from backend.app.models.entities import GradingSession

logger = logging.getLogger("OfflineSync")

class OfflineSyncManager:
    """
    Offline-First Buffer & Cloud Sync Engine untuk Pabrik Kelapa Sawit.
    Menyimpan status sinkronisasi lokal dan melakukan transmisi batch saat online.
    """

    def __init__(self):
        self.last_sync_timestamp = time.time()
        self.sync_status = "IDLE"  # IDLE, SYNCING, OFFLINE, ERROR
        self.pending_count = 0

    def check_connection(self) -> bool:
        """Simulasi uji konektivitas ke server cloud PKS pusat."""
        return True

    def get_sync_summary(self, db: Session) -> Dict[str, Any]:
        total_sessions = db.query(GradingSession).count()
        return {
            "mode": "OFFLINE_FIRST_BUFFER",
            "is_online": self.check_connection(),
            "local_database": "SQLite (smart_grade.db)",
            "total_local_records": total_sessions,
            "last_successful_sync": datetime.fromtimestamp(self.last_sync_timestamp).strftime("%d-%m-%Y %H:%M:%S WIB"),
            "sync_status": self.sync_status
        }

    def trigger_batch_sync(self, db: Session) -> Dict[str, Any]:
        """Menjalankan proses sinkronisasi batch lokal ke cloud."""
        if not self.check_connection():
            self.sync_status = "OFFLINE"
            return {"status": "offline", "message": "Jaringan cloud pusat tidak terjangkau. Data tersimpan aman di buffer lokal."}

        self.sync_status = "SYNCING"
        sessions = db.query(GradingSession).all()
        synced_count = len(sessions)
        
        # Simulasi transmisi payload
        time.sleep(0.5)
        self.last_sync_timestamp = time.time()
        self.sync_status = "IDLE"

        return {
            "status": "success",
            "records_pushed": synced_count,
            "cloud_destination": "https://cloud-api.pcwe-palm.ac.id/sync/v1",
            "timestamp": datetime.now().isoformat()
        }

global_sync_manager = OfflineSyncManager()
