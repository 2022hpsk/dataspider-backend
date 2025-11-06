# 【登录设置】
PLATFORM = "rednote"  # rednote | weibo | twitter
LOGIN_TYPE = "playwright"  # cookie是最推荐的方法
# 默认设置的爬虫间隔较长，如果出现登录验证，建议更换账号再重试爬取
# 自定义User Agent（暂时仅对XHS有效）
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
SAVE_LOGIN_STATE = True  # 是否保存登录状态


# 【爬虫设置】
# 帖子数据和用户数据应分开爬取，使用creator模式，降低被封号风险，需要手动提取用户ID列表
CRAWLER_TYPE = "search"  # search关键词搜索 | detail帖子详情| creator创作者主页数据
KEYWORDS = "排球扣球"  # 关键词搜索配置，以英文逗号分隔
SAVE_DATA_OPTION = "jsonl"  # 由于大量的数据爬取，用jsonl保存数据最佳
USER_DATA_DIR = "%s_user_data_dir"  # 用户浏览器缓存的浏览器文件配置，%s will be replaced by platform name
START_PAGE = 1  # 爬取开始页数 默认从第一页开始
MAX_SCROLL_ATTEMPTS = 999  # 最大滚动次数
CRAWLER_MAX_NOTES_COUNT = 200  # 用户设置的最大想要抓取的帖子数量
MAX_CONCURRENCY_NUM = 1  # 并发爬虫数量控制
ENABLE_GET_IMAGES = False  # 是否开启爬图片模式, 默认不开启爬图片
ENABLE_GET_COMMENTS = True  # 是否开启爬评论模式, 默认开启爬评论
CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = 999  # 爬取所有评论的数量控制(一级+二级评论)
ENABLE_GET_SUB_COMMENTS = True  # 是否开启爬二级评论模式, 默认不开启爬二级评论，老版本项目使用了 db, 则需参考 schema/tables.sql line 287 增加表字段
# 未启用代理时的最小和最大爬取间隔，单位秒
CRAWLER_MIN_SLEEP_SEC = 4
CRAWLER_MAX_SLEEP_SEC = 8


# 【各平台特有设置】
# ====wb====
# 指定微博平台需要爬取的帖子列表
WEIBO_SPECIFIED_ID_LIST = [
    "4982041758140155",
    # ........................
]
# 指定weibo创作者ID列表
WEIBO_CREATOR_ID_LIST = [
    "1719871835",
    # ........................
]

# ====rednote====
# 具体值参见media_platform.xxx.field下的枚举值，一般用综合排序general
SORT_TYPE = "popularity_descending"  # general/time_descending/popularity_descending
# detail模式下，根据用户ID爬取小红书作者信息
XHS_CREATOR_ID_LIST = [
    "5f0683a8000000000101d5dc",
    # ...............
]
# 指定小红书需要爬虫的笔记URL列表, 必须要携带xsec_token和xsec_source参数
XHS_SPECIFIED_NOTE_URL_LIST = [
    "https://www.xiaohongshu.com/explore/680af6e8000000000f032b0e?xsec_token=ABD0fDfPwrT_O5P8hu9dyR3AWxFM8WH8xCjVEG6yzOVKk=&xsec_source=pc_search"
    # ...............
]


# ====twitter====
# 指定twitter平台需要爬取的帖子列表
TWITTER_SPECIFIED_ID_LIST = [
    "1719871835",
    # ........................
]
# 指定twitter创作者ID列表
TWITTER_CREATOR_ID_LIST = [
    "1719871835",
    # ........................
]
