import threading
import time
import uuid
from typing import Dict, Optional
from datetime import datetime
from app.services.crawler import run_spider
import ctypes
class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.running_threads: Dict[str, threading.Thread] = {}
        self.stop_flags: Dict[str, threading.Event] = {}
    
    def start_crawl_task(self, spider_name: str, spider_args: Dict[str, str]) -> str:
        """启动爬虫任务，返回任务ID"""
        task_id = str(uuid.uuid4())
        
        # 创建停止标志
        stop_event = threading.Event()
        self.stop_flags[task_id] = stop_event
        
        # 创建任务信息
        task_info = {
            "task_id": task_id,
            "spider_name": spider_name,
            "spider_args": spider_args,
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "result": None
        }
        self.tasks[task_id] = task_info
        
        # 创建并启动线程
        thread = threading.Thread(
            target=self._run_crawl_task,
            args=(task_id, spider_name, spider_args, stop_event)
        )
        thread.daemon = True
        self.running_threads[task_id] = thread
        thread.start()
        
        return task_id
    
    def _run_crawl_task(self, task_id: str, spider_name: str, spider_args: Dict[str, str], 
                        stop_event: threading.Event):
        """执行爬虫任务的内部方法"""
        try:
            print(f"Starting crawl task {task_id} with:", spider_name, spider_args)
            result = {"status": "failed", "inserted": 0, "output_file": None, "error": None}
            
            # 检查是否需要停止
            if stop_event.is_set():
                result["status"] = "cancelled"
                result["error"] = "Task was cancelled before starting"
                self.tasks[task_id]["result"] = result
                self.tasks[task_id]["status"] = "cancelled"
                return
            print(f"Task {task_id}: Running spider..., spider_name:", spider_name, "args:", spider_args)
            
            # 运行爬虫，传入stop_event以便中途停止
            output = run_spider_with_stop(spider_name, spider_args, stop_event)
            
            print(f"Task {task_id}: Spider output file:", output)

            # 检查是否需要停止
            if stop_event.is_set():
                result["status"] = "cancelled"
                result["error"] = "Task was cancelled during spider execution"
                self.tasks[task_id]["result"] = result
                self.tasks[task_id]["status"] = "cancelled"
                return
            
            if not output:
                result["error"] = "spider failed or produced no output"
                self.tasks[task_id]["result"] = result
                self.tasks[task_id]["status"] = "failed"
                return
            
            result["output_file"] = output
            try:
                # 读取输出文件中数据的数量（数据文件是jsonl格式）
                with open(output, "r", encoding="utf-8") as f:
                    inserted = sum(1 for _ in f)
                result["inserted"] = inserted
                result["status"] = "completed"
                print(f"Task {task_id}: Completed successfully, crawl {inserted} records")
            except Exception as e:
                result["error"] = str(e)
                result["status"] = "failed"
                print(f"Task {task_id}: failed: {e}")

            
            self.tasks[task_id]["result"] = result
            self.tasks[task_id]["status"] = result["status"]
            
        except Exception as e:
            print(f"Task {task_id}: Unexpected error: {e}")
            self.tasks[task_id]["result"] = {"status": "failed", "error": str(e)}
            self.tasks[task_id]["status"] = "failed"
        finally:
            # 清理
            if task_id in self.running_threads:
                del self.running_threads[task_id]
            if task_id in self.stop_flags:
                del self.stop_flags[task_id]
    
    def stop_task(self, task_id: str) -> bool:
        """停止指定任务"""
        if task_id in self.stop_flags:
            self.stop_flags[task_id].set()
            self.tasks[task_id]["status"] = "stopping"
            print(f"Stop signal sent to task {task_id}")
            thread = self.running_threads.get(task_id)
            if thread.is_alive():
                # 强行终止线程
                try:
                    tid = thread.ident
                    if tid is None:
                        print("Cannot obtain thread id; cannot force kill.")
                    else:
                        # 向线程抛出 SystemExit 异常
                        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                        ctypes.c_long(tid), ctypes.py_object(SystemExit)
                        )
                        if res == 1:
                            print(f"Raised SystemExit in thread {tid}")
                        else:
                        # 如果返回值不是1，撤销操作
                            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
                            print(f"Failed to raise exception in thread {tid} (res={res})")
                except Exception as e:
                    print(f"Force kill failed: {e}")

            print(f"Task {task_id} has been stopped.")
            #将task信息状态改为stopped
            self.tasks[task_id]["status"] = "stopped"
            return True
        return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        return self.tasks.get(task_id)
    
    def list_tasks(self) -> Dict[str, Dict]:
        """列出所有任务"""
        return self.tasks
    
    def cleanup_finished_tasks(self):
        """清理已完成的任务（可选）"""
        finished_tasks = [
            task_id for task_id, task in self.tasks.items()
            if task["status"] in ["completed", "failed", "cancelled"]
        ]
        for task_id in finished_tasks:
            if task_id not in self.running_threads:  # 确保线程已结束
                del self.tasks[task_id]

# 全局任务管理器实例
task_manager = TaskManager()

def run_spider_with_stop(spider_name: str, spider_args: Dict[str, str], stop_event: threading.Event):
    """支持停止的爬虫运行函数"""
    from app.services.crawler import run_spider

    
    # 这里可以进一步优化，在爬虫执行过程中定期检查stop_event
    # 目前简单实现：如果收到停止信号，直接返回None
    if stop_event.is_set():
        return None
    
    # 实际运行爬虫
    return run_spider(spider_name, spider_args)