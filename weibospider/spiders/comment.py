import json
from scrapy import Spider
from scrapy.http import Request
from spiders.common import parse_user_info, parse_time, url_to_mid
import pandas as pd



class CommentSpider(Spider):
    """
    微博评论数据采集
    """
    name = "comment"
    def start_requests(self):
        """
        爬虫入口
        """
        # 这里tweet_ids 从csv文件中读取
        df = pd.read_csv('../tweet_ids.csv', header=None)
        tweet_ids = df[0].tolist()
        for tweet_id in tweet_ids:
            mid = url_to_mid(tweet_id)
            print(mid)
            url = f"https://weibo.com/ajax/statuses/buildComments?" \
                  f"is_reload=1&id={mid}&is_show_bulletin=2&is_mix=0&count=20"
            yield Request(url, callback=self.parse, meta={'source_url': url,'processed': 0, 'tweet_id': tweet_id})

    def parse(self, response, **kwargs):
        """
        网页解析
        """
        data = json.loads(response.text)
        #如果data['data']为空，说明需要更换url的is_show_bulletin参数为0,重新请求
        if not data['data']:
            url = response.meta['source_url'].replace('is_show_bulletin=2', 'is_show_bulletin=0')
            response.meta['source_url'] = url
            yield Request(url, callback=self.parse, meta=response.meta)
            return
        for comment_info in data['data']:
            item = self.parse_comment(comment_info, response.meta['tweet_id'])
            yield item
            # 解析二级评论
            if 'more_info' in comment_info:
                url = f"https://weibo.com/ajax/statuses/buildComments?is_reload=1&id={comment_info['id']}" \
                      f"&is_show_bulletin=2&is_mix=1&fetch_level=1&max_id=0&count=20"
                yield Request(url, callback=self.parse, priority=20, meta={'source_url': url, 'processed': 0, 'tweet_id': response.meta['tweet_id']})
        if data.get('max_id', 0) != 0 and 'fetch_level=1' not in response.url:
            url = response.meta['source_url'] + '&max_id=' + str(data['max_id'])
            print('!!!!!!!!!!!!here, url:', url)
            response.meta['processed'] += 1
            yield Request(url, callback=self.parse, meta=response.meta)

    # @staticmethod
    def parse_comment(self,data, tweet_id):
        """
        解析comment
        """
        item = dict()
        item['tweet_id'] = tweet_id
        item['parent_comment_id'] = data['rootid']
        item['created_at'] = parse_time(data['created_at'])
        item['_id'] = data['id']
        item['like_counts'] = data['like_counts']
        item['ip_location'] = data.get('source', '')
        item['content'] = data['text_raw']
        item['comment_user'] = parse_user_info(data['user'])
        if 'reply_comment' in data:
            item['reply_comment'] = {
                '_id': data['reply_comment']['id'],
                'text': data['reply_comment']['text'],
                'user': parse_user_info(data['reply_comment']['user']),
            }
        return item
