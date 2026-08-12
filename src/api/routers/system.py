from fastapi import APIRouter
from src.core.config import settings

router = APIRouter(tags=["System"])

@router.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}\n