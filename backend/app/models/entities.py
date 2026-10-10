from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    farmer_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    nik = Column(String(30), nullable=True)
    phone_number = Column(String(30), nullable=True)
    cooperative_name = Column(String(150), nullable=True)
    certification_status = Column(String(50), default="NONE")  # NONE, ISPO, RSPO, BOTH
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    blocks = relationship("PlantationBlock", back_populates="farmer", cascade="all, delete-orphan")
    delivery_orders = relationship("DeliveryOrder", back_populates="farmer")


class PlantationBlock(Base):
    __tablename__ = "plantation_blocks"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    block_code = Column(String(50), unique=True, index=True, nullable=False)
    area_hectares = Column(Float, default=1.0)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    planting_year = Column(Integer, nullable=True)
    variety = Column(String(100), default="DxP")
    legal_status = Column(String(100), default="SHM")
    boundary_geojson = Column(Text, nullable=True)  # GeoJSON polygon coordinate string
    eudr_compliant = Column(String(50), default="VERIFIED")  # VERIFIED, EXEMPT_SMALL, NON_COMPLIANT
    deforestation_cutoff_date = Column(String(20), default="2020-12-31")

    # Relationships
    farmer = relationship("Farmer", back_populates="blocks")
    delivery_orders = relationship("DeliveryOrder", back_populates="block")


class DeliveryOrder(Base):
    __tablename__ = "delivery_orders"

    id = Column(Integer, primary_key=True, index=True)
    spb_number = Column(String(100), unique=True, index=True, nullable=False)  # Surat Pengantar Buah
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    block_id = Column(Integer, ForeignKey("plantation_blocks.id"), nullable=False)
    truck_plate_number = Column(String(30), nullable=False)
    driver_name = Column(String(100), nullable=True)
    net_weight_kg = Column(Float, default=0.0)
    arrival_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="PENDING_GRADING")  # PENDING_GRADING, GRADED, REJECTED

    # Relationships
    farmer = relationship("Farmer", back_populates="delivery_orders")
    block = relationship("PlantationBlock", back_populates="delivery_orders")
    grading_sessions = relationship("GradingSession", back_populates="delivery_order", cascade="all, delete-orphan")

    @property
    def grading_session(self):
        return self.grading_sessions[-1] if self.grading_sessions else None


class GradingSession(Base):
    __tablename__ = "grading_sessions"

    id = Column(Integer, primary_key=True, index=True)
    delivery_order_id = Column(Integer, ForeignKey("delivery_orders.id"), nullable=True)
    session_code = Column(String(100), unique=True, index=True, nullable=False)
    operator_name = Column(String(100), default="Operator Grader")
    image_path = Column(String(255), nullable=True)
    annotated_image_path = Column(String(255), nullable=True)
    
    total_bunches = Column(Integer, default=0)
    count_unripe = Column(Integer, default=0)
    count_underripe = Column(Integer, default=0)
    count_ripe = Column(Integer, default=0)
    count_overripe = Column(Integer, default=0)
    count_long_stalk = Column(Integer, default=0)
    
    inference_latency_ms = Column(Float, default=0.0)
    model_version = Column(String(100), default="YOLOv8n-IOPRI-v1")
    notes = Column(Text, nullable=True)
    graded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    delivery_order = relationship("DeliveryOrder", back_populates="grading_sessions")
    detections = relationship("DetectionItem", back_populates="grading_session", cascade="all, delete-orphan")
    oer_assessment = relationship("OERAssessment", back_populates="grading_session", uselist=False, cascade="all, delete-orphan")


class DetectionItem(Base):
    __tablename__ = "detection_items"

    id = Column(Integer, primary_key=True, index=True)
    grading_session_id = Column(Integer, ForeignKey("grading_sessions.id"), nullable=False)
    class_name = Column(String(50), nullable=False)  # unripe, underripe, ripe, overripe
    confidence = Column(Float, nullable=False)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)

    # Relationships
    grading_session = relationship("GradingSession", back_populates="detections")


class OERAssessment(Base):
    __tablename__ = "oer_assessments"

    id = Column(Integer, primary_key=True, index=True)
    grading_session_id = Column(Integer, ForeignKey("grading_sessions.id"), unique=True, nullable=False)
    
    estimated_oer_percentage = Column(Float, nullable=False)
    baseline_oer_percentage = Column(Float, default=21.5)
    oer_variance = Column(Float, default=0.0)
    quality_score = Column(Float, default=1.0)
    
    price_per_kg_base = Column(Float, default=2850.0)
    price_penalty_percentage = Column(Float, default=0.0)
    stalk_penalty_percentage = Column(Float, default=0.0)
    effective_net_weight_kg = Column(Float, nullable=True)
    final_price_per_kg = Column(Float, default=2850.0)
    total_payout = Column(Float, default=0.0)
    ffa_risk_category = Column(String(50), default="LOW")  # LOW, MEDIUM, HIGH
    calculated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    grading_session = relationship("GradingSession", back_populates="oer_assessment")
