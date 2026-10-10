from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import random

from backend.app.core.database import get_db
from backend.app.models.entities import Farmer
from backend.app.schemas.schemas import FarmerCreate, FarmerResponse

router = APIRouter(prefix="/farmers", tags=["Farmers (Pekebun)"])

@router.get("/", response_model=List[FarmerResponse])
def get_farmers(
    skip: int = 0,
    limit: int = 100,
    certification: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Farmer)
    if certification:
        query = query.filter(Farmer.certification_status == certification)
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=FarmerResponse)
def create_farmer(payload: FarmerCreate, db: Session = Depends(get_db)):
    code = f"FMR-{datetime.now().year}-{random.randint(1000, 9999)}"
    farmer = Farmer(
        farmer_code=code,
        name=payload.name,
        nik=payload.nik,
        phone_number=payload.phone_number,
        cooperative_name=payload.cooperative_name,
        certification_status=payload.certification_status
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return farmer

@router.get("/{farmer_id}", response_model=FarmerResponse)
def get_farmer_detail(farmer_id: int, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Petani tidak ditemukan")
    return farmer
