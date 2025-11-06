import argparse
import asyncio
import sys
from xhs_spider import RednoteCrawler
import os

def parse_args():
    parser = argparse.ArgumentParser(
        description="Twitter crawler runner (attach to Chrome via remote debugging)."
    )
    parser.add_argument(
        "--mode",
        choices=["keyword", "user", "tweet"],
        default="keyword",
        help="运行模式: keyword 或 user 或 tweet",
    )
    parser.add_argument("--keyword", required=True, help="搜索关键词")
    parser.add_argument(
        "--output",
        required=True,
        help="输出文件路径，默认为 output/_contents_<date>.jsonl",
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    # 将输出目录写入 output.txt 
    with open('output.txt', 'w', encoding='utf-8') as f:
        f.write(args.output)

    crawler = RednoteCrawler(args.keyword, args.mode)
    await crawler.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit()
