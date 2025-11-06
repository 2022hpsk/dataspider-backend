# -*- coding: utf-8 -*-
import datetime
import json
import os.path
import time
from scrapy.utils.project import get_project_settings


class JsonWriterPipeline(object):
    """
    写入json文件的pipline
    """
    def __init__(self):
        self.file = None
        self.output_dir = 'output'
        if os.path.exists('output.txt'):
            with open('output.txt', 'r', encoding='utf-8') as f:
                self.output_dir = f.read().strip()
        if not os.path.exists( self.output_dir):
            os.makedirs(self.output_dir)

    def process_item(self, item, spider):
        """
        处理item
        """
        if not self.file:
            now = datetime.datetime.now()
            file_name = spider.name + "_" + now.strftime("%Y%m%d%H%M%S") + '.jsonl'
            self.file = open(os.path.join(self.output_dir, file_name), 'wt', encoding='utf-8')
        item['crawl_time'] = int(time.time())
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        self.file.flush()
        return item
