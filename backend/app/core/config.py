from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "SMART GRADE API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Base Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    ROOT_DIR: Path = BASE_DIR.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    WEIGHTS_DIR: Path = ROOT_DIR / "ml_engine" / "weights"
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/smart_grade.db"
    
    # Model Configuration
    DEFAULT_MODEL_PATH: str = str(ROOT_DIR / "ml_engine" / "weights" / "best.pt")
    ONNX_MODEL_PATH: str = str(ROOT_DIR / "ml_engine" / "weights" / "best.onnx")
    INFERENCE_BACKEND: str = "onnx"  # "onnx" or "pytorch"
    CONFIDENCE_THRESHOLD: float = 0.40
    IOU_THRESHOLD: float = 0.45
    
    # IOPRI Oil Extraction Constants
    OER_YIELD_UNRIPE: float = 0.120      # 12.0%
    OER_YIELD_UNDERRIPE: float = 0.170   # 17.0%
    OER_YIELD_RIPE: float = 0.235        # 23.5%
    OER_YIELD_OVERRIPE: float = 0.210    # 21.0%
    
    # Base Commercial Price for TBS (Rp / Kg) reference
    DEFAULT_TBS_PRICE_PER_KG: float = 2850.0  # Rp 2.850 / kg
    BASELINE_OER_BENCHMARK: float = 21.5      # 21.5%

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
