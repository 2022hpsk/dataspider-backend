
import json
from scrapy import Spider
from scrapy.http import Request
from spiders.common import parse_user_info
import pandas as pd
import os

def extract_user_ids_from_jsonl(file_path):
    user_ids = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            data = json.loads(line)
            user_id = data.get('user', {}).get('_id')
            if user_id:
                user_ids.append(user_id)
    return user_ids

class UserSpider(Spider):
    """
    微博用户信息爬虫
    """
    name = "user_spider"
    base_url = "https://weibo.cn"

    def start_requests(self):
        """
        爬虫入口
        """
        # 这里user_ids可替换成实际待采集的数据
        # Tip：步骤5中可以调用extract_user_ids_from_jsonl，获取user_ids
        # print(os.getcwd())
        # user_ids = extract_user_ids_from_jsonl('../output/tweet_spider_by_keyword_20240319202354.jsonl')
        # print(user_ids)
        
  
        df = pd.read_csv('../user_ids.csv', header=None)
        user_ids = df[0].tolist()
        # 读取文件内容到列表
        # with open('最初的数据需求设计/user_ids.txt', 'r', encoding='utf-8') as file:
        #     user_ids = file.read().splitlines()
        urls = [f'https://weibo.com/ajax/profile/info?uid={user_id}' for user_id in user_ids]
        for url in urls:
            yield Request(url, callback=self.parse)

    def parse(self, response, **kwargs):
        """
        网页解析
        """
        data = json.loads(response.text)
        item = parse_user_info(data['data']['user'])
        url = f"https://weibo.com/ajax/profile/detail?uid={item['_id']}"
        yield Request(url, callback=self.parse_detail, meta={'item': item})

    @staticmethod
    def parse_detail(response):
        """
        解析详细数据
        """
        item = response.meta['item']
        data = json.loads(response.text)['data']
        item['birthday'] = data.get('birthday', '')
        if 'created_at' not in item:
            item['created_at'] = data.get('created_at', '')
        item['desc_text'] = data.get('desc_text', '')
        item['ip_location'] = data.get('ip_location', '')
        item['sunshine_credit'] = data.get('sunshine_credit', {}).get('level', '')
        item['label_desc'] = [label['name'] for label in data.get('label_desc', [])]
        if 'company' in data:
            item['company'] = data['company']
        if 'education' in data:
            item['education'] = data['education']
        yield item
