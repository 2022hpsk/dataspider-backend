import json
import urllib.request
import time
from typing import Optional


def make_request(
    url: str, method: str = "GET", data: dict = None, timeout: int = 30
) -> tuple:
    """通用请求函数"""
    try:
        headers = {"Content-Type": "application/json"} if data else {}

        if data:
            json_data = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(
                url, data=json_data, headers=headers, method=method
            )
        else:
            req = urllib.request.Request(url, method=method)

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, body
    except Exception as e:
        return None, str(e)


def test_start_keyword_task():
    """测试启动关键词爬虫任务"""
    print("\n=== 测试启动关键词爬虫任务 ===")
    url = "http://localhost:8000/api/v1/scrape"
    payload = {
        "mode": "keyword",
        "platform": "xhs",
        "keyword": "测试",
        "start_date": "2025-06-01",
        "end_date": "2025-06-02",
        "max_pages": 1,
        "output_dir": "C:/Users/lenovo/Desktop/out",
    }

    status, response = make_request(url, "POST", payload)
    print(f"状态码: {status}")
    print(f"响应: {response}")

    if status == 200:
        try:
            data = json.loads(response)
            task_id = data.get("task_id")
            print(f"任务ID: {task_id}")
            return task_id
        except:
            print("解析响应失败")
            return None
    return None


def test_start_user_task():
    """测试启动用户推文爬虫任务"""
    print("\n=== 测试启动用户推文爬虫任务 ===")
    url = "http://localhost:8000/api/v1/scrape"
    payload = {
        "mode": "user",
        "platform": "twitter",
        "user_id": "7284785243",
        "start_date": "2024-06-01",
        "end_date": "2025-10-17",
        "max_pages": 1,
    }

    status, response = make_request(url, "POST", payload)
    print(f"状态码: {status}")
    print(f"响应: {response}")

    if status == 200:
        try:
            data = json.loads(response)
            task_id = data.get("task_id")
            print(f"任务ID: {task_id}")
            return task_id
        except:
            print("解析响应失败")
            return None
    return None


def test_start_tweet_task():
    """测试启动单条推文爬虫任务"""
    print("\n=== 测试启动单条推文爬虫任务 ===")
    url = "http://localhost:8000/api/v1/scrape"
    payload = {"mode": "tweet", "platform": "twitter", "tweet_id": "abcdef123456"}

    status, response = make_request(url, "POST", payload)
    print(f"状态码: {status}")
    print(f"响应: {response}")

    if status == 200:
        try:
            data = json.loads(response)
            task_id = data.get("task_id")
            print(f"任务ID: {task_id}")
            return task_id
        except:
            print("解析响应失败")
            return None
    return None


def test_get_task_status(task_id: str):
    """测试查看任务状态"""
    print(f"\n=== 测试查看任务状态 (ID: {task_id}) ===")
    url = f"http://localhost:8000/api/v1/task/{task_id}"

    status, response = make_request(url, "GET")
    print(f"状态码: {status}")
    print(f"响应: {response}")

    if status == 200:
        try:
            data = json.loads(response)
            task_status = data.get("status", "unknown")
            print(f"任务状态: {task_status}")
            return data
        except:
            print("解析响应失败")
    return None


def test_list_all_tasks():
    """测试查看所有任务"""
    print("\n=== 测试查看所有任务 ===")
    url = "http://localhost:8000/api/v1/tasks"

    status, response = make_request(url, "GET")
    print(f"状态码: {status}")
    print(f"响应: {response}")

    if status == 200:
        try:
            data = json.loads(response)
            tasks = data.get("tasks", {})
            print(f"当前任务数量: {len(tasks)}")
            for task_id, task_info in tasks.items():
                print(
                    f"  任务 {task_id}: {task_info.get('status', 'unknown')} - {task_info.get('spider_name', 'unknown')}"
                )
            return tasks
        except:
            print("解析响应失败")
    return None


def test_stop_task(task_id: str):
    """测试停止任务"""
    print(f"\n=== 测试停止任务 (ID: {task_id}) ===")
    url = f"http://localhost:8000/api/v1/stop/{task_id}"

    status, response = make_request(url, "POST")
    print(f"状态码: {status}")
    print(f"响应: {response}")

    return status == 200


def test_invalid_requests():
    """测试无效请求"""
    print("\n=== 测试无效请求 ===")

    # 测试缺少必要参数
    print("1. 测试缺少keyword参数")
    url = "http://localhost:8000/api/v1/scrape"
    payload = {"mode": "keyword"}
    status, response = make_request(url, "POST", payload)
    print(f"状态码: {status}, 响应: {response}")

    # 测试无效模式
    print("2. 测试无效模式")
    payload = {"mode": "invalid_mode"}
    status, response = make_request(url, "POST", payload)
    print(f"状态码: {status}, 响应: {response}")

    # 测试查看不存在的任务
    print("3. 测试查看不存在的任务")
    url = "http://localhost:8000/api/v1/scrape/task/nonexistent-task-id"
    status, response = make_request(url, "GET")
    print(f"状态码: {status}, 响应: {response}")

    # 测试停止不存在的任务
    print("4. 测试停止不存在的任务")
    url = "http://localhost:8000/api/v1/scrape/stop/nonexistent-task-id"
    status, response = make_request(url, "POST")
    print(f"状态码: {status}, 响应: {response}")


def main():
    """主测试流程"""
    print("开始API测试...")

    # 1. 测试启动不同类型的任务
    task_ids = []

    # 启动关键词任务
    keyword_task_id = test_start_keyword_task()
    if keyword_task_id:
        task_ids.append(keyword_task_id)

    # # 启动用户任务
    # user_task_id = test_start_user_task()
    # if user_task_id:
    #     task_ids.append(user_task_id)

    # # 启动推文任务
    # tweet_task_id = test_start_tweet_task()
    # if tweet_task_id:
    #     task_ids.append(tweet_task_id)

    # 2. 查看所有任务
    test_list_all_tasks()

    # 3. 等待一段时间让任务开始运行
    if task_ids:
        print(f"\n等待11秒让任务开始运行...")
        time.sleep(11)

        # 4. 查看任务状态
        for task_id in task_ids:
            test_get_task_status(task_id)

        # 5. 停止第一个任务
        if len(task_ids) > 0:
            test_stop_task(task_ids[0])

            # 等待停止生效
            time.sleep(5)

            # 再次查看状态
            test_get_task_status(task_ids[0])

    # 6. 再次查看所有任务
    # test_list_all_tasks()

    # 7. 测试无效请求
    # test_invalid_requests()

    print("\n=== API测试完成 ===")


if __name__ == "__main__":
    main()
