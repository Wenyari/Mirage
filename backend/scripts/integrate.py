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
# 1. 填入你的变量
MY_ACCOUNT_ID = "***REMOVED***"       # 对应 R2_ACCOUNT_ID
MY_ACCESS_KEY = "***REMOVED***"    # 对应 R2_ACCESS_KEY_ID
MY_SECRET_KEY = "***REMOVED***"# 对应 R2_SECRET_ACCESS_KEY

# Cloudflare R2 S3 客户端配置
R2_CONFIG = {
    # 关键点：Endpoint 必须拼接成 https://<account_id>.r2.cloudflarestorage.com
    "endpoint_url": f"https://{MY_ACCOUNT_ID}.r2.cloudflarestorage.com",
    "aws_access_key_id": MY_ACCESS_KEY,
    "aws_secret_access_key": MY_SECRET_KEY,
    "region_name": "auto" # R2 自动识别区域，这就填 auto 即可
}

# 2. 桶名称
BUCKET_NAME = "assets"  # 对应你的 R2_BUCKET_NAME

# 3. 公网访问域名
# 注意：去掉末尾的斜杠，方便后面代码拼接
PUBLIC_DOMAIN = "https://pub-a68a295d454b46b694db9db8b1272806.r2.dev"

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
            "r2_key": None,
            "r2_url": None,
            "cover_r2_key": None,
            "cover_r2_url": None
        }

        # 2. 检查是否需要转存图片
        original_url = item.get("original_image_url")
        
        # 如果有原图链接，且还没有被处理过 (防止重复处理)
        if original_url and not item.get("r2_url"):
            try:
                logger.info(f"Downloading: {original_url[:30]}...")
                resp = await client.get(original_url)
                
                if resp.status_code == 200:
                    image_data = BytesIO(resp.content)
                    
                    # A. 获取尺寸
                    try:
                        with Image.open(image_data) as img:
                            normalized_item["width"], normalized_item["height"] = img.size
                            fmt = img.format.lower()
                    except Exception:
                        fmt = "jpg" # 默认 fallback
                        
                    # B. 上传 R2
                    date_str = datetime.now().strftime("%Y%m")
                    file_uuid = uuid.uuid4().hex
                    key = f"images/{date_str}/{file_uuid}.{fmt}"
                    
                    # 使用线程池执行同步的 boto3 上传
                    r2_url = await asyncio.to_thread(upload_bytes_to_r2, image_data, key, f"image/{fmt}")
                    
                    if r2_url:
                        normalized_item["r2_key"] = key
                        normalized_item["r2_url"] = r2_url
                        logger.info(f" -> Uploaded: {key}")
                    else:
                        logger.warning(f" -> Upload Failed: {original_url}")
                else:
                    logger.warning(f" -> Download Failed ({resp.status_code}): {original_url}")
            except Exception as e:
                logger.error(f" -> Processing Error: {e}")
        
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