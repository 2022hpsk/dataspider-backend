# 文件名: app\api\routes.py
# filepath: c:\Users\lenovo\Desktop\datacrawl\backend\WeiboSpider-backend\app\api\routes.py
from fastapi import APIRouter
from app.api.v1 import scrape

router = APIRouter()
router.include_router(scrape.router, prefix="/v1", tags=["v1"])