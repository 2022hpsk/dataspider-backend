# 文件名: app\main.py
# filepath: c:\Users\lenovo\Desktop\datacrawl\backend\WeiboSpider-backend\app\main.py
from fastapi import FastAPI
from app.api import routes
import logging
import sys
from fastapi.middleware.cors import CORSMiddleware

# 配置根日志，uvicorn 会使用这些配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("weibospider_app")

def create_app():
    app = FastAPI(title="WeiboSpider Backend")
    app.include_router(routes.router, prefix="/api")
    # 允许所有来源跨域（开发环境用，生产请限制 origins）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app

app = create_app()

#python -u -m uvicorn app.main:app --host 0.0.0.0 --port 8000