"""
API 适配器基类
定义所有适配器的通用接口
"""
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
