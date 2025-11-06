import re, os, asyncio, json, hashlib
from datetime import datetime
from playwright.async_api import BrowserContext, Page, Locator, async_playwright
from typing import List, Optional, Dict, Any, Set
from urllib.parse import urljoin

import tools.text_util
import config
from .login import RednoteLogin
from .store import RednoteJsonlStoreImplement
from models import Post, Platform

ROOT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)  # xhsspider 目录
LOGIN_STATE_PATH = os.path.join(ROOT_DIR, "xiaohongshu_login_state.json")


class RednoteCrawler:
    """小红书笔记详情提取器"""

    def __init__(self, keyword: str, mode: str = "keyword"):
        self.keyword = keyword
        self.mode = mode
        self.context_page: Page  # 标签页
        self.browser_context: BrowserContext  # 浏览器环境
        self.index_url = "https://www.xiaohongshu.com"  # 首页
        self.login_state_path = LOGIN_STATE_PATH  # 登录状态文件
        self.crawled_posts: List[Post] = []  # 存储爬取的帖子
        self.crawled_post_ids: Set[str] = set()  # 已爬取的帖子ID集合，用于去重
        self.current_page_num: int = 1  # 当前页码

    async def start(self):
        async with async_playwright() as playwright:
            # 启动浏览器
            browser = await playwright.chromium.launch(headless=False, slow_mo=100)

            # 如果有保存的登录状态，直接复用
            if os.path.exists(self.login_state_path):
                print("检测到已保存的登录状态，直接加载...")
                self.browser_context = await browser.new_context(
                    storage_state=self.login_state_path
                )
                self.context_page = await self.browser_context.new_page()
            else:
                # 如果没有检测到登录状态，进行手动登录
                self.browser_context = await browser.new_context()
                self.context_page = await self.browser_context.new_page()

            # 检查登录状态是否仍然有效
            login_checker = RednoteLogin(
                browser_context=self.browser_context,
                context_page=self.context_page,
                login_state_path=self.login_state_path,
            )
            await self.context_page.goto(
                "https://www.xiaohongshu.com/explore", wait_until="domcontentloaded"
            )

            if await login_checker.check_login_status():
                print("登录状态有效，继续使用")
            else:
                print("保存的登录状态已过期，需要重新登录")
                await login_checker.click_login_button()

            if await login_checker.check_login_status():
                await self.context_page.goto(
                    "https://www.xiaohongshu.com/explore", wait_until="domcontentloaded"
                )
                # 保存登录状态
                await self.browser_context.storage_state(path=self.login_state_path)
                print(f"登录状态已保存到 {self.login_state_path}")

                # 选择爬虫方式
                if self.mode == "keyword":
                    # Search for notes and retrieve their comment information.
                    print("开始执行关键词爬取任务...")
                    await self.search()
                # elif config.CRAWLER_TYPE == "detail":
                #     # Get the information and comments of the specified post
                #     await self.get_specified_notes()
                # elif config.CRAWLER_TYPE == "creator":
                #     # Get creator's information and their notes and comments
                #     await self.get_creators_information()
                else:
                    pass

    async def search(self):
        # 输入关键词到搜索框
        search_keyword = self.keyword
        search_input = self.context_page.locator(
            "input[placeholder='搜索小红书']"
        )  # 根据搜索框 placeholder 定位
        await search_input.focus()
        await search_input.fill(search_keyword)

        search_btn = self.context_page.locator(".input-box .search-icon")
        await search_btn.click()

        print("搜索中，等待页面加载...")
        await asyncio.sleep(5)
        # 爬取搜索结果
        await self.crawl_search_results()

    async def crawl_search_results(self):
        """爬取当前页面的帖子"""
        print("开始解析搜索结果...")

        max_posts = getattr(config, "CRAWLER_MAX_NOTES_COUNT", 10)

        while len(self.crawled_posts) < max_posts:
            # 获取当前页面的所有帖子卡片
            note_cards = self.context_page.locator(
                '.note-item, [class*="note-card"], [class*="feeds-container"] .note'
            )
            card_count = await note_cards.count()

            print(f"第 {self.current_page_num} 页，找到 {card_count} 个帖子卡片")

            if card_count == 0:
                print("未找到帖子卡片，可能页面结构变化")
                break

            # 获取当前视口内可见的卡片
            visible_cards = await self.get_visible_cards_in_viewport(
                note_cards, card_count
            )
            print(f"当前视口内可见的帖子: {len(visible_cards)} 个")

            if not visible_cards:
                print("没有可见帖子，滚动加载更多...")
                await self.scroll_to_load_more()
                continue

            # 修改这里：传递 note_cards 而不是 visible_cards
            new_posts_count = await self.crawl_current_page_posts(
                visible_cards, card_count, max_posts
            )

            # 如果当前可见帖子都爬完了，再滚动
            if new_posts_count == 0:
                print("当前可见帖子已爬完，滚动加载更多...")
                await self.scroll_to_load_more()

            self.current_page_num += 1

        print(f"爬取完成！共爬取 {len(self.crawled_posts)} 个可见帖子")

    async def get_visible_cards_in_viewport(
        self, note_cards: Locator, card_count: int
    ) -> list:
        """获取当前视口内可见且为真实帖子的卡片"""
        visible_cards = []

        for i in range(card_count):
            try:
                card = note_cards.nth(i)

                # 检查是否在视口内（部分可见即可）
                is_in_viewport = await card.evaluate(
                    """
                    element => {
                        const rect = element.getBoundingClientRect();
                        const windowHeight = window.innerHeight || document.documentElement.clientHeight;
                        const windowWidth = window.innerWidth || document.documentElement.clientWidth;

                        return (
                            rect.top < windowHeight &&
                            rect.bottom > 0 &&
                            rect.left < windowWidth &&
                            rect.right > 0
                        );
                    }
                    """
                )

                if not is_in_viewport:
                    continue

                # 检查是否可见
                if not await card.is_visible():
                    continue

                # 过滤掉系统推荐、广告等非帖子卡片
                inner_html = (await card.inner_html()).lower()
                if any(
                    keyword in inner_html
                    for keyword in [
                        "大家都在搜",
                    ]
                ):
                    continue

                visible_cards.append(card)

            except Exception as e:
                print(f"检查卡片 {i} 视口位置时出错: {e}")
                continue

        return visible_cards

    async def crawl_current_page_posts(
        self, visible_cards: list, card_count: int, max_posts: int
    ) -> int:
        """爬取当前页面的帖子，返回新爬取的帖子数量"""
        new_posts_count = 0

        # 直接遍历 visible_cards 列表
        for card_index, card in enumerate(visible_cards):
            if len(self.crawled_posts) >= max_posts:
                break

            try:
                # 获取当前帖子卡片（直接从列表中获取）
                current_card = card

                # 检查是否已经爬取过（通过帖子链接或ID）
                card_info = await self.extract_card_info(current_card)
                if not card_info or card_info["post_id"] in self.crawled_post_ids:
                    print(
                        f"跳过已爬取或无效帖子: {card_info.get('post_id', 'unknown')}"
                    )
                    continue
                if (
                    not card_info
                    or not card_info["url"]
                    or "/explore/" not in card_info["url"]
                ):
                    print("跳过非帖子卡片（疑似推荐或广告）")
                    continue

                print(
                    f"正在爬取第 {len(self.crawled_posts) + 1} 个帖子: {card_info['post_id']}"
                )

                # 点击进入帖子详情
                await current_card.click()
                await self.context_page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)

                # 爬取帖子详情
                post = await self.extract_post_detail()
                if post:
                    self.crawled_posts.append(post)
                    self.crawled_post_ids.add(post.source.post_id)
                    new_posts_count += 1
                    await RednoteJsonlStoreImplement.save_data_to_jsonl(
                        post, "contents"
                    )
                    print(f"成功爬取帖子: {post.source.post_id}")

                # 返回搜索结果页
                await self.context_page.go_back()
                await self.context_page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)

            except Exception as e:
                print(f"爬取第 {card_index + 1} 个帖子卡片时出错: {e}")
                # 尝试返回搜索结果页
                try:
                    if "search" not in self.context_page.url:
                        await self.context_page.go_back()
                        await asyncio.sleep(2)
                except:
                    pass
                continue

        return new_posts_count

    async def extract_card_info(self, card: Locator) -> Optional[Dict[str, str]]:
        """从卡片中提取基本信息，用于去重"""
        try:
            # 获取卡片的链接
            link_selectors = ['a[href*="/explore/"]', 'a[href*="note_id="]', "a"]

            for selector in link_selectors:
                links = card.locator(selector)
                if await links.count() > 0:
                    href = await links.first.get_attribute("href")
                    if href and ("/explore/" in href or "note_id=" in href):
                        post_id = self.extract_post_id(href)
                        if post_id:
                            return {
                                "post_id": post_id,
                                "url": (
                                    urljoin(self.index_url, href)
                                    if href.startswith("/")
                                    else href
                                ),
                            }

            # 尝试从图片或其他元素提取
            img_elements = card.locator("img")
            if await img_elements.count() > 0:
                # 使用图片URL生成唯一ID（备用方案）
                img_src = await img_elements.first.get_attribute("src")
                if img_src:
                    unique_id = hashlib.md5(img_src.encode()).hexdigest()[:12]
                    return {"post_id": unique_id, "url": ""}

            return None

        except Exception as e:
            print(f"提取卡片信息失败: {e}")
            return None

    async def scroll_to_load_more(self):
        """滚动页面以加载更多内容"""
        try:
            await self.context_page.evaluate(
                """
                window.scrollBy({
                    top: window.innerHeight * 0.7,
                    behavior: 'smooth'
                });
            """
            )

            # 等待新内容加载
            await asyncio.sleep(3)

        except Exception as e:
            print(f"滚动加载失败: {e}")

    async def extract_post_detail(self) -> Optional[Post]:
        """提取帖子详情"""
        try:
            # 获取帖子ID和URL
            current_url = self.context_page.url
            post_id = self.extract_post_id(current_url)

            if not post_id:
                print("无法提取帖子ID")
                return None

            # 检查是否已经爬取过（双重检查）
            if post_id in self.crawled_post_ids:
                print(f"帖子 {post_id} 已爬取，跳过")
                return None

            # 提取帖子内容
            content_data = await self.extract_content()

            # 提取发帖人信息
            sender_data = await self.extract_sender_info()

            # 提取统计信息
            stats_data = await self.extract_statistics()

            # 构建Post对象
            post = Post(
                id=f"socialMedia_crawler/rednote/{post_id}",  # 数据库唯一ID
                type=Post.PostType.post,
                source=Post.Source(
                    platform=Platform.rednote,
                    engine="playwright_crawler",
                    url=current_url,
                    post_id=post_id,
                    parent_id=None,
                ),
                content=Post.Content(
                    raw_text=content_data.get("raw_text", ""),
                    at_users=content_data.get("at_users", []),
                    tags=content_data.get("tags", []),
                    urls=content_data.get("urls", []),
                    images=content_data.get("images", []),
                    videos=content_data.get("videos", []),
                ),
                sender=Post.Sender(
                    user_id=sender_data.get("user_id", ""),
                    send_time=sender_data.get("send_time"),
                    location=Post.Sender.Location(
                        gps=sender_data.get("location", {}).get("gps"),
                        city=sender_data.get("location", {}).get("city"),
                        country=sender_data.get("location", {}).get("country"),
                    ),
                ),
                statistics=Post.StatisticsItem(
                    cnt_view=stats_data.get("views", -1),
                    cnt_like=stats_data.get("likes", -1),
                    cnt_comment=stats_data.get("comments", -1),
                    cnt_share=stats_data.get("shares", -1),
                    cnt_collect=stats_data.get("collects", -1),
                ),
            )

            return post

        except Exception as e:
            print(f"提取帖子详情失败: {e}")
            return None

    async def extract_content(self) -> Dict[str, Any]:
        """提取帖子内容"""
        content_data = {
            "raw_text": "",
            "urls": [],
            "images": [],
            "tags": [],
            "at_users": [],
        }

        try:
            # 提取标题
            title_selectors = [
                ".title",
                "[class*='title']",
                ".note-title",
                "h1",
                "h2",
            ]

            title_text = ""
            for selector in title_selectors:
                title_elements = self.context_page.locator(selector)
                if await title_elements.count() > 0:
                    title_text = await title_elements.first.text_content()
                    if title_text:
                        title_text = title_text.strip()
                        break

            # 提取正文内容
            text_selectors = [
                ".desc",
                "[class*='content']",
                "[class*='text']",
                ".note-content",
            ]

            raw_text = ""
            for selector in text_selectors:
                text_elements = self.context_page.locator(selector)
                if await text_elements.count() > 0:
                    raw_text = await text_elements.first.text_content()
                    if raw_text:
                        raw_text = raw_text.strip()
                        break

            # 拼接标题和正文
            if title_text and raw_text:
                content_data["raw_text"] = f"{title_text}\n{raw_text}"
            elif title_text:
                content_data["raw_text"] = title_text
            elif raw_text:
                content_data["raw_text"] = raw_text

            content_data["tags"] = tools.text_util.extract_tags(
                content_data["raw_text"], Platform.rednote
            )
            content_data["at_users"] = tools.text_util.extract_at_users(
                content_data["raw_text"], Platform.rednote
            )

        except Exception as e:
            print(f"提取内容失败: {e}")

        return content_data

    async def extract_sender_info(self) -> Dict[str, Any]:
        """提取发帖人信息"""
        sender_data = {"user_id": "", "send_time": None, "location": {"city": ""}}

        try:
            # 提取用户ID
            user_link = self.context_page.locator('a[href*="/user/profile/"]').first
            if await user_link.count() > 0:
                user_href = await user_link.get_attribute("href")
                if user_href:
                    user_id_match = re.search(r"/user/profile/([a-f0-9]+)", user_href)
                    if user_id_match:
                        sender_data["user_id"] = user_id_match.group(1)

            # 提取发布时间和地理位置（都在 .date 中）
            date_text = await self.context_page.evaluate(
                """
                () => {
                    const el = document.querySelector('.date');
                    return el ? el.innerText.trim() : null;
                }
                """
            )
            if date_text:
                parts = date_text.split()
                if len(parts) == 1:
                    send_time = parts[0]
                    city = None
                elif len(parts) >= 2:
                    send_time = parts[0]
                    # 合并剩余部分（防万一中间有空格，如“中国 北京”）
                    city = " ".join(parts[1:])

                sender_data["send_time"] = tools.time_util.parse_xhs_time(send_time)
                sender_data["location"]["city"] = city
        except Exception as e:
            print(f"提取发帖人信息失败: {e}")

        return sender_data

    async def extract_statistics(self) -> Dict[str, int]:
        """提取帖子统计信息"""
        stats = {"views": -1, "likes": 0, "comments": 0, "shares": -1, "collects": 0}

        try:
            # 方法1: 直接通过特定的 class 选择器定位
            # 点赞数
            like_element = self.context_page.locator(".like-wrapper .count").first
            if await like_element.count() > 0:
                like_text = await like_element.text_content()
                if like_text and like_text.strip():
                    clean_text = re.sub(r"[^\d]", "", like_text.strip())
                    if clean_text:
                        stats["likes"] = int(clean_text)

            # 收藏数
            collect_element = self.context_page.locator(".collect-wrapper .count").first
            if await collect_element.count() > 0:
                collect_text = await collect_element.text_content()
                if collect_text and collect_text.strip():
                    clean_text = re.sub(r"[^\d]", "", collect_text.strip())
                    if clean_text:
                        stats["collects"] = int(clean_text)

            # 评论数
            comment_element = self.context_page.locator(".chat-wrapper .count").first
            if await comment_element.count() > 0:
                comment_text = await comment_element.text_content()
                if comment_text and comment_text.strip():
                    clean_text = re.sub(r"[^\d]", "", comment_text.strip())
                    if clean_text:
                        stats["comments"] = int(clean_text)

            print(
                f"提取到的统计信息: 点赞={stats['likes']}, 收藏={stats['collects']}, 评论={stats['comments']}"
            )

        except Exception as e:
            print(f"提取统计信息失败: {e}")

        return stats

    def extract_post_id(self, url: str) -> Optional[str]:
        """从URL中提取帖子ID"""
        try:
            # 小红书帖子URL模式
            match = re.search(r"/explore/([a-f0-9]+)", url)
            if match:
                return match.group(1)

            match = re.search(r"note_id=([a-f0-9]+)", url)
            if match:
                return match.group(1)

            return None
        except Exception as e:
            print(f"提取帖子ID失败: {e}")
            return None

    def parse_time_string(self, time_str: str) -> Optional[datetime]:
        """解析时间字符串"""
        try:
            # 处理相对时间
            if "前" in time_str:
                return datetime.now()

            # 处理绝对时间
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"]:
                try:
                    return datetime.strptime(time_str, fmt)
                except:
                    continue

            return None
        except:
            return None

    async def close(self):
        """关闭浏览器"""
        if hasattr(self, "browser_context"):
            await self.browser_context.close()
