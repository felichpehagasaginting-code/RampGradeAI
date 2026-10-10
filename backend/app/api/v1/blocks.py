from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import random

from backend.app.core.database import get_db
from backend.app.models.entities import PlantationBlock, Farmer
from backend.app.schemas.schemas import BlockCreate, BlockResponse

router = APIRouter(prefix="/blocks", tags=["Plantation Blocks (Blok Kebun)"])

@router.get("/", response_model=List[BlockResponse])
def get_blocks(farmer_id: int = None, db: Session = Depends(get_db)):
    query = db.query(PlantationBlock)
    if farmer_id:
        query = query.filter(PlantationBlock.farmer_id == farmer_id)
    return query.all()

@router.post("/", response_model=BlockResponse)
def create_block(payload: BlockCreate, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.id == payload.farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Petani pemilik blok tidak ditemukan")

    block_code = f"BLK-{payload.farmer_id}-{random.randint(100, 999)}"
    block = PlantationBlock(
        farmer_id=payload.farmer_id,
        block_code=block_code,
        area_hectares=payload.area_hectares,
        latitude=payload.latitude,
        longitude=payload.longitude,
        planting_year=payload.planting_year,
        variety=payload.variety,
        legal_status=payload.legal_status
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block
