from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

from .platforms import Platform


class Post(BaseModel):
    class PostType(str, Enum):
        post = "post"
        retweet = "retweet"
        comment = "comment"

    class Source(BaseModel):
        platform: Platform = Field(..., description="帖子来源平台")
        engine: str = Field(..., description="帖子数据引擎")
        url: Optional[str] = Field(None, description="帖子url")  # 小红书commenturl为空
        post_id: str = Field(..., description="帖子在平台中的唯一id")
        parent_id: Optional[str] = Field(None, description="父亲贴id")

    class Content(BaseModel):
        raw_text: str = Field(..., description="原始文本")
        at_users: List[str] = Field(default_factory=list, description="帖子中@的用户")
        tags: List[str] = Field(default_factory=list, description="帖子中的#标签")
        urls: List[str] = Field(default_factory=list, description="帖子中的链接")
        images: List[str] = Field(default_factory=list, description="帖子中的图片")
        videos: List[str] = Field(default_factory=list, description="帖子中的视频")

    class Sender(BaseModel):
        class Location(BaseModel):
            class GPS(BaseModel):
                lat: float = Field(..., ge=-90, le=90, description="经度")
                lon: float = Field(..., ge=-180, le=180, description="纬度")

            gps: Optional[GPS] = Field(None, description="帖子GPS信息")
            city: Optional[str] = Field(None, description="帖子城市信息")
            country: Optional[str] = Field(None, description="帖子国家信息")

        user_id: str = Field(..., description="发帖用户在平台的唯一id")
        send_time: Optional[datetime] = Field(
            None, description="发帖时间"
        )  # twitter转发时没有
        location: Location = Field(default_factory=Location, description="发帖位置信息")

    class StatisticsItem(BaseModel):
        cnt_view: int = Field(-1, description="浏览数")
        cnt_like: int = Field(-1, description="点赞数")
        cnt_comment: int = Field(-1, description="评论数")
        cnt_share: int = Field(-1, description="分享数")
        cnt_collect: int = Field(-1, description="收藏数")

    id: str = Field(..., description="数据库存储唯一id")
    type: PostType = Field(..., description="帖子类型")
    source: Source = Field(default_factory=Source, description="帖子来源")
    content: Content = Field(default_factory=Content, description="帖子内容")
    sender: Sender = Field(default_factory=Sender, description="发帖人信息")
    statistics: StatisticsItem = Field(
        default_factory=StatisticsItem, description="帖子统计信息"
    )
    extra_field: Optional[str] = Field(None, description="扩展字段")
