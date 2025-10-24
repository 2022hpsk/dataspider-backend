from pydantic import BaseModel, Field
from typing import Optional

class ScrapeRequest(BaseModel):
    mode: str = Field(..., description="爬取类型: keyword | tweet | user")
    platform: str = Field("weibo", description="平台，默认为 weibo")
    keyword: Optional[str] = None
    tweet_id: Optional[str] = None
    user_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_pages: Optional[int] = 0
    output_dir: Optional[str] = None

class ScrapeResponse(BaseModel):
    status: str
    task_id: Optional[str] = None  # 新增任务ID字段
    inserted: int = 0
    output_file: Optional[str] = None
    error: Optional[str] = None