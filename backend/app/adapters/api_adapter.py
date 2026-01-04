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
    T8Star (https://ai.t8star.cn) API 适配器

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
    # 规范化 URL（移除协议和路径，只保留域名）
    api_base_lower = api_base.lower()

    # T8Star 适配器
    if 'ai.t8star.cn' in api_base_lower or 't8star.cn' in api_base_lower:
        logger.info(f"Using T8StarAdapter for API base: {api_base}")
        return T8StarAdapter(api_base)

    # 未来可以在这里添加更多适配器
    # elif 'api.openai.com' in api_base_lower:
    #     return OpenAIAdapter(api_base)
    # elif 'another-provider.com' in api_base_lower:
    #     return AnotherAdapter(api_base)

    # 默认适配器
    logger.info(f"Using DefaultAdapter for API base: {api_base}")
    return DefaultAdapter(api_base)
