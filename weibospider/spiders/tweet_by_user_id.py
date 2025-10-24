# ...existing code...
import datetime
import json
import re

from scrapy import Spider
from scrapy.http import Request
from spiders.common import parse_tweet_info, parse_long_tweet


class TweetSpiderByUserID(Spider):
    """
    用户推文数据采集
    """
    name = "tweet_spider_by_user_id"

    def __init__(self, user_id=None, start_date=None, end_date=None, max_pages=None, step_days=10, *args, **kwargs):
        """
        参数:
          - user_id: str(逗号分隔) 或 list，例如 "123,456" 或 ["123","456"]
          - start_date/end_date: ISO 字符串或 YYYY-MM-DD，例如 "2025-01-01" 或 "2025-01-01T00:00:00"
          - max_pages: 每个时间窗口内的最大翻页数（可选）
          - step_days: 时间窗口跨度天数（默认 10 天）
        """
        super().__init__(*args, **kwargs)

        # user_id 支持 list 或 逗号分隔字符串
        if isinstance(user_id, list):
            self.user_ids = [str(u).strip() for u in user_id if str(u).strip()]
        elif isinstance(user_id, str) and user_id.strip():
            self.user_ids = [u.strip() for u in user_id.split(",") if u.strip()]
        else:
            # 未传递则默认空列表，不会发起请求
            self.user_ids = []

        def parse_dt(v):
            if not v:
                return None
            try:
                return datetime.datetime.fromisoformat(v)
            except Exception:
                try:
                    return datetime.datetime.strptime(v, "%Y-%m-%d")
                except Exception:
                    return None

        self.start_time = parse_dt(start_date)
        self.end_time = parse_dt(end_date)
        self.max_pages = int(max_pages) if max_pages not in (None, "") else 0
        try:
            self.step_days = int(step_days) if step_days not in (None, "") else 10
        except Exception:
            self.step_days = 10

    def start_requests(self):
        """
        爬虫入口
        """
        if not self.user_ids:
            self.logger.warning("No user_id provided. Use -a user_id=123 or -a user_id=123,456")
            return

        for uid in self.user_ids:
            base = (
                f"https://weibo.com/ajax/statuses/searchProfile?"
                f"uid={uid}&page=1&hasori=1&hastext=1&haspic=1&hasvideo=1&hasmusic=1&hasret=1"
            )

            # 若同时提供了 start_date 和 end_date，则按 step_days 切片抓取；否则抓取全部
            if self.start_time and self.end_time and self.start_time <= self.end_time:
                tmp_start = self.start_time
                while tmp_start <= self.end_time:
                    tmp_end = min(tmp_start + datetime.timedelta(days=self.step_days), self.end_time)
                    url = (
                        base
                        + f"&starttime={int(tmp_start.timestamp())}"
                        + f"&endtime={int(tmp_end.timestamp())}"
                    )
                    yield Request(url, callback=self.parse, meta={"user_id": uid, "page_num": 1})
                    tmp_start = tmp_end + datetime.timedelta(days=1)
            else:
                yield Request(base, callback=self.parse, meta={"user_id": uid, "page_num": 1})

    def parse(self, response, **kwargs):
        """
        网页解析
        """
        data = json.loads(response.text)
        tweets = data.get("data", {}).get("list", []) or []
        for tweet in tweets:
            item = parse_tweet_info(tweet)
            item["user_id"] = item["user"]["_id"]
            del item["user"]
            if item.get("isLongText"):
                url = "https://weibo.com/ajax/statuses/longtext?id=" + item["mblogid"]
                yield Request(url, callback=parse_long_tweet, meta={"item": item})
            else:
                yield item

        # 翻页
        if tweets:
            user_id = response.meta["user_id"]
            page_num = response.meta.get("page_num", 1)

            # 若设置了 max_pages，达到上限则停止
            if self.max_pages and page_num >= self.max_pages:
                return

            next_url = response.url.replace(f"page={page_num}", f"page={page_num + 1}")
            yield Request(next_url, callback=self.parse, meta={"user_id": user_id, "page_num": page_num + 1})
# ...existing code...