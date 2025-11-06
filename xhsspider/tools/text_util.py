import re
from typing import List
from models import Post, Platform

# 已完成修改20250717

_url_pattern = re.compile(r'https?://[^\s<>"]+', re.IGNORECASE)


def extract_urls(text: str) -> List[str]:
    """
    Extract urls from text.
    :param text: The text to extract urls from.
    :return: a List of urls.
    """
    if not isinstance(text, str):
        text = ""

    urls = _url_pattern.findall(text)
    for i, url in enumerate(urls):
        urls[i] = url.strip()
    return urls


_tag_pattern_map = {
    Platform.twitter: re.compile(
        r"(?<!\w)#\w+(?=\s|$)"
    ),  # Twitter标签（允许空格外字符）
    Platform.weibo: re.compile(r"#([^#\r\n]+?)#"),  # 微博标签（两个#包围）
    # Platform.rednote: re.compile(
    #     r"#([^#\s]+)#"
    # ),  # 小红书标签（两个#包围，中间不含#和空格）
    Platform.rednote: re.compile(r"#([^\s#]+)"),
}


def extract_tags(text: str, platform: Platform) -> List[str]:
    """
    Extract tags from text.
    :param text: The text to extract tags from.
    :param platform: The platform of the text.
    :return: a List of tags.
    """
    if not isinstance(text, str):
        text = ""

    _tag_pattern = _tag_pattern_map[platform]
    # replace one by one from start, to avoid '#tag1# ... #tag2#' => '# ... #'

    tags = []
    start_pos = 0

    # remove consecutive #'s
    text = re.sub(r"##+", "#", text)

    while True:
        match = _tag_pattern.search(text, pos=start_pos)
        if match is None:
            break
        # text = text[:match.start()] + text[match.end():]
        start_pos = match.end()
        tag = match.group().strip("#")
        tags.append(tag)
    text = text.strip()
    return tags


def extract_at_users(text, platform: Platform) -> List[str]:
    """
    Extract @users from text.
    :param text: The text to extract @users from.
    :param platform: The platform of the text.
    :return: A List of @users.
    """
    if not isinstance(text, str):
        text = ""

    if platform == Platform.twitter:
        at_pattern = re.compile(r"@(\w+)")  # Twitter: 字母/数字/下划线
    elif platform == Platform.weibo:
        at_pattern = re.compile(r"@([^\s#]+)")  # 微博: 非空格和#的字符
    elif platform == Platform.rednote:
        at_pattern = re.compile(
            r"@([\w\u4e00-\u9fa5]+)"
        )  # 小红书: 中文/字母/数字/下划线
    else:
        return []

    at_users = at_pattern.findall(text)
    return [user.strip() for user in at_users]


def process_post_text(post: Post, platform: Platform):
    """
    Process the text of a post.
    :param post: The post to process.
    """
    # NOTE: 要先处理URL，因为URL也可能带井号
    urls = extract_urls(post.content.raw_text)
    tags = extract_tags(post.content.raw_text, platform)
    at_users = extract_at_users(post.content.raw_text, platform)
    post.content.urls = urls
    post.content.tags = tags
    post.content.at_users = at_users

    return post
