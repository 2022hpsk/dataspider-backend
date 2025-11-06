import asyncio
import pathlib
import aiofiles
from tools import utils
from var import crawler_type_var


class RednoteJsonlStoreImplement:


    # jsonl_store_path: str = "output"
    # jsonl_store_path: str = "data/rednote/jsonl"
    lock = asyncio.Lock()

    # @classmethod
    # def make_save_file_name(cls, store_type: str):
    #     """生成保存文件名"""
    #     return f"{cls.jsonl_store_path}/{crawler_type_var.get()}_{store_type}_{utils.get_current_date()}.jsonl"

    @classmethod
    async def save_data_to_jsonl(cls, save_item, store_type: str):
        """保存数据到 JSONL 文件"""
            #如果output.txt存在，读取 output.txt 中的路径作为存储路径
        jsonl_store_path: str
        try:
            with open('output.txt', 'r', encoding='utf-8') as f:
                jsonl_store_path = f.read().strip()
        except FileNotFoundError:
            raise Exception("output.txt not found. Please ensure the output path is set.")
        # pathlib.Path(cls.jsonl_store_path).mkdir(parents=True, exist_ok=True)
        # save_file_name = cls.make_save_file_name(store_type=store_type)
        save_file_name = jsonl_store_path

        async with cls.lock:
            async with aiofiles.open(save_file_name, "a", encoding="utf-8") as file:
                # 使用 json() 确保数据正确序列化，并禁用 ASCII 转义
                line = save_item.json(ensure_ascii=False)
                await file.write(line + "\n")
                await file.flush()  # 确保数据写入磁盘

    @classmethod
    async def store_content(cls, content_item):
        """存储内容"""
        await cls.save_data_to_jsonl(content_item, "contents")

    @classmethod
    async def store_comment(cls, comment_item):
        """存储评论"""
        await cls.save_data_to_jsonl(comment_item, "comments")

    @classmethod
    async def store_creator(cls, creator):
        """存储创作者"""
        await cls.save_data_to_jsonl(creator, "creator")
