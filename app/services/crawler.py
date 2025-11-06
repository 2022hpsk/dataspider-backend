import os
import sys
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, Optional
from app import config

logger = logging.getLogger("weibospider_crawler")


def run_spider(
    spider: str, params: Dict[str, str], timeout: int = 60 * 30
) -> Optional[str]:
    platform = params.get("platform", "").lower()
    output_dir = params.get("output_dir", None)
    # output_path 变为用户可传入
    if "output_dir" in params and params["output_dir"]:
        output_dir = params["output_dir"]
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        fname = f"{platform}_{spider}_{ts}.jsonl"
        output_path = os.path.join(output_dir, fname)
    else:
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        fname = f"{platform}_{spider}_{ts}.jsonl"
        if platform == "weibo":
            output_path = os.path.join(config.WEIBO_OUTPUT, fname)
        elif platform == "twitter":
            output_path = os.path.join(config.TWITTER_OUTPUT, fname)
        elif platform == "xhs":
            output_path = os.path.join(config.XHS_OUTPUT, fname)

    # 根据 platform 参数决定使用哪个 run_spider.py（如 platform == "weibo" 则使用 weibo 路径下的 run_spider.py）

    run_spider_py = None
    if platform == "weibo":
        cwd_BASE = config.WEIBO_BASE
        run_spider_py = os.path.join(config.WEIBO_BASE, "run_spider.py")
    elif platform == "twitter":
        cwd_BASE = config.TWITTER_BASE
        run_spider_py = os.path.join(config.TWITTER_BASE, "run_spider.py")
    elif platform == "xhs":
        cwd_BASE = config.XHS_BASE
        run_spider_py = os.path.join(config.XHS_BASE, "run_spider.py")
    else:
        # wrong or missing platform, raise error
        raise ValueError(f"Unsupported platform: {platform}")
    args_json = json.dumps(params, ensure_ascii=False)
    if run_spider_py and os.path.exists(run_spider_py):
        if platform == "weibo":
            cmd = [
                sys.executable,
                run_spider_py,
                "--spider",
                spider,
                "--output",
                output_path,
                "--args_json",
                args_json,
            ]
        elif platform == "twitter":
            cmd = [
                sys.executable,
                run_spider_py,
                "--mode",
                params.get("mode", "keyword"),
                "--keyword",
                params.get("keyword", ""),
                "--start",
                params.get("start_date", ""),
                "--end",
                params.get("end_date", ""),
                "--output_dir",
                output_dir,
            ]
        elif platform == "xhs":
            cmd = [
                sys.executable,
                run_spider_py,
                "--mode",
                params.get("mode", "keyword"),
                "--keyword",
                params.get("keyword", ""),
            ]
    else:
        cmd = [sys.executable, "-m", "scrapy", "crawl", spider, "-o", output_path]
        for k, v in params.items():
            cmd += ["-a", f"{k}={v}"]

    logger.info("Running command: %s", " ".join(cmd))

    try:
        # 使用 Popen 进行流式输出
        with subprocess.Popen(
            cmd,
            cwd=cwd_BASE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
        ) as proc:
            # 只记录到日志文件，不输出到控制台
            logfile = output_path + ".run.log"
            with open(logfile, "w", encoding="utf-8") as lf:
                try:
                    for line in proc.stdout:
                        if line is None:
                            break
                        # 只写入日志文件
                        lf.write(line)
                        lf.flush()

                    # 等待进程结束
                    retcode = proc.wait(timeout=timeout)

                except subprocess.TimeoutExpired:
                    proc.kill()
                    logger.error("Spider %s timed out and was killed", spider)
                    return None

            if proc.returncode != 0:
                logger.error(
                    "Spider process exited with code %s, see %s",
                    proc.returncode,
                    logfile,
                )
                return None

        # 检查输出文件是否存在
        if os.path.exists(output_path):
            logger.info("Spider completed successfully, output: %s", output_path)
            return output_path
        else:
            logger.warning("Output file not found: %s", output_path)
            return None

    except Exception as e:
        error_log = output_path + ".err.log"
        with open(error_log, "w", encoding="utf-8") as f:
            f.write(f"Exception: {repr(e)}\n")
            f.write(f"CMD: {' '.join(cmd)}\n")
        logger.error("Error running spider: %s", e)
        return None
