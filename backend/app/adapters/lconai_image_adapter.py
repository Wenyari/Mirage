"""
LconAI 图片生成适配器
支持 https://n.lconai.com/v1/images/generations
"""
import logging
from .base_adapter import ApiAdapter

logger = logging.getLogger(__name__)


class LconaiImageGenerationAdapter(ApiAdapter):
    """
    LconAI 图片生成适配器（同步）
    API: https://n.lconai.com/v1/images/generations
    
    提交响应示例：
    {
        "created": 1753687182,
        "data": [
            {
                "url": "https://...",
                "revised_prompt": "..."
            }
        ],
        "usage": { ... }
    }
    """

    def build_submit_payload(self, task_payload: dict) -> dict:
        """构造图片生成请求体"""
        params = task_payload.get('params', {})
        
        # LconAI 的 API 中，编辑图片需要传入 image 数组
        # （可选，如果有的话）
        image = params.get('image', [])
        
        if not image and task_payload.get('input_file_url'):
            input_url = task_payload['input_file_url']
            image = [input_url] if isinstance(input_url, str) else input_url
        model_pre = task_payload.get('model', 'gpt-image-1.5')
        if model_pre == 'gpt-4o-image':
            model_pre = 'gpt-image-1.5'
        elif model_pre == 'nano-banana':
            model_pre = 'gemini-2.5-flash-image'
        elif model_pre == 'nano-banana-2':
            model_pre = 'gemini-3-pro-image-preview'
            
        payload = {
            "model": model_pre,
            "prompt": task_payload.get('prompt', ''),
            "response_format": "url"
        }

        # 添加主要参数
        
        # 转换宽高比和分辨率到明确的 size 参数
        aspect_ratio = params.get('aspect_ratio', '1:1')
        
        if model_pre == 'gemini-2.5-flash-image':
            # nano-banana (gemini-2.5-flash-image) mapping
            size_map = {
                '1:1': '1024x1024',
                '2:3': '832x1248',
                '3:2': '1248x832',
                '3:4': '864x1184',
                '4:3': '1184x864',
                '4:5': '896x1152',
                '5:4': '1152x896',
                '9:16': '768x1344',
                '16:9': '1344x768',
                '21:9': '1536x672'
            }
            if aspect_ratio in size_map:
                payload['size'] = size_map[aspect_ratio]
                
        elif model_pre == 'gemini-3-pro-image-preview':
            # nano-banana-2 (gemini-3-pro-image-preview) mapping
            image_size_str = params.get('image_size', '1K')
            
            size_map = {
                '1:1': {'1K': '1024x1024', '2K': '2048x2048', '4K': '4096x4096'},
                '1:4': {'1K': '512x2048', '2K': '1024x4096', '4K': '2048x8192'}, # added from gemini-3.1 spec if needed, else 1K mappings follow docs
                '1:8': {'1K': '384x3072', '2K': '768x6144', '4K': '1536x12288'},
                '2:3': {'1K': '848x1264', '2K': '1696x2528', '4K': '3392x5056'},
                '3:2': {'1K': '1264x848', '2K': '2528x1696', '4K': '5056x3392'},
                '3:4': {'1K': '896x1200', '2K': '1792x2400', '4K': '3584x4800'},
                '4:1': {'1K': '2048x512', '2K': '4096x1024', '4K': '8192x2048'},
                '4:3': {'1K': '1200x896', '2K': '2400x1792', '4K': '4800x3584'},
                '4:5': {'1K': '928x1152', '2K': '1856x2304', '4K': '3712x4608'},
                '5:4': {'1K': '1152x928', '2K': '2304x1856', '4K': '4608x3712'},
                '8:1': {'1K': '3072x384', '2K': '6144x768', '4K': '12288x1536'},
                '9:16': {'1K': '768x1376', '2K': '1536x2752', '4K': '3072x5504'},
                '16:9': {'1K': '1376x768', '2K': '2752x1536', '4K': '5504x3072'},
                '21:9': {'1K': '1584x672', '2K': '3168x1344', '4K': '6336x2688'}
            }
            if aspect_ratio in size_map and image_size_str in size_map[aspect_ratio]:
                payload['size'] = size_map[aspect_ratio][image_size_str]

        # Use explicitly provided size if it exists
        if 'size' in params:
            payload['size'] = params['size']
            
        if 'n' in params:
            payload['n'] = params['n']
        if 'response_format' in params:
            payload['response_format'] = params['response_format']
        if image:
            payload['image'] = image

        # 添加其他额外参数（排除已处理的）
        excluded_keys = {'size', 'image', 'n', 'response_format', 'aspect_ratio', 'image_size'}
        for k, v in params.items():
            if k not in excluded_keys:
                payload[k] = v

        return payload

    def is_async_task(self) -> bool:
        """图片生成是同步任务，直接返回生成的图片结果"""
        return False

    def parse_sync_response(self, response_data: dict) -> dict:
        """解析同步响应并返回统一的结构"""
        data = response_data.get('data', [])
        result_urls = []
        
        for item in data:
            if isinstance(item, dict):
                if 'url' in item:
                    result_urls.append(item['url'])
                elif 'b64_json' in item:
                    result_urls.append(f"data:image/png;base64,{item['b64_json']}")
                    
        return {
            "result_url": result_urls[0] if result_urls else None,
            "result_urls": result_urls,
            "metadata": {
                "created": response_data.get('created'),
                "count": len(result_urls)
            }
        }
