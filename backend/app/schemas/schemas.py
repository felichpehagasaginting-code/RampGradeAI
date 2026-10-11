from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- Detection Box Schemas ---
class BoundingBox(BaseModel):
    class_name: str
    confidence: float
    bbox: List[float] = Field(..., description="[x1, y1, x2, y2]")

# --- Farmer Schemas ---
class FarmerBase(BaseModel):
    name: str
    nik: Optional[str] = None
    phone_number: Optional[str] = None
    cooperative_name: Optional[str] = None
    certification_status: str = "NONE"

class FarmerCreate(FarmerBase):
    pass

class FarmerResponse(FarmerBase):
    id: int
    farmer_code: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Plantation Block Schemas ---
class BlockBase(BaseModel):
    area_hectares: float = 1.0
    latitude: float
    longitude: float
    planting_year: Optional[int] = 2018
    variety: str = "DxP"
    legal_status: str = "SHM"
    boundary_geojson: Optional[str] = None
    eudr_compliant: str = "VERIFIED"
    deforestation_cutoff_date: str = "2020-12-31"

class BlockCreate(BlockBase):
    farmer_id: int

class BlockResponse(BlockBase):
    id: int
    farmer_id: int
    block_code: str

    class Config:
        from_attributes = True

# --- Delivery Order (SPB) Schemas ---
class DeliveryOrderCreate(BaseModel):
    farmer_id: int
    block_id: int
    truck_plate_number: str
    driver_name: Optional[str] = None
    net_weight_kg: float

class DeliveryOrderResponse(BaseModel):
    id: int
    spb_number: str
    farmer_id: int
    block_id: int
    truck_plate_number: str
    driver_name: Optional[str]
    net_weight_kg: float
    arrival_time: datetime
    status: str

    class Config:
        from_attributes = True

# --- OER Calculation Result Schemas ---
class OERCalculationResult(BaseModel):
    total_bunches: int
    unripe_count: int
    underripe_count: int
    ripe_count: int
    overripe_count: int
    empty_bunch_count: int = 0
    abnormal_count: int = 0
    long_stalk_count: int = 0
    
    unripe_percentage: float
    underripe_percentage: float
    ripe_percentage: float
    overripe_percentage: float
    empty_bunch_percentage: float = 0.0
    abnormal_percentage: float = 0.0
    long_stalk_percentage: float = 0.0
    
    estimated_oer_percentage: float
    baseline_oer_percentage: float
    oer_variance: float
    quality_score: float
    
    price_per_kg_base: float
    price_penalty_percentage: float
    stalk_penalty_percentage: float = 0.0
    effective_net_weight_kg: Optional[float] = None
    final_price_per_kg: float
    total_payout: Optional[float] = None
    ffa_risk_category: str

# --- Prediction & Grading Response ---
class GradingPredictionResponse(BaseModel):
    session_code: str
    inference_latency_ms: float
    image_url: str
    annotated_image_url: str
    detections: List[BoundingBox]
    assessment: OERCalculationResult

class GradingSessionCommit(BaseModel):
    session_code: str
    delivery_order_id: Optional[int] = None
    operator_name: str = "Petugas Grader"
    notes: Optional[str] = None

class GradingSessionResponse(BaseModel):
    id: int
    session_code: str
    operator_name: str
    delivery_order_id: Optional[int]
    image_path: Optional[str]
    annotated_image_path: Optional[str]
    total_bunches: int
    count_unripe: int
    count_underripe: int
    count_ripe: int
    count_overripe: int
    count_long_stalk: int = 0
    inference_latency_ms: float
    model_version: str
    graded_at: datetime
    assessment: Optional[OERCalculationResult] = None

    class Config:
        from_attributes = True

class CameraFramePredictionResponse(BaseModel):
    total_bunches: int
    unripe_count: int
    underripe_count: int
    ripe_count: int
    overripe_count: int
    empty_bunch_count: int = 0
    abnormal_count: int = 0
    long_stalk_count: int = 0
    unripe_percentage: float
    underripe_percentage: float
    ripe_percentage: float
    overripe_percentage: float
    empty_bunch_percentage: float = 0.0
    abnormal_percentage: float = 0.0
    long_stalk_percentage: float = 0.0
    estimated_oer_percentage: float
    quality_score: float
    ffa_risk_category: str
    inference_latency_ms: float
    frame_width: int
    frame_height: int
    detections: List[BoundingBox]
    tripwire_y: Optional[float] = None
    cumulative_counted: Optional[int] = None
