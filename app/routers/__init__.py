from app.routers.patients import router as patients_router
from app.routers.stats import router as stats_router
from app.routers.vapi import router as vapi_router

__all__ = ["patients_router", "stats_router", "vapi_router"]
