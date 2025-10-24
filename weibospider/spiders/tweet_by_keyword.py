# import datetime
# import json
# import re
# from scrapy import Spider, Request
# from spiders.common import parse_tweet_info, parse_long_tweet


# class TweetSpiderByKeyword(Spider):
#     """
#     关键词搜索采集
#     """
#     name = "tweet_spider_by_keyword"
#     base_url = "https://s.weibo.com/"

#     def start_requests(self):
#         """
#         爬虫入口
#         """
#         # 这里keywords可替换成实际待采集的数据
#         keywords = ["洛杉矶 中国省"]
#         # 这里的时间可替换成实际需要的时间段
#         start_time = datetime.datetime(year=2025, month=3, day=1, hour=0)
#         end_time = datetime.datetime(year=2025, month=3, day=15, hour=0)
#         # 是否按照小时进行切分，数据量更大; 对于非热门关键词**不需要**按照小时切分
#         is_split_by_month = False
#         for keyword in keywords:
#             if not is_split_by_month:
#                 _start_time = start_time.strftime("%Y-%m-%d-%H")
#                 _end_time = end_time.strftime("%Y-%m-%d-%H")
#                 # url = f"https://s.weibo.com/weibo?q={keyword}&timescope=custom%3A{_start_time}%3A{_end_time}&page=1" #增加热门功能！！&xsort=hot&suball=1
#                 # url = f"https://s.weibo.com/realtime?q={keyword}&rd=realtime&tw=realtime&Refer=weibo_realtime"
#                 url = f"https://s.weibo.com/weibo?q={keyword}"
#                 # url = f"https://s.weibo.com/realtime?q={keyword}&Refer=weibo_weibo"                
#                 yield Request(url, callback=self.parse, meta={'keyword': keyword})
#             else:
#                 time_cur = start_time
#                 while time_cur < end_time:
#                     _start_time = time_cur.strftime("%Y-%m-%d-%H")
#                     _end_time = (time_cur + datetime.timedelta(days=30)).strftime("%Y-%m-%d-%H")
#                     url = f"https://s.weibo.com/weibo?q={keyword}&timescope=custom%3A{_start_time}%3A{_end_time}&page=1"#增加热门功能！！&xsort=hot&suball=1
#                     yield Request(url, callback=self.parse, meta={'keyword': keyword,"page_num": 0})
#                     time_cur = time_cur + datetime.timedelta(days=30)

#     def parse(self, response, **kwargs):
#         """
#         网页解析
#         """
#         html = response.text
#         if '<p>抱歉，未找到相关结果。</p>' in html:
#             self.logger.info(f'no search result. url: {response.url}')
#             return
#         tweets_infos = re.findall('<div class="from"\s+>(.*?)</div>', html, re.DOTALL)
#         for tweets_info in tweets_infos:
#             tweet_ids = re.findall(r'weibo\.com/\d+/(.+?)\?refer_flag=1001030103_" ', tweets_info)
#             for tweet_id in tweet_ids:
#                 url = f"https://weibo.com/ajax/statuses/show?id={tweet_id}"
#                 yield Request(url, callback=self.parse_tweet, meta=response.meta, priority=10)
#         next_page = re.search('<a href="(.*?)" class="next">下一页</a>', html)
#         if next_page:
#             if response.meta.get("page_num",0) > 50:
#                 return
#             else :
#                 response.meta["page_num"] = response.meta.get("page_num", 0) + 1
#             url = "https://s.weibo.com" + next_page.group(1)
#             print("!!!!!!!!!!!next_page:",url)
#             yield Request(url, callback=self.parse, meta=response.meta)

#     @staticmethod
#     def parse_tweet(response):
#         """
#         解析推文
#         """
#         data = json.loads(response.text)
#         item = parse_tweet_info(data)
#         item['keyword'] = response.meta['keyword']
#         if item['isLongText']:
#             url = "https://weibo.com/ajax/statuses/longtext?id=" + item['mblogid']
#             yield Request(url, callback=parse_long_tweet, meta={'item': item}, priority=20)
#         else:
#             yield item
import datetime
import json
import re
import os
from scrapy import Spider, Request
from spiders.common import parse_tweet_info, parse_long_tweet

class TweetSpiderByKeyword(Spider):
    """
    关键词搜索采集，支持通过构造参数传入:
      keyword (str or list), start_date (ISO string), end_date (ISO string), max_pages (int), is_split_by_month (bool)
    """
    name = "tweet_spider_by_keyword"
    base_url = "https://s.weibo.com/"

    def __init__(self, keyword=None, start_date=None, end_date=None, max_pages=None, is_split_by_month=False, *args, **kwargs):
        print("TweetSpiderByKeyword init:", keyword, start_date, end_date, max_pages, is_split_by_month)
        super().__init__(*args, **kwargs)
        # support list or comma-separated string
        if isinstance(keyword, list):
            self.keywords = keyword
        elif isinstance(keyword, str) and keyword:
            self.keywords = [k.strip() for k in keyword.split(",") if k.strip()]
        else:
            self.keywords = ["默认关键词"]# 默认关键词
        # parse dates if provided
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
        self.start_time = parse_dt(start_date) or datetime.datetime(year=2025, month=3, day=1, hour=0)
        self.end_time = parse_dt(end_date) or datetime.datetime(year=2025, month=3, day=15, hour=0)
        self.max_pages = int(max_pages) if max_pages not in (None, "") else 0
        self.is_split_by_month = str(is_split_by_month).lower() in ("1", "true", "yes")

    def start_requests(self):
        print("TweetSpiderByKeyword start_requests:", self.keywords, self.start_time, self.end_time, self.max_pages, self.is_split_by_month)
        for keyword in self.keywords:
            if not self.is_split_by_month:
                print("TweetSpiderByKeyword start_requests single:", keyword)
                url = f"https://s.weibo.com/weibo?q={keyword}"
                yield Request(url, callback=self.parse, meta={'keyword': keyword, 'page_num': 1})
            else:
                time_cur = self.start_time
                while time_cur < self.end_time:
                    _start_time = time_cur.strftime("%Y-%m-%d-%H")
                    _end_time = (time_cur + datetime.timedelta(days=30)).strftime("%Y-%m-%d-%H")
                    url = f"https://s.weibo.com/weibo?q={keyword}&timescope=custom%3A{_start_time}%3A{_end_time}&page=1"
                    yield Request(url, callback=self.parse, meta={'keyword': keyword, "page_num": 1})
                    time_cur = time_cur + datetime.timedelta(days=30)

    def parse(self, response, **kwargs):
        print("TweetSpiderByKeyword parse:", response.url)
        html = response.text
        if '<p>抱歉，未找到相关结果。</p>' in html:
            self.logger.info(f'no search result. url: {response.url}')
            return
        tweets_infos = re.findall('<div class="from"\s+>(.*?)</div>', html, re.DOTALL)
        for tweets_info in tweets_infos:
            tweet_ids = re.findall(r'weibo\.com/\d+/(.+?)\?refer_flag=1001030103_" ', tweets_info)
            for tweet_id in tweet_ids:
                url = f"https://weibo.com/ajax/statuses/show?id={tweet_id}"
                yield Request(url, callback=self.parse_tweet, meta=response.meta, priority=10)
        next_page = re.search('<a href="(.*?)" class="next">下一页</a>', html)
        if next_page:
            page_num = response.meta.get("page_num", 1)
            if self.max_pages and page_num >= self.max_pages:
                return
            response.meta["page_num"] = page_num + 1
            url = "https://s.weibo.com" + next_page.group(1)
            yield Request(url, callback=self.parse, meta=response.meta)

    @staticmethod
    def parse_tweet(response):
        data = json.loads(response.text)
        item = parse_tweet_info(data)
        item['keyword'] = response.meta.get('keyword')
        if item.get('isLongText'):
            url = "https://weibo.com/ajax/statuses/longtext?id=" + item['mblogid']
            yield Request(url, callback=parse_long_tweet, meta={'item': item}, priority=20)
        else:
            yield item