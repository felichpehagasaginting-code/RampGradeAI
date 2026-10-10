from fastapi import APIRouter
from backend.app.api.v1.farmers import router as farmers_router
from backend.app.api.v1.blocks import router as blocks_router
from backend.app.api.v1.delivery_orders import router as delivery_orders_router
from backend.app.api.v1.grading import router as grading_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.websocket_stream import router as ws_router
from backend.app.api.v1.active_learning_router import router as active_learning_router

api_router = APIRouter()
api_router.include_router(farmers_router)
api_router.include_router(blocks_router)
api_router.include_router(delivery_orders_router)
api_router.include_router(grading_router)
api_router.include_router(analytics_router)
api_router.include_router(ws_router)
api_router.include_router(active_learning_router)
