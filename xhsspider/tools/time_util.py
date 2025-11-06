import time
from datetime import datetime, timedelta, timezone
import re


def get_current_timestamp() -> int:
    """
    获取当前的时间戳(13 位)：1701493264496
    :return:
    """
    return int(time.time() * 1000)


def get_current_time() -> str:
    """
    获取当前的时间：'2023-12-02 13:01:23'
    :return:
    """
    return time.strftime("%Y-%m-%d %X", time.localtime())


def get_current_date() -> str:
    """
    获取当前的日期：'2023-12-02'
    :return:
    """
    return time.strftime("%Y-%m-%d", time.localtime())


def get_time_str_from_unix_time(unixtime):
    """
    unix 整数类型时间戳  ==> 字符串日期时间
    :param unixtime:
    :return:
    """
    if int(unixtime) > 1000000000000:
        unixtime = int(unixtime) / 1000
    return time.strftime("%Y-%m-%d %X", time.localtime(unixtime))


def get_date_str_from_unix_time(unixtime):
    """
    unix 整数类型时间戳  ==> 字符串日期
    :param unixtime:
    :return:
    """
    if int(unixtime) > 1000000000000:
        unixtime = int(unixtime) / 1000
    return time.strftime("%Y-%m-%d", time.localtime(unixtime))


def get_unix_time_from_time_str(time_str):
    """
    字符串时间 ==> unix 整数类型时间戳，精确到秒
    :param time_str:
    :return:
    """
    try:
        format_str = "%Y-%m-%d %H:%M:%S"
        tm_object = time.strptime(str(time_str), format_str)
        return int(time.mktime(tm_object))
    except Exception as e:
        return 0
    pass


def get_unix_timestamp():
    return int(time.time())


def rfc2822_to_china_datetime(rfc2822_time):
    # 定义RFC 2822格式
    rfc2822_format = "%a %b %d %H:%M:%S %z %Y"

    # 将RFC 2822时间字符串转换为datetime对象
    dt_object = datetime.strptime(rfc2822_time, rfc2822_format)

    # 将datetime对象的时区转换为中国时区
    dt_object_china = dt_object.astimezone(timezone(timedelta(hours=8)))
    return dt_object_china


def rfc2822_to_timestamp(rfc2822_time):
    # 定义RFC 2822格式
    rfc2822_format = "%a %b %d %H:%M:%S %z %Y"

    # 将RFC 2822时间字符串转换为datetime对象
    dt_object = datetime.strptime(rfc2822_time, rfc2822_format)

    # 将datetime对象转换为UTC时间
    dt_utc = dt_object.replace(tzinfo=timezone.utc)

    # 计算UTC时间对应的Unix时间戳
    timestamp = int(dt_utc.timestamp())

    return timestamp


def parse_xhs_time(time_str: str) -> str:
    """
    解析小红书时间字符串为标准日期格式 YYYY-MM-DD
    """
    now = datetime.now()
    time_str = time_str.strip()

    # 1. 刚刚
    if time_str == "刚刚":
        return now.strftime("%Y-%m-%d")

    # 2. x分钟前
    match = re.match(r"(\d+)分钟前", time_str)
    if match:
        minutes = int(match.group(1))
        dt = now - timedelta(minutes=minutes)
        return dt.strftime("%Y-%m-%d")

    # 3. x小时前
    match = re.match(r"(\d+)小时前", time_str)
    if match:
        hours = int(match.group(1))
        dt = now - timedelta(hours=hours)
        return dt.strftime("%Y-%m-%d")

    # 4. x天前
    match = re.match(r"(\d+)天前", time_str)
    if match:
        days = int(match.group(1))
        dt = now - timedelta(days=days)
        return dt.strftime("%Y-%m-%d")

    # 5. 昨天 / 前天
    if time_str == "昨天":
        dt = now - timedelta(days=1)
        return dt.strftime("%Y-%m-%d")
    if time_str == "前天":
        dt = now - timedelta(days=2)
        return dt.strftime("%Y-%m-%d")

    # 6. x个月前
    match = re.match(r"(\d+)个月前", time_str)
    if match:
        months = int(match.group(1))
        year = now.year
        month = now.month - months
        while month <= 0:
            month += 12
            year -= 1
        dt = now.replace(year=year, month=month)
        return dt.strftime("%Y-%m-%d")

    # 7. x年前
    match = re.match(r"(\d+)年前", time_str)
    if match:
        years = int(match.group(1))
        dt = now.replace(year=now.year - years)
        return dt.strftime("%Y-%m-%d")

    # 8. MM-DD（补上当前年份）
    match = re.match(r"(\d{1,2})-(\d{1,2})", time_str)
    if match:
        month, day = map(int, match.groups())
        dt = datetime(now.year, month, day)
        # 处理跨年情况（如今天是1月，而帖子是12-25）
        if dt > now:
            dt = dt.replace(year=now.year - 1)
        return dt.strftime("%Y-%m-%d")

    # 9. YYYY-MM-DD（已完整）
    match = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", time_str)
    if match:
        return time_str

    # 10. 默认返回当前日期（无法识别的格式）
    return now.strftime("%Y-%m-%d")


if __name__ == "__main__":
    # 示例用法
    _rfc2822_time = "Sat Dec 23 17:12:54 +0800 2023"
    print(rfc2822_to_china_datetime(_rfc2822_time))
