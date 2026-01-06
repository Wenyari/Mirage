"""
T8Star 视频生成适配器
支持 https://ai.t8star.cn/v2/videos/generations
"""
from typing import Optional
import logging
from .base_adapter import ApiAdapter

logger = logging.getLogger(__name__)


class T8StarVideoGenerationAdapter(ApiAdapter):
    """
    T8Star 视频生成适配器（异步）
    API: https://ai.t8star.cn/v2/videos/generations

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
            logger.error(f"T8Star Video: No task_id in submit response: {response_data}")
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
                logger.warning(f"T8Star Video: SUCCESS but no result_url in response: {response_data}")

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
