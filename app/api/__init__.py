from fastapi import APIRouter

router = APIRouter()

from .v1 import scrape

router.include_router(scrape.router, prefix="/v1", tags=["scrape"])