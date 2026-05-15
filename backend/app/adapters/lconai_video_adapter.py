"""
LconAI 视频生成适配器
支持 https://n.lconai.com/v1/videos 等接口
"""
from typing import Optional
import logging
from .base_adapter import ApiAdapter

logger = logging.getLogger(__name__)


class LconaiVideoGenerationAdapter(ApiAdapter):
    """
    LconAI 视频生成适配器（异步）
    适用模型：veo 系列、sora 系列等
    API: https://n.lconai.com/v1/videos
    
    提交响应示例：
    {
        "id": "video_bbfbc1d2-...",
        "object": "video",
        "model": "sora_video2",
        "status": "queued",
        "progress": 0,
        "created_at": 1761635478,
        "size": "720x720"
    }
    
    状态查询响应示例：
    {
        "id": "...",
        "status": "completed",
        "progress": 100,
        "video_url": "...",
        "error": {
            "message": "...",
            "code": "..."
        }
    }
    """

    def build_submit_payload(self, task_payload: dict) -> dict:
        """构造视频生成请求体"""
        params = task_payload.get('params', {})
        
        payload = {
            "model": task_payload.get('model'),
            "prompt": task_payload.get('prompt', '')
        }

        # 处理图片参考
        images = params.get('images', [])
        if not images and task_payload.get('input_file_url'):
            input_url = task_payload['input_file_url']
            images = [input_url] if isinstance(input_url, str) else input_url

        if images:
            # LconAI 的 API 支持 images(数组) 和 image(单图) 以及 input_reference
            # 这里统一传递 images
            payload["images"] = images

        # 根据不同模型会有不同的参数区分
        model_name = task_payload.get('model', '').lower()
        
        # 将通用的 aspect_ratio 转换为 LconAI 需要的 size 参数
        if 'aspect_ratio' in params and 'size' not in params:
            aspect_ratio = params['aspect_ratio']
            if aspect_ratio == '16:9':
                payload['size'] = '1280x720'
            elif aspect_ratio == '9:16':
                payload['size'] = '720x1280'
            elif aspect_ratio == '1:1':
                payload['size'] = '720x720'
                
        # 传递剩余的所有参数
        excluded = {'images', 'aspect_ratio'}
        for k, v in params.items():
            if k not in excluded:
                payload[k] = v

        return payload

    def is_async_task(self) -> bool:
        """视频生成是异步任务"""
        return True

    def get_polling_config(self) -> dict:
        """获取轮询配置"""
        return {
            "max_timeout": 900,  # 视频生成可能较慢，设置 15 分钟
            "interval": 5,       # 5 秒轮询一次
            "status_url_pattern": "{base}/{task_id}"
        }

    def parse_submit_response(self, response_data: dict) -> Optional[str]:
        """提取上游任务ID"""
        task_id = response_data.get('id')
        if not task_id:
            logger.error(f"LconAI Video: No id in submit response: {response_data}")
            return None
        return task_id

    def parse_status_response(self, response_data: dict) -> dict:
        """解析状态响应"""
        # 1. 状态映射
        status_map = {
            'COMPLETED': 'SUCCESS',
            'SUCCESS': 'SUCCESS',
            'SUCCEEDED': 'SUCCESS',
            'FAILED': 'FAILED',
            'ERROR': 'FAILED',
            'CANCELLED': 'FAILED',
            'QUEUED': 'RUNNING',
            'PENDING': 'RUNNING',
            'RUNNING': 'RUNNING',
            'PROCESSING': 'RUNNING',
            'IN_PROGRESS': 'RUNNING'
        }
        
        raw_status = response_data.get('status', '').upper()
        normalized_status = status_map.get(raw_status, 'RUNNING')
        
        # 2. 结果 URL 提取
        result_url = response_data.get('video_url')
            
        if normalized_status == 'SUCCESS' and not result_url:
            logger.warning(f"LconAI Video: SUCCESS but no video_url in response: {response_data}")
            
        # 3. 失败原因
        fail_reason = None
        if normalized_status == 'FAILED':
            error_obj = response_data.get('error', {})
            if isinstance(error_obj, dict):
                fail_reason = error_obj.get('message') or str(error_obj)
            else:
                fail_reason = response_data.get('error')
                
        # 4. 进度
        progress = response_data.get('progress', 0)
        if normalized_status == 'SUCCESS':
            progress = 100
        elif normalized_status == 'FAILED':
            progress = 0
            
        # 安全转换进度为整数
        try:
            progress = int(progress)
        except (ValueError, TypeError):
            progress = 0
        
        return {
            'status': normalized_status,
            'progress': progress,
            'result_url': result_url,
            'fail_reason': fail_reason
        }
