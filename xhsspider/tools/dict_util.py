# 已完成修改20250717
# 安全获取多层键值，单层则使用dict默认的get
def safe_get(obj: dict, key: str, default: object = None):
    """
    :param obj: the dict
    :param key: "x.y.z" for sub dicts
    :param default: default value if key not found
    """
    if "." not in key:
        return obj.get(key, default)
    keys = key.split(".")
    section = obj
    for k in keys:
        if k not in section:
            return default
        section = section[k]
