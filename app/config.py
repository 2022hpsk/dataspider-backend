# 文件名: app\config.py
# filepath: c:\Users\lenovo\Desktop\datacrawl\backend\WeiboSpider-backend\app\config.py
import os
from pathlib import Path

# from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# load_dotenv(BASE_DIR / ".env")

TWITTER_BASE = str(BASE_DIR / "twitterspider")
TWITTER_OUTPUT = str(Path(TWITTER_BASE) / "output")
os.makedirs(TWITTER_OUTPUT, exist_ok=True)

WEIBO_BASE = str(BASE_DIR / "weibospider")
WEIBO_OUTPUT = str(Path(WEIBO_BASE) / "output")
os.makedirs(WEIBO_OUTPUT, exist_ok=True)

XHS_BASE = str(BASE_DIR / "xhsspider")
XHS_OUTPUT = str(Path(XHS_BASE) / "output")
os.makedirs(XHS_OUTPUT, exist_ok=True)
