from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal

from models import Platform


class Account(BaseModel):
    class Source(BaseModel):
        platform: Platform = Field(..., description="账户平台")
        engine: str = Field(..., description="数据引擎")
        user_id: str = Field(..., description="账户平台唯一id")

    class Location(BaseModel):
        net_ip: Optional[str] = Field(None, description="ip地址")
        city: Optional[str] = Field(None, description="城市")
        country: Optional[str] = Field(None, description="国家")
        address_text: Optional[str] = Field(None, description="未结构化的地址信息")

    class Statistics(BaseModel):
        cnt_following: int = Field(-1, description="关注数")
        cnt_follower: int = Field(-1, description="粉丝数")
        cnt_posts: int = Field(-1, description="发帖数")

    id: str = Field(..., description="数据库存储唯一id")
    source: Source = Field(default_factory=Source, description="来源")
    user_name: str = Field(..., description="昵称")
    location: Location = Field(default_factory=Location, description="账号位置信息")

    homepage: str = Field(..., description="主页url")
    avatar: Optional[str] = Field(None, description="头像url")
    intro: Optional[str] = Field(None, description="简介")
    tags: list[str] = Field(default_factory=list, description="标签")
    gender: Optional[Literal["male", "female", "other"]] = Field(
        None, description="性别"
    )
    birthyear: Optional[int] = Field(None, description="生日年份")
    register_time: Optional[datetime] = Field(None, description="注册时间")
    qualification: list[str] = Field(default_factory=list, description="官方认证信息")
    statistics: Statistics = Field(
        default_factory=Statistics, description="统计发帖、粉丝、关注信息"
    )
    extra_field: Optional[str] = Field(None, description="扩展字段")
