"""
上游 API 适配器
用于处理不同上游 API 的响应格式差异

每个适配器负责：
1. 解析提交响应，提取 task_id
2. 解析轮询响应，标准化为统一格式
"""
import re
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ApiAdapter:
    """API 适配器基类"""

    def __init__(self, api_base: str):
        self.api_base = api_base

    # ========== 新增方法：支持同步/异步任务 ==========

    def build_submit_payload(self, task_payload: dict) -> dict:
        """
        构造提交请求体

        Args:
            task_payload: 从队列取出的任务数据
                {
                    "task_id": "...",
                    "model": "sora-2",
                    "prompt": "...",
                    "params": {...},
                    "input_file_url": "..."
                }

        Returns:
            dict: 上游 API 的请求体
                示例（视频）: {
                    "model": "sora-2",
                    "prompt": "...",
                    "images": [...],
                    "duration": 5
                }
                示例（图片）: {
                    "model": "dall-e-3",
                    "prompt": "...",
                    "size": "1024x1024"
                }
        """
        raise NotImplementedError

    def is_async_task(self) -> bool:
        """
        判断是否是异步任务（需要轮询）

        Returns:
            bool: True=异步任务，需要轮询进度
                  False=同步任务，直接返回结果
        """
        raise NotImplementedError

    def get_polling_config(self) -> dict:
        """
        获取轮询配置（仅异步任务需要）

        Returns:
            dict: {
                "max_timeout": 600,   # 最长轮询时间（秒）
                "interval": 3,        # 轮询间隔（秒）
                "status_url_pattern": "{base}/{task_id}"  # URL 模板
            }
        """
        return {
            "max_timeout": 600,
            "interval": 3,
            "status_url_pattern": "{base}/{task_id}"
        }

    def parse_sync_response(self, response_data: dict) -> dict:
        """
        解析同步响应（仅同步任务需要）

        Args:
            response_data: 提交响应的 JSON 数据

        Returns:
            dict: {
                "result_url": "https://...",  # 结果链接
                "result_urls": ["https://..."],  # 多个结果（图片生成可能返回多张）
                "metadata": {...}  # 其他元数据
            }
        """
        return {
            "result_url": None,
            "result_urls": [],
            "metadata": {}
        }

    # ========== 已有方法保持不变 ==========

    def parse_submit_response(self, response_data: dict) -> Optional[str]:
        """
        解析提交响应，提取上游任务ID

        Args:
            response_data: 上游 API 提交响应的 JSON 数据

        Returns:
            str: 上游任务ID，如果解析失败返回 None
        """
        raise NotImplementedError

    def parse_status_response(self, response_data: dict) -> dict:
        """
        解析状态查询响应，标准化为统一格式

        Args:
            response_data: 上游 API 状态查询响应的 JSON 数据

        Returns:
            dict: 标准化的状态数据
            {
                "status": str,  # RUNNING | SUCCESS | FAILED
                "progress": int,  # 0-100
                "result_url": str | None,  # 成功时的结果链接
                "fail_reason": str | None  # 失败时的原因
            }
        """
        raise NotImplementedError


class T8StarAdapter(ApiAdapter):
    """
    T8Star (https://ai.t8star.cn//v2/videos/generations) API 适配器

    提交响应示例：
    {
        "task_id": "veo3:1756693796-YQVHH4A3Lg",
        ...
    }

    状态响应示例：
    {
        "task_id": "veo3:1756693796-YQVHH4A3Lg",
        "status": "SUCCESS",  # SUCCESS | FAILED | RUNNING | PENDING
        "progress": "100%",  # 字符串格式
        "fail_reason": "",
        "data": {
            "output": "https://filesystem.site/cdn/..."  # 直接是 URL 字符串
        }
    }
    """

    def build_submit_payload(self, task_payload: dict) -> dict:
        """构造视频生成请求体"""
        params = task_payload.get('params', {})

        # 处理 images 字段
        images = params.get('images', [])
        if not images and task_payload.get('input_file_url'):
            input_url = task_payload['input_file_url']
            images = [input_url] if isinstance(input_url, str) else input_url

        return {
            "model": task_payload.get('model'),
            "prompt": task_payload.get('prompt', ''),
            "images": images,
            **params  # duration, aspect_ratio 等参数
        }

    def is_async_task(self) -> bool:
        """视频生成是异步任务"""
        return True

    def get_polling_config(self) -> dict:
        """视频生成轮询配置"""
        return {
            "max_timeout": 600,  # 10 分钟
            "interval": 3,       # 3 秒
            "status_url_pattern": "{base}/{task_id}"
        }

    def parse_submit_response(self, response_data: dict) -> Optional[str]:
        """提取上游任务ID"""
        task_id = response_data.get('task_id')
        if not task_id:
            logger.error(f"T8Star: No task_id in submit response: {response_data}")
            return None
        return task_id

    def parse_status_response(self, response_data: dict) -> dict:
        """解析状态响应"""
        # 1. 状态映射
        status_map = {
            'SUCCESS': 'SUCCESS',
            'SUCCEEDED': 'SUCCESS',
            'COMPLETED': 'SUCCESS',
            'FAILED': 'FAILED',
            'FAILURE': 'FAILED',
            'ERROR': 'FAILED',
            'RUNNING': 'RUNNING',
            'PROCESSING': 'RUNNING',
            'PENDING': 'RUNNING',
            'IN_PROGRESS': 'RUNNING'
        }

        raw_status = response_data.get('status', '').upper()
        normalized_status = status_map.get(raw_status, 'RUNNING')

        # 2. 进度解析（字符串 "100%" -> 整数 100）
        progress_str = response_data.get('progress', '0')
        progress = self._parse_progress(progress_str)

        # 3. 结果 URL 提取
        result_url = None
        if normalized_status == 'SUCCESS':
            # T8Star 的结果在 data.output 中，且是字符串而不是对象
            data = response_data.get('data', {})
            if isinstance(data, dict):
                output = data.get('output')
                if isinstance(output, str):
                    result_url = output
                elif isinstance(output, dict):
                    result_url = output.get('url')

            if not result_url:
                logger.warning(f"T8Star: SUCCESS but no result_url in response: {response_data}")

        # 4. 失败原因
        fail_reason = response_data.get('fail_reason') or None

        return {
            'status': normalized_status,
            'progress': progress,
            'result_url': result_url,
            'fail_reason': fail_reason
        }

    @staticmethod
    def _parse_progress(progress_str) -> int:
        """
        解析进度字符串为整数

        支持格式：
        - "100%"
        - "50.5%"
        - 100 (已经是整数)
        - "100" (字符串数字)
        """
        if isinstance(progress_str, int):
            return max(0, min(100, progress_str))

        if isinstance(progress_str, float):
            return max(0, min(100, int(progress_str)))

        if isinstance(progress_str, str):
            # 移除百分号和空格
            cleaned = progress_str.strip().rstrip('%')

            # 尝试解析为浮点数
            try:
                value = float(cleaned)
                return max(0, min(100, int(value)))
            except ValueError:
                logger.warning(f"Cannot parse progress: {progress_str}, defaulting to 0")
                return 0

        logger.warning(f"Unexpected progress type: {type(progress_str)}, defaulting to 0")
        return 0


class T8StarImageGenerationAdapter(T8StarAdapter):
    """
    T8Star 图片生成适配器 (https://ai.t8star.cn/v1/images/generations)

    继承自 T8StarAdapter，使用相同的响应格式

    提交响应示例：
    {
        "task_id": "flux:1756693796-XXXXX",
        ...
    }

    状态响应示例：
    {
        "task_id": "flux:1756693796-XXXXX",
        "status": "SUCCESS",
        "progress": "100%",
        "fail_reason": "",
        "data": {
            "output": "https://filesystem.site/cdn/..."
        }
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


class T8StarImageEditAdapter(T8StarAdapter):
    """
    T8Star 图片编辑适配器 (https://ai.t8star.cn/v1/images/edits)

    继承自 T8StarAdapter，使用相同的响应格式

    提交响应示例：
    {
        "task_id": "edit:1756693796-XXXXX",
        ...
    }

    状态响应示例：
    {
        "task_id": "edit:1756693796-XXXXX",
        "status": "SUCCESS",
        "progress": "100%",
        "fail_reason": "",
        "data": {
            "output": "https://filesystem.site/cdn/..."
        }
    }
    """

    def build_submit_payload(self, task_payload: dict) -> dict:
        """构造图片编辑请求体"""
        params = task_payload.get('params', {})

        payload = {
            "model": task_payload.get('model'),
            "prompt": task_payload.get('prompt', ''),
        }

        # 添加必需和可选参数
        if 'image' in params:
            payload['image'] = params['image']
        if 'mask' in params:
            payload['mask'] = params['mask']
        if 'size' in params:
            payload['size'] = params['size']
        if 'n' in params:
            payload['n'] = params['n']

        # 添加其他参数（排除已处理的）
        excluded_keys = {'image', 'mask', 'size', 'n'}
        for k, v in params.items():
            if k not in excluded_keys:
                payload[k] = v

        return payload

    def is_async_task(self) -> bool:
        """图片编辑是同步任务"""
        return False

    def parse_sync_response(self, response_data: dict) -> dict:
        """解析同步响应（与图片生成相同）"""
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


class DefaultAdapter(ApiAdapter):
    """
    默认适配器（通用格式）

    适用于标准的 OpenAI 风格 API
    """

    def parse_submit_response(self, response_data: dict) -> Optional[str]:
        """提取上游任务ID"""
        # 尝试多种可能的字段名
        for key in ['task_id', 'id', 'taskId', 'request_id']:
            if key in response_data:
                return response_data[key]

        logger.error(f"Default: No task ID found in submit response: {response_data}")
        return None

    def parse_status_response(self, response_data: dict) -> dict:
        """解析状态响应"""
        # 状态映射
        status_map = {
            'SUCCESS': 'SUCCESS',
            'SUCCEEDED': 'SUCCESS',
            'COMPLETED': 'SUCCESS',
            'DONE': 'SUCCESS',
            'FAILED': 'FAILED',
            'ERROR': 'FAILED',
            'RUNNING': 'RUNNING',
            'PROCESSING': 'RUNNING',
            'PENDING': 'RUNNING',
            'IN_PROGRESS': 'RUNNING',
        }

        raw_status = response_data.get('status', '').upper()
        normalized_status = status_map.get(raw_status, 'RUNNING')

        # 进度（假设是整数）
        progress = response_data.get('progress', 0)
        if isinstance(progress, str):
            progress = T8StarAdapter._parse_progress(progress)
        elif isinstance(progress, float):
            progress = int(progress)

        # 结果 URL（尝试多种路径）
        result_url = None
        if normalized_status == 'SUCCESS':
            result_url = (
                response_data.get('result_url') or
                response_data.get('output', {}).get('url') or
                response_data.get('video_url') or
                response_data.get('url')
            )

        # 失败原因
        fail_reason = response_data.get('fail_reason') or response_data.get('error')

        return {
            'status': normalized_status,
            'progress': progress,
            'result_url': result_url,
            'fail_reason': fail_reason
        }


def get_adapter(api_base: str) -> ApiAdapter:
    """
    根据 API Base URL 返回对应的适配器

    Args:
        api_base: API 基础 URL (如 "https://ai.t8star.cn/v2/videos/generations")

    Returns:
        ApiAdapter: 对应的适配器实例
    """
    # 规范化 URL
    api_base_lower = api_base.lower()

    # T8Star 适配器 - 使用精确路径匹配
    if 'ai.t8star.cn' in api_base_lower or 't8star.cn' in api_base_lower:
        # 图片生成
        if '/v1/images/generations' in api_base_lower:
            logger.info(f"Using T8StarImageGenerationAdapter for API base: {api_base}")
            return T8StarImageGenerationAdapter(api_base)

        # 图片编辑
        elif '/v1/images/edits' in api_base_lower:
            logger.info(f"Using T8StarImageEditAdapter for API base: {api_base}")
            return T8StarImageEditAdapter(api_base)

        # 视频生成（默认）
        elif '/v2/videos/generations' in api_base_lower:
            logger.info(f"Using T8StarAdapter (video) for API base: {api_base}")
            return T8StarAdapter(api_base)

        # 如果路径不匹配，默认使用视频适配器
        else:
            logger.warning(f"Unknown T8Star API path: {api_base}, using default T8StarAdapter")
            return T8StarAdapter(api_base)

    # 未来可以在这里添加更多适配器
    # elif 'api.openai.com' in api_base_lower:
    #     return OpenAIAdapter(api_base)
    # elif 'another-provider.com' in api_base_lower:
    #     return AnotherAdapter(api_base)

    # 默认适配器
    logger.info(f"Using DefaultAdapter for API base: {api_base}")
    return DefaultAdapter(api_base)
