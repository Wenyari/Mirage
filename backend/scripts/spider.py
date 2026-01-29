import asyncio
import httpx
import boto3
import json
import os
import uuid
import time
from io import BytesIO
from PIL import Image
import ffmpeg  # wrapper for ffmpeg-python
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
PUBLIC_DOMAIN = "https://pub-826107e0701d495a8c5318616ce8ac43.r2.dev"

# 爬虫设置
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DOWNLOAD_TIMEOUT = 60  # 下载大视频的超时时间

# ================= R2 工具函数 =================
def get_r2_client():
    return boto3.client('s3', config=Config(signature_version='s3v4'), **R2_CONFIG)

def upload_bytes_to_r2(data_bytes: BytesIO, key: str, content_type: str):
    """上传内存数据到 R2"""
    r2 = get_r2_client()
    try:
        data_bytes.seek(0)
        r2.upload_fileobj(
            Fileobj=data_bytes,
            Bucket=BUCKET_NAME,
            Key=key,
            ExtraArgs={
                'ContentType': content_type,
                'CacheControl': 'max-age=31536000' # 设置缓存一年
            }
        )
        return f"{PUBLIC_DOMAIN}/{key}"
    except Exception as e:
        print(f"[R2 Upload Error] {key}: {e}")
        return None

def upload_file_to_r2(file_path: str, key: str, content_type: str):
    """上传本地文件到 R2"""
    r2 = get_r2_client()
    try:
        with open(file_path, 'rb') as f:
            r2.upload_fileobj(
                Fileobj=f,
                Bucket=BUCKET_NAME,
                Key=key,
                ExtraArgs={
                    'ContentType': content_type,
                    'CacheControl': 'max-age=31536000'
                }
            )
        return f"{PUBLIC_DOMAIN}/{key}"
    except Exception as e:
        print(f"[R2 Upload Error] {key}: {e}")
        return None

# ================= 媒体处理核心逻辑 =================

async def process_image(client, img_url):
    """处理图片：下载 -> 获取宽高 -> 上传 R2"""
    try:
        print(f"   -> 正在下载图片: {img_url[:30]}...")
        resp = await client.get(img_url)
        if resp.status_code != 200:
            print(f"   [Error] 下载失败 status: {resp.status_code}")
            return None

        image_data = BytesIO(resp.content)
        
        # 1. 使用 Pillow 读取元数据
        with Image.open(image_data) as img:
            width, height = img.size
            fmt = img.format.lower()
            
        # 2. 生成 R2 路径 (按年月归档)
        ext = f".{fmt}" if fmt else ".jpg"
        date_str = datetime.now().strftime("%Y%m")
        file_uuid = uuid.uuid4().hex
        r2_key = f"images/{date_str}/{file_uuid}{ext}"
        
        # 3. 上传
        # 注意：Image.open 可能会移动指针，重新上传前需 reset
        image_data.seek(0)
        r2_url = await asyncio.to_thread(upload_bytes_to_r2, image_data, r2_key, f"image/{fmt}")
        
        if r2_url:
            return {
                "width": width,
                "height": height,
                "aspect_ratio": round(width / height, 2),
                "r2_key": r2_key,
                "r2_url": r2_url,
                "cover_r2_key": None, # 图片不需要独立封面
                "cover_r2_url": None
            }
    except Exception as e:
        print(f"   [Exception] 图片处理出错: {e}")
    return None

async def process_video(client, video_url):
    """处理视频：下载 -> 保存临时文件 -> ffmpeg提取封面/宽高 -> 上传 -> 清理"""
    temp_video = f"temp_{uuid.uuid4().hex}.mp4"
    temp_cover = f"temp_{uuid.uuid4().hex}.jpg"
    
    try:
        print(f"   -> 正在下载视频: {video_url[:30]}...")
        async with client.stream('GET', video_url) as resp:
            if resp.status_code != 200:
                return None
            with open(temp_video, "wb") as f:
                async for chunk in resp.aiter_bytes():
                    f.write(chunk)
        
        # 1. 获取视频信息 (宽高)
        probe = ffmpeg.probe(temp_video)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        
        # 2. 截取封面 (取第1秒)
        (
            ffmpeg
            .input(temp_video, ss=1)
            .filter('scale', width, -1) # 保持原宽
            .output(temp_cover, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # 3. 生成 R2 路径
        date_str = datetime.now().strftime("%Y%m")
        file_uuid = uuid.uuid4().hex
        video_key = f"videos/{date_str}/{file_uuid}.mp4"
        cover_key = f"covers/{date_str}/{file_uuid}.jpg"
        
        # 4. 上传 (使用线程避免阻塞异步循环)
        print("   -> 正在上传视频和封面到 R2...")
        video_r2_url = await asyncio.to_thread(upload_file_to_r2, temp_video, video_key, "video/mp4")
        cover_r2_url = await asyncio.to_thread(upload_file_to_r2, temp_cover, cover_key, "image/jpeg")
        
        if video_r2_url and cover_r2_url:
            return {
                "width": width,
                "height": height,
                "aspect_ratio": round(width / height, 2),
                "r2_key": video_key,
                "r2_url": video_r2_url,
                "cover_r2_key": cover_key,
                "cover_r2_url": cover_r2_url
            }

    except ffmpeg.Error as e:
        print(f"   [FFmpeg Error] {e.stderr.decode('utf8')}")
    except Exception as e:
        print(f"   [Exception] 视频处理出错: {e}")
    finally:
        # 清理临时文件
        if os.path.exists(temp_video): os.remove(temp_video)
        if os.path.exists(temp_cover): os.remove(temp_cover)
    
    return None

# ================= 业务逻辑 =================

async def mock_fetch_from_source():
    """
    [开发替换点]
    这里应该替换为你真实的爬虫代码 (Playwright 或 httpx 解析 HTML)。
    为了演示，这里返回模拟数据。
    """
    await asyncio.sleep(1) # 模拟网络延迟
    return [
        {
            "source_id": "demo_vid_001",
            "prompt_en": "A cinematic shot of a cyberpunk city with neon lights, rain, 8k resolution",
            "prompt_zh": "", # 假设源站没有中文
            "type": "video",
            # 请替换为真实可访问的测试链接
            "url": "https://www.w3schools.com/html/mov_bbb.mp4" 
        },
        {
            "source_id": "demo_img_001",
            "prompt_en": "A cute cat sitting on a laptop, anime style",
            "prompt_zh": "一只坐在笔记本电脑上的可爱猫咪，动漫风格",
            "type": "image",
            # 请替换为真实可访问的测试链接
            "url": "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
        }
    ]

async def main():
    print("=== 开始 GoGen 采集任务 ===")
    
    # 1. 获取源数据
    items = await mock_fetch_from_source()
    print(f"获取到 {len(items)} 条源数据")
    
    processed_results = []
    
    async with httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT, headers={"User-Agent": USER_AGENT}) as client:
        for item in items:
            print(f"\n正在处理: {item['source_id']} ({item['type']})")
            
            meta = None
            if item['type'] == 'video':
                meta = await process_video(client, item['url'])
            elif item['type'] == 'image':
                meta = await process_image(client, item['url'])
            
            if meta:
                # 简单处理中文翻译 (如果没有)
                final_zh = item['prompt_zh']
                if not final_zh and item['prompt_en']:
                    # 这里可以接入 googletrans 或 LLM API
                    final_zh = "[待翻译] " + item['prompt_en'] 

                result_entry = {
                    "source_id": item['source_id'],
                    "media_type": item['type'],
                    "prompt_en": item['prompt_en'],
                    "prompt_zh": final_zh,
                    "negative_prompt": "", # 暂时留空
                    
                    # 混入处理后的元数据 (width, height, urls...)
                    **meta
                }
                processed_results.append(result_entry)
                print(f"   [成功] {item['source_id']} 处理完成")
            else:
                print(f"   [失败] {item['source_id']} 处理失败，跳过")

    # 2. 保存为 JSON
    output_file = "local_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(processed_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 任务完成 ===")
    print(f"成功采集: {len(processed_results)} 条")
    print(f"数据已保存至: {os.path.abspath(output_file)}")
    print("下一步: 请使用 scp 将此 JSON 文件发送到服务器入库。")

if __name__ == "__main__":
    asyncio.run(main())