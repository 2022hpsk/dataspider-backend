from fastapi import APIRouter
from .scrape import router as scrape_router

router = APIRouter()
router.include_router(scrape_router, prefix="", tags=["scrape"])

__all__ = ["router"]