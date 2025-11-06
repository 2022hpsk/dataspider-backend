import argparse
import asyncio
import sys
from xhs_spider import RednoteCrawler


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
    return parser.parse_args()


async def main():
    args = parse_args()

    crawler = RednoteCrawler(args.keyword, args.mode)
    await crawler.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit()
