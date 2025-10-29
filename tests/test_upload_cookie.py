import json
import uuid
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

def encode_multipart_formdata(fields: Dict[str, str], files: Dict[str, Tuple[str, bytes, str]]) -> Tuple[bytes, str]:
    """
    fields: { name: value(str) }
    files:  { name: (filename(str), content(bytes), content_type(str)) }
    return: (body_bytes, content_type_header_value)
    """
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    crlf = "\r\n"
    lines: List[bytes] = []

    # 普通表单字段
    for name, value in (fields or {}).items():
        lines.append(f"--{boundary}".encode("utf-8"))
        lines.append(f'Content-Disposition: form-data; name="{name}"'.encode("utf-8"))
        lines.append(b"")
        lines.append(str(value).encode("utf-8"))

    # 文件字段
    for name, (filename, content, content_type) in (files or {}).items():
        lines.append(f"--{boundary}".encode("utf-8"))
        lines.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode("utf-8")
        )
        lines.append(f"Content-Type: {content_type or 'application/octet-stream'}".encode("utf-8"))
        lines.append(b"")
        lines.append(content)

    lines.append(f"--{boundary}--".encode("utf-8"))
    lines.append(b"")

    body = crlf.encode("utf-8").join(lines)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type

def make_multipart_request(url: str, fields: Dict[str, str], files: Dict[str, Tuple[str, bytes, str]], timeout: int = 30) -> Tuple[Optional[int], str]:
    """发送 multipart/form-data 请求"""
    try:
        body, content_type = encode_multipart_formdata(fields, files)
        headers = {"Content-Type": content_type, "Content-Length": str(len(body))}
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body_text = resp.read().decode("utf-8", errors="ignore")
            return resp.status, body_text
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            err_body = str(e)
        return e.code, err_body
    except Exception as e:
        return None, str(e)

def test_upload_cookie_weibo():
    """测试上传 weibo 的 cookie.txt"""
    print("\n=== 测试上传 weibo cookie.txt ===")
    url = "http://localhost:8000/api/v1/upload_cookie"

    cookie_content = "hahahah"
    # 新接口接收 cookie 字符串作为表单字段 'cookie'
    files = {}
    fields = {"platform": "weibo", "cookie": cookie_content}

    status, response = make_multipart_request(url, fields, files)
    print(f"状态码: {status}")
    print(f"响应: {response}")

    if status == 200:
        try:
            data: Dict[str, Any] = json.loads(response)
            assert data.get("status") == "ok", "status 非 ok"
            assert data.get("platform") == "weibo", "platform 非 weibo"

            # 优先使用服务端返回的写入路径进行校验
            returned_path = data.get("path")
            if returned_path:
                p = Path(returned_path)
            else:
                # 兼容：根据项目结构推断路径
                p = Path(__file__).resolve().parents[1] / "weibospider" / "cookie.txt"

            if p.exists():
                on_disk = p.read_text(encoding="utf-8", errors="ignore")
                print(f"写入路径: {p}")
                print(f"写入的 cookie.txt 长度: {len(on_disk)}")
            else:
                print(f"未找到写入的 cookie.txt 文件: {p}")
        except Exception as e:
            print(f"解析/断言失败: {e}")

def test_upload_cookie_unsupported_platform():
    """测试不支持的平台"""
    print("\n=== 测试上传 不支持的平台 cookie.txt ===")
    url = "http://localhost:8000/api/v1/upload_cookie"

    cookie_content = "k=v"
    files = {}
    fields = {"platform": "unknown", "cookie": cookie_content}

    status, response = make_multipart_request(url, fields, files)
    print(f"状态码: {status}")
    print(f"响应: {response}")

def test_upload_cookie_missing_platform():
    """测试缺少 platform 字段"""
    print("\n=== 测试上传 缺少 platform 字段 ===")
    url = "http://localhost:8000/api/v1/upload_cookie"

    cookie_content = "k=v"
    files = {}
    fields = {"cookie": cookie_content}  # 缺少 platform

    status, response = make_multipart_request(url, fields, files)
    print(f"状态码: {status}")
    print(f"响应: {response}")

def test_upload_cookie_missing_file():
    """测试缺少文件"""
    print("\n=== 测试上传 缺少 cookie_file ===")
    url = "http://localhost:8000/api/v1/upload_cookie"

    # 对应新接口，此用例表示缺少 cookie 字段
    files = {}
    fields = {"platform": "weibo"}  # 缺少 cookie

    status, response = make_multipart_request(url, fields, files)
    print(f"状态码: {status}")
    print(f"响应: {response}")

def main():
    print("开始 upload_cookie 接口测试...")
    test_upload_cookie_weibo()
    test_upload_cookie_unsupported_platform()
    test_upload_cookie_missing_platform()
    test_upload_cookie_missing_file()
    print("\n=== upload_cookie 接口测试完成 ===")

if __name__ == "__main__":
    main()