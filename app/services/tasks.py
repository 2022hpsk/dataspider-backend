from typing import Dict
from app.services.task_manager import task_manager

def crawl_and_store(spider_name: str, spider_args: Dict[str, str]) -> str:
    """启动爬虫任务，返回任务ID"""
    task_id = task_manager.start_crawl_task(spider_name, spider_args)
    return task_id