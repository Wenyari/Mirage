import asyncio
import httpx
import boto3
import json
import os
import uuid
import logging
from io import BytesIO
from PIL import Image
from botocore.config import Config
from datetime import datetime

# ================= 配置区域 =================
# 1. 从环境变量读取 R2 凭据，勿硬编码
MY_ACCOUNT_ID = os.environ["R2_ACCOUNT_ID"]
MY_ACCESS_KEY = os.environ["R2_ACCESS_KEY_ID"]
MY_SECRET_KEY = os.environ["R2_SECRET_ACCESS_KEY"]

# Cloudflare R2 S3 客户端配置
R2_CONFIG = {
    # 关键点：Endpoint 必须拼接成 https://<account_id>.r2.cloudflarestorage.com
    "endpoint_url": f"https://{MY_ACCOUNT_ID}.r2.cloudflarestorage.com",
    "aws_access_key_id": MY_ACCESS_KEY,
    "aws_secret_access_key": MY_SECRET_KEY,
    "region_name": "auto" # R2 自动识别区域，这就填 auto 即可
}

# 2. 桶名称
BUCKET_NAME = os.environ.get("R2_BUCKET_NAME", "assets")

# 3. 公网访问域名
# 注意：去掉末尾的斜杠，方便后面代码拼接
PUBLIC_DOMAIN = os.environ["R2_PUBLIC_URL"].rstrip("/")

# 并发限制 (防止一次性发起太多请求)
MAX_CONCURRENCY = 10

# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================= R2 工具函数 =================
def get_r2_client():
    return boto3.client('s3', config=Config(signature_version='s3v4'), **R2_CONFIG)

def upload_bytes_to_r2(data_bytes: BytesIO, key: str, content_type: str):
    """同步上传函数，将在线程池中运行"""
    r2 = get_r2_client()
    try:
        data_bytes.seek(0)
        r2.upload_fileobj(
            Fileobj=data_bytes,
            Bucket=BUCKET_NAME,
            Key=key,
            ExtraArgs={
                'ContentType': content_type,
                'CacheControl': 'max-age=31536000'
            }
        )
        return f"{PUBLIC_DOMAIN}/{key}"
    except Exception as e:
        logger.error(f"R2 Upload Error ({key}): {e}")
        return None

# ================= 核心处理逻辑 =================

async def process_single_item(item, client, semaphore):
    """
    处理单条数据：
    1. 标准化字段
    2. 如果有图片 URL，下载并上传 R2
    3. 返回标准化后的字典
    """
    async with semaphore:
        # 1. 基础字段映射 (标准化)
        normalized_item = {
            "source_id": item.get("source_id"),
            "title": item.get("title"),
            "media_type": item.get("media_type", "image"),
            "prompt_en": item.get("prompt_en"),
            "prompt_zh": item.get("prompt_zh"),
            "width": 0,
            "height": 0,
            "r2_keys": [],
            "r2_urls": [],
            "cover_r2_key": None,
            "cover_r2_url": None
        }

        # 2. 检查是否需要转存图片
        original_urls = item.get("original_image_url")
        
        # 兼容旧数据: 如果是字符串,转为数组
        if isinstance(original_urls, str):
            original_urls = [original_urls] if original_urls else []
        elif original_urls is None:
            original_urls = []
        
        # 如果有原图链接,且还没有被处理过 (防止重复处理)
        if original_urls and not item.get("r2_urls"):
            for idx, original_url in enumerate(original_urls):
                try:
                    logger.info(f"Downloading [{idx+1}/{len(original_urls)}]: {original_url[:50]}...")
                    resp = await client.get(original_url)
                    
                    if resp.status_code == 200:
                        image_data = BytesIO(resp.content)
                        
                        # A. 获取尺寸 (使用第一张图片的尺寸)
                        if idx == 0:
                            try:
                                with Image.open(image_data) as img:
                                    normalized_item["width"], normalized_item["height"] = img.size
                                    fmt = img.format.lower()
                            except Exception:
                                fmt = "jpg" # 默认 fallback
                        else:
                            # 后续图片只获取格式
                            try:
                                image_data.seek(0)
                                with Image.open(image_data) as img:
                                    fmt = img.format.lower()
                            except Exception:
                                fmt = "jpg"
                                
                        # B. 上传 R2
                        date_str = datetime.now().strftime("%Y%m")
                        file_uuid = uuid.uuid4().hex
                        key = f"images/{date_str}/{file_uuid}.{fmt}"
                        
                        # 使用线程池执行同步的 boto3 上传
                        r2_url = await asyncio.to_thread(upload_bytes_to_r2, image_data, key, f"image/{fmt}")
                        
                        if r2_url:
                            normalized_item["r2_keys"].append(key)
                            normalized_item["r2_urls"].append(r2_url)
                            
                            # 第一张图片作为封面
                            if idx == 0:
                                normalized_item["cover_r2_key"] = key
                                normalized_item["cover_r2_url"] = r2_url
                            
                            logger.info(f" -> Uploaded [{idx+1}/{len(original_urls)}]: {key}")
                        else:
                            logger.warning(f" -> Upload Failed [{idx+1}/{len(original_urls)}]: {original_url}")
                    else:
                        logger.warning(f" -> Download Failed ({resp.status_code}) [{idx+1}/{len(original_urls)}]: {original_url}")
                except Exception as e:
                    logger.error(f" -> Processing Error [{idx+1}/{len(original_urls)}]: {e}")
        
        return normalized_item

async def main():
    # 1. 读取所有源文件
    files = [
        "github_data_test.json", 
        "youmind_data_test.json", 
        "sora2_data.json"
    ]
    
    all_raw_data = []
    for filename in files:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} items from {filename}")
                all_raw_data.extend(data)
        else:
            logger.warning(f"File not found: {filename}, skipping.")

    logger.info(f"Total items to process: {len(all_raw_data)}")
    
    # 1.5. 删除旧的 R2 图片 (如果存在 final_data_to_sync.json)
    output_filename = "final_data_to_sync.json"
    if os.path.exists(output_filename):
        logger.info("=" * 30)
        logger.info("CLEANING OLD R2 FILES")
        try:
            with open(output_filename, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            
            old_r2_keys = []
            for item in old_data:
                # 支持旧格式(字符串)和新格式(数组)
                r2_key = item.get('r2_key') or item.get('r2_keys')
                if r2_key:
                    if isinstance(r2_key, list):
                        old_r2_keys.extend(r2_key)
                    elif isinstance(r2_key, str):
                        old_r2_keys.append(r2_key)
                
                # 封面图也可能需要删除
                cover_key = item.get('cover_r2_key')
                if cover_key and cover_key not in old_r2_keys:
                    old_r2_keys.append(cover_key)
            
            if old_r2_keys:
                logger.info(f"Found {len(old_r2_keys)} old R2 files to delete")
                r2 = get_r2_client()
                
                # 批量删除(R2 S3 API 每次最多删除 1000 个)
                deleted_count = 0
                failed_count = 0
                
                for i in range(0, len(old_r2_keys), 1000):
                    batch = old_r2_keys[i:i+1000]
                    try:
                        delete_objects = [{'Key': key} for key in batch]
                        response = r2.delete_objects(
                            Bucket=BUCKET_NAME,
                            Delete={'Objects': delete_objects}
                        )
                        deleted_count += len(response.get('Deleted', []))
                        failed_count += len(response.get('Errors', []))
                    except Exception as e:
                        logger.error(f"Batch delete error: {e}")
                        failed_count += len(batch)
                
                logger.info(f"Deleted: {deleted_count}, Failed: {failed_count}")
            else:
                logger.info("No old R2 files to delete")
        except Exception as e:
            logger.warning(f"Failed to clean old R2 files: {e}")
        logger.info("=" * 30)
    
    # 2. 并发处理
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = []
    
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for item in all_raw_data:
            task = process_single_item(item, client, semaphore)
            tasks.append(task)
        
        # 等待所有任务完成
        processed_results = await asyncio.gather(*tasks)

    # 3. 过滤无效数据 (可选: 如果 source_id 丢失)
    final_data = [item for item in processed_results if item.get("source_id")]

    # 4. 保存最终结果
    output_filename = "final_data_to_sync.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    logger.info("="*30)
    logger.info("PROCESSING COMPLETE")
    logger.info(f"Successfully processed: {len(final_data)} items")
    logger.info(f"Output saved to: {os.path.abspath(output_filename)}")
    logger.info("Now you can SCP this file to your server and run the importer.")
    logger.info("="*30)

if __name__ == "__main__":
    if "你的ACCOUNT_ID" in R2_CONFIG["endpoint_url"]:
        logger.error("Please configure your R2 credentials in the code first!")
    else:
        asyncio.run(main())