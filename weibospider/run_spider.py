
# import os
# import sys
# from scrapy.crawler import CrawlerProcess
# from scrapy.utils.project import get_project_settings
# from spiders.tweet_by_user_id import TweetSpiderByUserID
# from spiders.tweet_by_keyword import TweetSpiderByKeyword
# from spiders.tweet_by_tweet_id import TweetSpiderByTweetID
# from spiders.comment import CommentSpider
# from spiders.follower import FollowerSpider
# from spiders.user import UserSpider
# from spiders.fan import FanSpider
# from spiders.repost import RepostSpider

# if __name__ == '__main__':
#     mode = sys.argv[1]
#     os.environ['SCRAPY_SETTINGS_MODULE'] = 'settings'
#     settings = get_project_settings()
#     process = CrawlerProcess(settings)
#     mode_to_spider = {
#         'comment': CommentSpider,
#         'fan': FanSpider,
#         'follow': FollowerSpider,
#         'user': UserSpider,
#         'repost': RepostSpider,
#         'tweet_by_tweet_id': TweetSpiderByTweetID,
#         'tweet_by_user_id': TweetSpiderByUserID,
#         'tweet_by_keyword': TweetSpiderByKeyword,
#     }
#     process.crawl(mode_to_spider[mode])
#     # the script will block here until the crawling is finished
#     process.start()
import os
import sys
import json
import argparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from spiders.tweet_by_user_id import TweetSpiderByUserID
from spiders.tweet_by_keyword import TweetSpiderByKeyword
from spiders.tweet_by_tweet_id import TweetSpiderByTweetID
from spiders.comment import CommentSpider
from spiders.follower import FollowerSpider
from spiders.user import UserSpider
from spiders.fan import FanSpider
from spiders.repost import RepostSpider

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run a scrapy spider with JSON args")
    parser.add_argument("--spider", required=True, help="spider key/name to run")
    parser.add_argument("--output", help="output file path")
    parser.add_argument("--args_json", default="{}", help="JSON string of spider args")
    args = parser.parse_args()

    # 设置 scrapy 环境
    os.environ['SCRAPY_SETTINGS_MODULE'] = 'settings'
    settings = get_project_settings()
    
    # 如果指定了输出路径，设置到 scrapy settings
    if args.output:
        settings.set('FEEDS', {
            args.output: {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'overwrite': True
            }
        })

    process = CrawlerProcess(settings)

    # spider 映射
    mode_to_spider = {
        'comment': CommentSpider,
        'fan': FanSpider,
        'follow': FollowerSpider,
        'follower': FollowerSpider,
        'user': UserSpider,
        'repost': RepostSpider,
        'tweet_by_tweet_id': TweetSpiderByTweetID,
        'tweet_by_user_id': TweetSpiderByUserID,
        'tweet_by_keyword': TweetSpiderByKeyword,
        'tweet_spider_by_keyword': TweetSpiderByKeyword,
        'tweet_spider_by_user_id': TweetSpiderByUserID,
        'tweet_spider_by_tweet_id': TweetSpiderByTweetID,
    }

    try:
        spider_key = args.spider
        spider_cls = mode_to_spider[spider_key]
    except KeyError:
        print(f"Unknown spider: {args.spider}", file=sys.stderr)
        sys.exit(2)

    try:
        spider_args = json.loads(args.args_json) if args.args_json else {}
        if not isinstance(spider_args, dict):
            raise ValueError("args_json must decode to a dict")
    except Exception as e:
        print("Invalid args_json:", e, file=sys.stderr)
        sys.exit(3)

    print(f"Starting spider: {spider_key} with args: {spider_args}")
    if args.output:
        print(f"Output will be saved to: {args.output}")
    
    # 启动爬虫
    process.crawl(spider_cls, **spider_args)
    process.start()