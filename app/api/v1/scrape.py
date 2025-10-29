from fastapi import APIRouter, BackgroundTasks, HTTPException, Form
from app.models.schemas import ScrapeRequest, ScrapeResponse
from app.services import tasks
from app.services.task_manager import task_manager
from typing import Dict
import logging
from pathlib import Path


logger = logging.getLogger("weibospider_app.api.scrape")
router = APIRouter()

@router.post("/scrape", response_model=ScrapeResponse)
async def scrape(req: ScrapeRequest):
    """提交爬虫任务"""
    logger.info("Received scrape request: %s", req.json())
    mode = req.mode.lower()
    spider_name = None
    spider_args: Dict[str, str] = {}
    spider_args["platform"] = req.platform.lower()
    spider_args["output_dir"] = req.output_dir if req.output_dir else ""
    
    if mode == "keyword":
        if not req.keyword:
            raise HTTPException(status_code=400, detail="keyword required for mode=keyword")
        spider_name = "tweet_by_keyword"
        spider_args["keyword"] = req.keyword
        if req.start_date:
            spider_args["start_date"] = req.start_date
        if req.end_date:
            spider_args["end_date"] = req.end_date
        if req.max_pages:
            spider_args["max_pages"] = str(req.max_pages)
    elif mode == "tweet":
        if not req.tweet_id:
            raise HTTPException(status_code=400, detail="tweet_id required for mode=tweet")
        spider_name = "tweet_by_tweet_id"
        spider_args["tweet_id"] = req.tweet_id
    elif mode == "user":
        if not req.user_id:
            raise HTTPException(status_code=400, detail="user_id required for mode=user")
        spider_name = "tweet_by_user_id"
        spider_args["user_id"] = req.user_id
        if req.start_date:
            spider_args["start_date"] = req.start_date
        if req.end_date:
            spider_args["end_date"] = req.end_date
        if req.max_pages:
            spider_args["max_pages"] = str(req.max_pages)
    else:
        raise HTTPException(status_code=400, detail="mode must be one of: keyword, tweet, user")

    # 启动任务并返回任务ID
    task_id = tasks.crawl_and_store(spider_name, spider_args)
    
    return {
        "status": "submitted", 
        "task_id": task_id,
        "inserted": 0, 
        "output_file": None, 
        "error": None
    }

@router.post("/stop/{task_id}")
async def stop_task(task_id: str):
    """停止指定任务"""
    success = task_manager.stop_task(task_id)
    if success:
        return {"status": "stop_signal_sent", "task_id": task_id}
    else:
        raise HTTPException(status_code=404, detail="Task not found or already finished")

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    task = task_manager.get_task_status(task_id)
    if task:
        return task
    else:
        raise HTTPException(status_code=404, detail="Task not found")

@router.get("/tasks")
async def list_tasks():
    """列出所有任务"""
    return {"tasks": task_manager.list_tasks()}




@router.post("/upload_cookie")
async def upload_cookie(platform: str = Form(...), cookie: str = Form(...)):
    """上传 cookie 字符串并根据 platform 覆盖本地 cookie 文件"""
    logger.info("Received cookie upload for platform: %s cookie_size: %d", platform, len(cookie) if cookie is not None else 0)
    platform_key = platform.lower()

    # 映射 platform 到本地 cookie 文件路径 —— 根据需要调整路径
    project_root = Path(__file__).resolve().parents[3]  # WeiboSpider-backend 根目录
    target_paths = {
        "weibo": project_root / "weibospider" / "cookie.txt",
        # "other": Path("...")  # 如果有其他平台，可在此添加
    }

    if platform_key not in target_paths:
        raise HTTPException(status_code=400, detail=f"unsupported platform: {platform}")

    target_path = target_paths[platform_key]

    try:
        # cookie is a string from the form. Encode to bytes for writing.
        content = cookie.encode("utf-8")
        # 备份旧文件（可选）
        # if target_path.exists():
        #     backup_path = target_path.with_suffix(".cookie.bak")
        #     try:
        #         target_path.replace(backup_path)
        #         logger.info("Backed up existing cookie to %s", backup_path)
        #     except Exception:
        #         # 如果替换备份失败，忽略继续写入
        #         logger.exception("Failed to backup existing cookie")

        # 写入新的 cookie 内容（以二进制写入以兼容不同编码）
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(content)

        logger.info("Wrote cookie file to %s", target_path)
        return {"status": "ok", "platform": platform_key, "path": str(target_path)}
    except Exception as e:
        logger.exception("Failed to write cookie file")
        raise HTTPException(status_code=500, detail="failed to save cookie file")
