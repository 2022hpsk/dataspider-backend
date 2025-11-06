# 已完成修改20250717


def safe_to_non_negative_int(value) -> int | None:
    """
    安全地将值转换为非负整数：
    - 如果已经是非负整数，直接返回
    - 如果是非负整数字符串（如 "100"），转换为整数
    - 其他情况返回-1，表示未获取到有效值
    """
    if isinstance(value, int):
        if value >= 0:  # 仅接受非负整数
            return value
    elif isinstance(value, str):
        if value.isdigit():  # 仅接受非负整数字符串
            return int(value)
    return -1


def parse_xhs_like_count(like_str) -> int:
    """
    处理小红书点赞数字符串，转换成整数数值。

    示例输入:
    "1.2万+", "3.5千+", "888+", "500"

    返回:
    12000, 3500, 888, 500
    """
    if not like_str:
        return 0

    like_str = str(like_str).replace("+", "").strip()

    multiplier_map = {
        "万": 10_000,
        "千": 1_000,
        "亿": 100_000_000,
        # 可以继续扩展
    }

    # 先找单位
    for unit, multiplier in multiplier_map.items():
        if like_str.endswith(unit):
            try:
                number_part = float(like_str[: -len(unit)])
                return int(number_part * multiplier)
            except ValueError:
                return 0

    # 没有单位，直接转换数字
    try:
        return int(like_str)
    except ValueError:
        return 0
