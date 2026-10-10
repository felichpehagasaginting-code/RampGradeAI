from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import random

from backend.app.core.database import get_db
from backend.app.models.entities import DeliveryOrder, Farmer, PlantationBlock
from backend.app.schemas.schemas import DeliveryOrderCreate, DeliveryOrderResponse

router = APIRouter(prefix="/delivery-orders", tags=["Delivery Orders (SPB / Tiket Timbang)"])

@router.get("/", response_model=List[DeliveryOrderResponse])
def get_delivery_orders(status: str = None, db: Session = Depends(get_db)):
    query = db.query(DeliveryOrder)
    if status:
        query = query.filter(DeliveryOrder.status == status)
    return query.order_by(DeliveryOrder.arrival_time.desc()).all()

@router.post("/", response_model=DeliveryOrderResponse)
def create_delivery_order(payload: DeliveryOrderCreate, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.id == payload.farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Data Petani tidak ditemukan")

    block = db.query(PlantationBlock).filter(PlantationBlock.id == payload.block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Data Blok Kebun tidak ditemukan")

    now = datetime.now()
    spb_number = f"SPB-{now.strftime('%Y%m%d')}-{random.randint(100, 999)}"
    
    order = DeliveryOrder(
        spb_number=spb_number,
        farmer_id=payload.farmer_id,
        block_id=payload.block_id,
        truck_plate_number=payload.truck_plate_number.upper(),
        driver_name=payload.driver_name,
        net_weight_kg=payload.net_weight_kg,
        status="PENDING_GRADING"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.get("/{spb_number}", response_model=DeliveryOrderResponse)
def get_delivery_order_by_spb(spb_number: str, db: Session = Depends(get_db)):
    order = db.query(DeliveryOrder).filter(DeliveryOrder.spb_number == spb_number).first()
    if not order:
        raise HTTPException(status_code=404, detail="Nomor tiket SPB tidak ditemukan")
    return order
