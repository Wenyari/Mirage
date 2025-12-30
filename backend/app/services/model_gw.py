"""
模型网关 (Model Gateway)
屏蔽底层模型差异，提供统一的调用接口
支持: OpenAI Sora, Midjourney 等
"""
import requests
from flask import current_app
from app.config import Config


class ModelGateway:
    """模型网关基类"""

    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.endpoint = Config.SORA_API_ENDPOINT

    def call_model(self, model_name: str, prompt: str, params: dict = None) -> dict:
        """
        调用模型生成

        Args:
            model_name: 模型名称
            prompt: 提示词
            params: 其他参数

        Returns:
            dict: {"job_id": "...", "status": "pending"}

        Raises:
            Exception: 调用失败
        """
        raise NotImplementedError("Subclass must implement call_model")

    def get_job_status(self, job_id: str) -> dict:
        """
        查询任务状态

        Args:
            job_id: 上游任务 ID

        Returns:
            dict: {"status": "success/failed/processing", "result_url": "..."}
        """
        raise NotImplementedError("Subclass must implement get_job_status")


class SoraGateway(ModelGateway):
    """第三方 Sora API 网关"""

    def __init__(self):
        super().__init__()
        # API基础URL (可配置，便于切换不同的API提供商)
        from app.config import Config
        self.api_base_url = Config.SORA_API_BASE_URL

    def call_model(self, model_name: str, prompt: str, params: dict = None) -> dict:
        """
        调用第三方 Sora API

        API端点: {api_base_url}/v2/videos/generations
        """
        params = params or {}

        # 第三方API端点
        url = f"{self.api_base_url}/v2/videos/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 构建请求体 (根据第三方API规范)
        payload = {
            "prompt": prompt,
            "model": model_name,  # sora-2, sora-2-pro
            "aspect_ratio": params.get('aspect_ratio', '16:9'),  # 16:9, 9:16
            "hd": params.get('hd', False),  # true/false (仅sora-2-pro支持)
            "duration": str(params.get('duration', 10)),  # "10", "15", "25"
            "watermark": False,
            "private": False
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            return {
                "job_id": data.get('task_id'),  # 第三方API返回task_id
                "status": "pending"
            }

        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Sora API call failed: {e}")
            raise Exception(f"Failed to call Sora API: {str(e)}")

    def get_job_status(self, job_id: str) -> dict:
        """
        查询第三方 Sora 任务状态

        API端点: {api_base_url}/v2/videos/generations/{task_id}
        """
        url = f"{self.api_base_url}/v2/videos/generations/{job_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            # 获取任务状态
            status = data.get('status')

            # 映射状态到系统内部状态
            if status == 'SUCCESS':
                # 成功完成
                video_url = data.get('data', {}).get('output')
                return {
                    "status": "success",
                    "result_url": video_url
                }
            elif status == 'FAILURE':
                # 任务失败
                fail_reason = data.get('fail_reason', 'Unknown error')
                return {
                    "status": "failed",
                    "fail_reason": fail_reason
                }
            else:
                # IN_PROGRESS, NOT_START 或其他状态
                return {
                    "status": "processing",
                    "result_url": None
                }

        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Sora API status check failed: {e}")
            return {
                "status": "failed",
                "fail_reason": f"API error: {str(e)}"
            }


class MidjourneyGateway(ModelGateway):
    """Midjourney 网关 (示例)"""

    def call_model(self, model_name: str, prompt: str, params: dict = None) -> dict:
        """
        调用 Midjourney API
        TODO: 根据实际 MJ API 实现
        """
        # 示例实现
        return {
            "job_id": "mj_job_123",
            "status": "pending"
        }

    def get_job_status(self, job_id: str) -> dict:
        """
        查询 Midjourney 任务状态
        TODO: 根据实际 MJ API 实现
        """
        return {
            "status": "processing",
            "result_url": None
        }


# 模型网关工厂
def get_gateway(model_name: str) -> ModelGateway:
    """
    根据模型名称获取对应的网关

    Args:
        model_name: 模型名称

    Returns:
        ModelGateway: 对应的网关实例
    """
    if 'sora' in model_name.lower():
        return SoraGateway()
    elif 'midjourney' in model_name.lower() or 'mj' in model_name.lower():
        return MidjourneyGateway()
    else:
        raise ValueError(f"Unsupported model: {model_name}")
