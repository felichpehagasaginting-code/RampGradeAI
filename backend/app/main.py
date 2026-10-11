from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, SessionLocal
from backend.app.models.entities import Farmer, PlantationBlock, DeliveryOrder
from backend.app.api.v1.router import api_router

# Inisialisasi Tabel Basis Data
Base.metadata.create_all(bind=engine)

def seed_initial_data():
    """Mengisi data awal untuk simulasi traceability jika database masih kosong."""
    db = SessionLocal()
    try:
        if db.query(Farmer).count() == 0:
            farmer1 = Farmer(
                farmer_code="FMR-2026-0012",
                name="Kelompok Tani Sawit Mandiri (Bpk. Joko Supriyanto)",
                nik="1401021980050001",
                phone_number="081267891234",
                cooperative_name="KUD Sawit Sejahtera Riau",
                certification_status="RSPO"
            )
            farmer2 = Farmer(
                farmer_code="FMR-2026-0045",
                name="Pekebun Swadaya Bpk. Herman Nasution",
                nik="1402031975100003",
                phone_number="081398765432",
                cooperative_name="Asosiasi Petani Sawit Berkelanjutan",
                certification_status="ISPO"
            )
            db.add_all([farmer1, farmer2])
            db.flush()

            block1 = PlantationBlock(
                farmer_id=farmer1.id,
                block_code="BLK-RIAU-04A",
                area_hectares=4.5,
                latitude=0.5386,
                longitude=101.4485,
                planting_year=2016,
                variety="DxP Marihat",
                legal_status="SHM",
                boundary_geojson='[[101.4465, 0.5372], [101.4505, 0.5372], [101.4510, 0.5402], [101.4470, 0.5405], [101.4465, 0.5372]]',
                eudr_compliant="VERIFIED",
                deforestation_cutoff_date="2020-12-31"
            )
            block2 = PlantationBlock(
                farmer_id=farmer2.id,
                block_code="BLK-RIAU-02B",
                area_hectares=2.8,
                latitude=0.5412,
                longitude=101.4521,
                planting_year=2018,
                variety="Yangambi",
                legal_status="Girik",
                boundary_geojson='[[101.4508, 0.5401], [101.4535, 0.5401], [101.4538, 0.5425], [101.4511, 0.5426], [101.4508, 0.5401]]',
                eudr_compliant="VERIFIED",
                deforestation_cutoff_date="2020-12-31"
            )
            db.add_all([block1, block2])
            db.flush()

            order1 = DeliveryOrder(
                spb_number="SPB-20261008-001",
                farmer_id=farmer1.id,
                block_id=block1.id,
                truck_plate_number="BM 8421 AU",
                driver_name="Samsul Bahri",
                net_weight_kg=6840.0,
                status="PENDING_GRADING"
            )
            db.add(order1)
            db.commit()
            print("[Database] Seed data initial traceability berhasil ditambahkan.")
    except Exception as e:
        db.rollback()
        print(f"[Database] Error saat seeding: {e}")
    finally:
        db.close()

seed_initial_data()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API SMART GRADE - Deteksi Kematangan TBS & Traceability Berbasis YOLOv8 & IOPRI 1997"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_exceptions_middleware(request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        traceback.print_exc()
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"detail": str(e), "traceback": traceback.format_exc()})

# Mount Static Files untuk Akses Hasil Citra & Anotasi
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount Frontend SPA if built
frontend_dist = settings.ROOT_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

@app.get("/health")
def health():
    return {
        "system": settings.PROJECT_NAME,
        "status": "online",
        "version": settings.VERSION,
        "institution": "Politeknik Citra Widya Edukasi (PCWE)",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }

@app.get("/")
def root():
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        from fastapi.responses import FileResponse
        return FileResponse(index_file)
    return health()


