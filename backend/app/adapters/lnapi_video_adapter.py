"""
LnAPI 视频生成适配器
支持 https://lnapi.com/v1/videos 及其查询接口
"""
from typing import Optional
import logging
from .base_adapter import ApiAdapter

logger = logging.getLogger(__name__)


class LnapiVideoGenerationAdapter(ApiAdapter):
    """
    LnAPI 视频生成适配器（异步）
    适用模型：veo 系列、grok 系列、sora 系列等
    API: https://lnapi.com/v1/videos
    
    提交响应示例：
    {
        "id": "veo3-fast-frames:1757555257-PORrVn9sa9",
        "status": "pending",
        "status_update_time": 1757555257582
    }
    
    状态查询响应示例：
    {
        "id": "veo3.1-fast:1770350082-trii1OXZc3",
        "status": "completed",
        "video_url": "https://pro.filesystem.site/cdn/.../xxx.mp4",
        "enhanced_prompt": "...",
        "status_update_time": 1770350329098,
        "detail": {
            "status": "completed",
            "error_message": "...",
            ...
        }
    }
    """

    def build_submit_payload(self, task_payload: dict) -> dict:
        """构造视频生成请求体"""
        params = task_payload.get('params', {})
        
        # 处理 images 字段，将 input_file_url 转换为 images
        images = params.get('images', [])
        if not images and task_payload.get('input_file_url'):
            input_url = task_payload['input_file_url']
            images = [input_url] if isinstance(input_url, str) else input_url

        # 构造请求体
        payload = {
            "model": task_payload.get('model'),
            "prompt": task_payload.get('prompt', ''),
            **params
        }
        if images:
            payload["images"] = images
            
        return payload

    def is_async_task(self) -> bool:
        """视频生成是异步任务"""
        return True

    def get_polling_config(self) -> dict:
        """获取轮询配置"""
        # 智能处理状态 URL，因为提交是 /v1/videos，查询是 /v1/video/query
        base = self.api_base.split('|')[1] if '|' in self.api_base else self.api_base
        if base.endswith('/videos'):
            base = base[:-7] + '/video/query'
        elif base.endswith('/videos/'):
            base = base[:-8] + '/video/query'
            
        # 如果 pattern 中不包含 {base}，worker.py format 时会直接忽略它
        pattern = base + "?id={task_id}"
        
        # 对于已经包含 {task_id} 的 base（如果用户使用了 | 语法配置了完整的带参数的 query URL）
        if '{task_id}' in base:
            pattern = base
            
        return {
            "max_timeout": 600,  # 10 分钟
            "interval": 3,       # 3 秒
            "status_url_pattern": pattern
        }

    def parse_submit_response(self, response_data: dict) -> Optional[str]:
        """提取上游任务ID"""
        task_id = response_data.get('id')
        if not task_id:
            logger.error(f"LnAPI Video: No id in submit response: {response_data}")
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
            'PENDING': 'RUNNING',
            'RUNNING': 'RUNNING',
            'PROCESSING': 'RUNNING',
            'IN_PROGRESS': 'RUNNING'
        }
        
        raw_status = response_data.get('status', '').upper()
        normalized_status = status_map.get(raw_status, 'RUNNING')
        
        # 2. 结果 URL 提取
        result_url = response_data.get('video_url')
        
        # 尝试从 detail 中提取
        detail = response_data.get('detail', {})
        if not result_url and isinstance(detail, dict):
            result_url = detail.get('video_url')
            
        if normalized_status == 'SUCCESS' and not result_url:
            logger.warning(f"LnAPI Video: SUCCESS but no video_url in response: {response_data}")
            
        # 3. 失败原因
        fail_reason = None
        if normalized_status == 'FAILED':
            if isinstance(detail, dict):
                fail_reason = detail.get('error_message') or detail.get('video_generation_error')
            if not fail_reason:
                fail_reason = response_data.get('error_message') or response_data.get('fail_reason')
                
        # 4. 进度估算（因为 API 未提供具体百分比，我们可以用固定值代替）
        progress = 100 if normalized_status == 'SUCCESS' else (0 if normalized_status == 'FAILED' else 50)
        
        return {
            'status': normalized_status,
            'progress': progress,
            'result_url': result_url,
            'fail_reason': fail_reason
        }
