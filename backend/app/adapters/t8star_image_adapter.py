"""
T8Star 图片生成适配器
支持 https://ai.t8star.cn/v1/images/generations
"""
import logging
from .t8star_video_adapter import T8StarVideoGenerationAdapter

logger = logging.getLogger(__name__)


class T8StarImageGenerationAdapter(T8StarVideoGenerationAdapter):
    """
    T8Star 图片生成适配器（同步）
    API: https://ai.t8star.cn/v1/images/generations

    继承自 T8StarVideoGenerationAdapter，复用状态解析逻辑

    提交响应示例：
    {
        "created": 1234567890,
        "data": [
            {"b64_json": "..." 或 "url": "https://..."}
        ]
    }
    """

    def build_submit_payload(self, task_payload: dict) -> dict:
        """构造图片生成请求体"""
        params = task_payload.get('params', {})

        # 图片生成可能有参考图
        image = params.get('image', [])

        payload = {
            "model": task_payload.get('model'),
            "prompt": task_payload.get('prompt', ''),
        }

        # 添加可选参数
        if 'size' in params:
            payload['size'] = params['size']
        if 'aspect_ratio' in params:
            payload['aspect_ratio'] = params['aspect_ratio']
        if image:
            payload['image'] = image

        # 添加其他参数（排除已处理的）
        excluded_keys = {'size', 'aspect_ratio', 'image'}
        for k, v in params.items():
            if k not in excluded_keys:
                payload[k] = v

        return payload

    def is_async_task(self) -> bool:
        """图片生成是同步任务"""
        return False

    def parse_sync_response(self, response_data: dict) -> dict:
        """解析同步响应"""
        # 假设响应格式：
        # {
        #   "created": 1234567890,
        #   "data": [
        #     {"b64_json": "..." 或 "url": "https://..."}
        #   ]
        # }
        data = response_data.get('data', [])
        result_urls = []

        for item in data:
            if isinstance(item, dict):
                if 'url' in item:
                    result_urls.append(item['url'])
                elif 'b64_json' in item:
                    # 将 base64 转换为 data URL
                    result_urls.append(f"data:image/png;base64,{item['b64_json']}")

        return {
            "result_url": result_urls[0] if result_urls else None,
            "result_urls": result_urls,
            "metadata": {
                "created": response_data.get('created'),
                "count": len(result_urls)
            }
        }
