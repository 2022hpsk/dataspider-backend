from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import random
import json
import os
from datetime import datetime
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver import ActionChains
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
def get_posts_byday(driver,keyword, start_date, end_date, output_dir=None,is_live=False): 
    posts_lists = []
    post_index = set() #帖子独立标识集合去重
    if is_live:
        driver.get(f"https://x.com/search?q={keyword}%20lang%3Aen%20until%3A{end_date}%20since%3A{start_date}&src=typed_query&f=live") # 查询条件 src=typed_query：表示这是一个手动输入的查询。f=live：表示只检索实时搜索结果
    else:
        # driver.get(f"https://x.com/search?q={keyword}&src=typed_query&f=top") # 查询条件 src=typed_query：表示这是一个手动输入的查询。
        driver.get(f"https://x.com/search?q={keyword}%20lang%3Aen%20until%3A{end_date}%20since%3A{start_date}&src=typed_query&f=top")

    # driver.get(f"https://x.com/OpenAI")
    time.sleep(5)  # 等待页面加载完成


    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_step = 4500  # 每次向下滚动的像素数
    scroll_count = 0
    previous_post_count = 0  # 用于记录上一次的帖子ID数量
    max_attempts = 5  # 当数据条数不变的最大允许次数
    attempts = 0
    garbages = []
    isgarbage = 0

    # 保存路径
    if not output_dir:
        # 保存路径为该父文件夹下的output文件夹
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        # base_dir = r"C:\Users\admin\codespace\twittercrawler\twitter\json"
        os.makedirs(base_dir, exist_ok=True)
    else:
        base_dir = output_dir
        os.makedirs(base_dir, exist_ok=True)
    # 文件命名要加入目前的时间戳，防止覆盖
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    if is_live:
        posts_file = os.path.join(base_dir, f"[latest rank]posts_{keyword}_{start_date}_{end_date}_{timestamp}.json")
    else:
        posts_file = os.path.join(base_dir, f"[top rank]posts_{keyword}_{start_date}_{end_date}_{timestamp}.json")

    while True:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')
        post_tags = soup.select('div[data-testid="cellInnerDiv"]')
        # post_tags = soup.select('article[data-testid="tweet"]')
        for post_tag in post_tags:
            transform_value = post_tag['style'].split('translateY(')[1].split('px)')[0]
            # print(transform_value)
            if float(transform_value) > 450 and transform_value not in post_index: # 不想漏掉第一个帖子，所以宁可错采一些
                post_index.add(transform_value)

                # 提取用户名
                username_tag = post_tag.select_one('div[data-testid="User-Name"]')
                if username_tag:
                    username = username_tag.get_text(strip=True)
                    # 检查用户名是否包含垃圾词
                    if any(garbage in username for garbage in garbages):
                        isgarbage = 1
                        continue  # 跳过当前帖子，不再提取ID
                    username = username_tag.select_one('span').text.strip() if username_tag.select_one('span') else ''
                isgarbage = 0

                post_content = ""
                tweet_text_div = post_tag.select_one('div[data-testid="tweetText"]')
                if tweet_text_div:
                    # 遍历所有子元素，按顺序提取文字、图片和链接
                    for element in tweet_text_div.children:
                        if element.name == 'span':  # 处理文本
                            post_content += element.text.strip() + " "
                        elif element.name == 'img':  # 处理图片
                            alt_text = element.get('alt', '')
                            if alt_text:
                                post_content += f"{alt_text} "
                        elif element.name == 'a':  # 处理链接
                            href = element.get('href', '')
                            if href:
                                post_content += f"{href} "
                                post_content += element.text.strip() + " "

                # 输出最终提取的内容
                # print(post_content)

                # print(post_content)

                # 查找包含aria-label的div标签，提取转评赞以及帖子id
                if start_date < '2023-01-01':
                    aria_label = post_tag.find('div', attrs={'aria-label': re.compile(r'.*likes.*')}) # likes views
                else:
                    aria_label = post_tag.find('div', attrs={'aria-label': re.compile(r'.*views.*')}) # likes views
                if aria_label:
                    # 从aria-label中提取数据
                    label_text = aria_label['aria-label']

                    # 初始化数据
                    replies = reposts = likes = bookmarks = views = 0

                    if 'repl' in label_text:
                        match = re.search(r'(\d+)\s+repl', label_text)
                        replies = int(match.group(1)) if match else 0

                    if 'repost' in label_text:
                        match = re.search(r'(\d+)\s+repost', label_text)
                        reposts = int(match.group(1)) if match else 0

                    if 'like' in label_text:
                        match = re.search(r'(\d+)\s+like', label_text)
                        likes = int(match.group(1)) if match else 0

                    if 'bookmark' in label_text:
                        match = re.search(r'(\d+)\s+bookmark', label_text)
                        bookmarks = int(match.group(1)) if match else 0
                    if 'view' in label_text:
                        # views = int(re.search(r'(\d+)\s+view', label_text).group(1))
                        # 检查是否匹配到了 "view" 和数字
                        match = re.search(r'(\d+)\s+view', label_text)
                        if match:
                            views = int(match.group(1))
                        else:
                            views = 0  # 如果没有匹配到，设置默认值为0

                    # 查找帖子ID和用户ID
                    post_id_tag = aria_label.find_all('div', class_='css-175oi2r r-18u37iz r-1h0z5md r-13awgt0')
                    if post_id_tag:
                        # 找到第四个div，提取其中的链接
                        post_id_link = post_id_tag[3].find('a', href=True)
                        if post_id_link:
                            post_id = post_id_link['href'].split('/')[3]  # 从URL中提取帖子ID
                            user_id = post_id_link['href'].split('/')[1]
                        else:
                            post_id = ''
                            user_id = ''
                    else:
                        post_id = ''
                        user_id = ''
                else:
                    replies = reposts = likes = bookmarks = views = 0
                    post_id = ''
                    user_id = ''
                    break

                # 提取帖子发布时间
                time_tag = post_tag.find('time', attrs={'datetime': True})
                if time_tag and 'datetime' in time_tag.attrs:
                    datetime_str = time_tag['datetime']
                    # 解析ISO格式的日期时间字符串
                    dt = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                    # 格式化为“年-月-日 时:分:秒”格式
                    post_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    post_time = ''

                # 提取hashtags，确保唯一性，使用集合去重
                hashtags = set()
                hashtag_tags = post_tag.select('a[href*="/hashtag/"]')
                for tag in hashtag_tags:
                    hashtag = tag.get_text(strip=True)
                    hashtags.add(hashtag)

                # 提取图片和视频的链接
                media_urls = set()  # 使用集合来自动去重
                img_tags = post_tag.find_all('img')
                for img in img_tags:
                    img_url = img.get('src')
                    if img_url and 'profile_images' not in img_url and 'emoji' not in img_url:
                        media_urls.add(img_url)
                media_urls = list(media_urls)

                # 提取@了哪些用户
                # at_usernames = set()  # 使用集合确保唯一性
                # at_usernames.update(re.findall(r'@(\w+)', post_content))  # 查找所有 @ 后的用户名

                # 提取帖子中的所有链接（使用正则表达式从文本中匹配URL）
                urls = set()  # 使用集合去重

                # 匹配以 http 或 https 开头的 URL
                url_pattern = re.compile(r'https?://[^\s]+')

                # 在帖子文本中查找所有符合条件的URL
                urls.update(url_pattern.findall(post_content))

                # 查找回复的多个用户
                reply_users = []
                reply_tag = post_tag.find('div', class_='css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41') # 查找包含回复信息的 div
                if reply_tag:
                    # 获取所有回复用户的 a 标签
                    reply_user_tags = reply_tag.find_all('a')
                    for reply_user_tag in reply_user_tags:
                        # 提取用户名并添加到列表
                        reply_users.append(reply_user_tag.text.strip())
                # 构建帖子数据，新增字段
                web_object = {
                    "postUrl": f"https://x.com/{user_id}/status/{post_id}",
                    "text": post_content,
                    "mid": post_id,
                    "userName": username,
                    "userId": user_id,
                    "date": post_time,
                    "likeNum": likes,
                    "commentNum": replies,
                    "repostNum": reposts,
                    "viewNum": views,
                    "bookmarks": bookmarks,
                    "hashtags": list(hashtags),
                    "mediaUrls": media_urls,
                    # "atUsernames": list(at_usernames),  # 新增字段：记录@的用户
                    # "urls": list(urls),  # 新增字段：记录帖中的所有链接
                    # "replyUsers": reply_users  # 新增字段：记录多个回复的用户
                }

                #  # 构建帖子数据
                # web_object = {
                #     "text": post_content,
                #     "mid": post_id,
                #     "userName": username,
                #     "userId": user_id,
                #     "date": post_time,
                #     "likeNum": likes,
                #     "commentNum": replies,
                #     "repostNum": reposts,
                #     "viewNum": views,
                #     "bookmarks": bookmarks
                # }

                posts_lists.append(web_object)

                # 保存 posts
                if os.path.exists(posts_file):
                    # File exists, so read the existing data
                    with open(posts_file, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                    
                    # Append the new posts data to the existing data
                    existing_data.extend(posts_lists)

                    # Write the updated data back to the file
                    with open(posts_file, "w", encoding="utf-8") as f:
                        json.dump(existing_data, f, ensure_ascii=False, indent=4)
                    
                    print(f"Data appended to {posts_file}")

                else:
                    # File doesn't exist, create it and write the new data
                    with open(posts_file, "w", encoding="utf-8") as f:
                        json.dump(posts_lists, f, ensure_ascii=False, indent=4)

                    print(f"File {posts_file} created with initial data.")
                '''
                [目前]存储在posts.json文件中的每个帖子对象包含以下信息：

                    text: 帖子的正文内容。
                    mid: 帖子的ID。
                    userName: 用户名。
                    userId: 用户ID。
                    date: 帖子的发布时间。
                    likeNum: 点赞数。
                    commentNum: 评论数。
                    repostNum: 转发数。
                    viewNum: 浏览数。
                    bookmarks: 收藏数。
                ''' 
            
        current_post_count = len(posts_lists)
        print(f"已收集到 {current_post_count} 个帖子")

        # if current_post_count >= 200:  # 如果爬取到的数据条数超过200，则停止爬取
        #     break

        if current_post_count == previous_post_count and not isgarbage: #防止遇到批量垃圾帖子，导致误识别为滑到底了
            time.sleep(random.uniform(1, 2))
            attempts += 1
        else:
            attempts = 0
            previous_post_count = current_post_count

        if attempts == max_attempts:
            # 检测到页面错误信息，尝试点击'Retry'按钮...
            if len(post_tags) > 0 and post_tags[-1].select_one('span').text.strip() == "Something went wrong. Try reloading." if post_tags[-1].select_one('span') else '':
                print(f"检测到'Retry'按钮，当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')},滚动了{scroll_count}次")
                # 等待人工确认点击
                input("按Enter键以继续爬取...")
                while True:  # 无限循环，直到成功点击
                    try:
                        # 等待6分钟（360秒）
                        print("等待1分钟...")
                        time.sleep(60)  # 等待6分钟

                        # 使用 CSS Selector 或 XPath 查找'Retry'按钮并确保它可点击
                        retrybutton = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[.//*[contains(text(),'Retry')]]"))
                        )

                        # 滚动到按钮所在位置
                        driver.execute_script("arguments[0].scrollIntoView();", retrybutton)

                        # 强制点击按钮
                        driver.execute_script("arguments[0].click();", retrybutton)
                        print(f"点击'Retry'按钮成功，等待5秒后继续爬取，当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        time.sleep(15)  # 等待15秒后继续爬取
                        attempts = 0
                        previous_post_count = current_post_count
                        break  # 成功点击后跳出循环

                    except Exception as e:
                        # print(f"未能找到'Retry'按钮或点击失败，错误信息: {e}")
                        print("没找到按钮")

            print("多次滚动后没有新数据，等30秒")
            time.sleep(30)

        if attempts > max_attempts:  # 如果连续6次没有新数据，停止爬取
            print(f"多次滚动后没有新数据，已尝试 {attempts}")
            # break
            user_input = input("请输入0停止爬取，1继续爬取: ")  # 获取用户输入
            if user_input == "0":
                print("停止爬取。")
                break  # 停止爬取
            elif user_input == "1":
                print("继续爬取...")
                attempts = 0  # 重置尝试次数，继续爬取
            else:
                print("无效输入，请输入0或1。")

        driver.execute_script(f"window.scrollBy(0, {scroll_step});")
        scroll_count += 1
        time.sleep(random.uniform(2, 3))  # 等待加载更多内容




def get_posts_byuser(driver, username, start_date, end_date, with_media=False):
    # todo: 实现按用户抓取的逻辑
    pass