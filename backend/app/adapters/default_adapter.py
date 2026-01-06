"""
默认适配器
用于处理通用的 OpenAI 风格 API
"""
from typing import Optional
import logging
from .base_adapter import ApiAdapter

logger = logging.getLogger(__name__)


class DefaultAdapter(ApiAdapter):
    """
    默认适配器（通用格式）
    适用于标准的 OpenAI 风格 API
    """

    def build_submit_payload(self, task_payload: dict) -> dict:
        """构造通用请求体"""
        params = task_payload.get('params', {})

        return {
            "model": task_payload.get('model'),
            "prompt": task_payload.get('prompt', ''),
            **params
        }

    def is_async_task(self) -> bool:
        """默认假定为异步任务"""
        return True

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
            # 复用 T8StarVideoGenerationAdapter 的进度解析逻辑
            from .t8star_video_adapter import T8StarVideoGenerationAdapter
            progress = T8StarVideoGenerationAdapter._parse_progress(progress)
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
