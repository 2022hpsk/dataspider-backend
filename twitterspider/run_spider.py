# ...existing code...
import argparse
import os
import subprocess
import time
import requests
import inspect

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from crawl_functions import get_posts_byday, get_posts_byuser

def wait_for_cdp(port: int, timeout: int = 20) -> bool:
    url = f"http://127.0.0.1:{port}/json/version"
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=1)
            if r.ok:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

def launch_chrome_with_cdp(port: int, user_data_dir: str) -> None:
    os.makedirs(user_data_dir, exist_ok=True)
    # 通过 App Paths 启动“chrome”，不用写死路径
    subprocess.Popen(
        [
            "powershell", "-NoProfile", "-Command",
            "Start-Process", "chrome",
            "-ArgumentList", f"'--remote-debugging-port={port}','--user-data-dir={user_data_dir}','--no-first-run','--no-default-browser-check','--disable-extensions','--disable-popup-blocking'"
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False
    )

def make_driver(port: int) -> webdriver.Chrome:
    option = Options()
    option.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
    driver = webdriver.Chrome(options=option)
    # 去除 WebDriver 痕迹
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    })
    return driver

def call_crawl_func(mode: str, driver: webdriver.Chrome, keyword: str, start_date: str, end_date: str, output_dir: str = None):
    # 根据函数签名自动适配参数个数（兼容你的实现）
    target = get_posts_byday if mode == "keyword" else get_posts_byuser
    args = [driver, keyword, start_date, end_date, output_dir if output_dir else None,False]
    return target(*args)

def parse_args():
    parser = argparse.ArgumentParser(description="Twitter crawler runner (attach to Chrome via remote debugging).")
    parser.add_argument("--mode", choices=["keyword", "user"], default="keyword", help="运行模式: keyword 或 user")
    parser.add_argument("--keyword", required=True, help="搜索关键词/账号")
    parser.add_argument("--start", required=True, help="开始日期，格式 YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="结束日期，格式 YYYY-MM-DD")
    parser.add_argument("--debug-port", type=int, default=9530, help="Chrome 远程调试端口")
    parser.add_argument("--user-data-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_data"), help="Chrome 用户数据目录")
    parser.add_argument("--attach-only", action="store_true", help="只连接已开启调试端口的 Chrome，不主动启动")
    parser.add_argument("--wait-timeout", type=int, default=20, help="等待调试端口就绪的超时秒数")
    parser.add_argument("--output_dir", required=False, help="输出文件路径（可选）")
    return parser.parse_args()

def main():
    args = parse_args()

    if not args.attach_only:
        launch_chrome_with_cdp(args.debug_port, args.user_data_dir)

    if not wait_for_cdp(args.debug_port, timeout=args.wait_timeout):
        raise RuntimeError(f"未检测到调试端口 {args.debug_port}，请确认 Chrome 已以 --remote-debugging-port={args.debug_port} 启动。")

    driver = make_driver(args.debug_port)
    print("浏览器已启动并已连接")

    try:
        call_crawl_func(
            mode=args.mode,
            driver=driver,
            keyword=args.keyword,
            start_date=args.start,
            end_date=args.end,
            output_dir=args.output_dir if hasattr(args, 'output_dir') else None
        )
    finally:
        # 如需保留浏览器可自行注释掉
        try:
            driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    main()
# python run_spider.py  --keyword 马斯克 --start 2025-10-01 --end 2025-10-02