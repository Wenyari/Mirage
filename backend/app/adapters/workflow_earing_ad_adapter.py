import json
import logging
import uuid
from typing import Dict, Optional
from pathlib import Path

from .base_adapter import ApiAdapter

logger = logging.getLogger(__name__)

class WorkflowEaringAdAdapter(ApiAdapter):
    """
    针对 workflow-earing-ad 的 ComfyUI 适配器
    请求后端提供的 ComfyUI API 并处理执行进度
    """

    def __init__(self, api_base: str):
        super().__init__(api_base)
        # 加载工作流模板
        template_path = Path(__file__).parent.parent / "workflows" / "workflow-earing-ad.json"
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                self.workflow_template = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load workflow template: {e}")
            self.workflow_template = {}

    def build_submit_payload(self, task_payload: dict) -> dict:
        """
        构造提交给 ComfyUI /prompt 接口的请求体
        """
        import copy
        workflow = copy.deepcopy(self.workflow_template)

        # 提取动态参数
        prompt = task_payload.get("prompt", "")
        api_base = task_payload.get("api_base", "")
        api_key = task_payload.get("api_key", "")
        
        input_images = task_payload.get("input_file_url", [])
        if isinstance(input_images, str):
            input_images = [input_images]
            
        params = task_payload.get("params", {})

        # TODO: 将动态参数替换到 workflow 的对应节点
        # 27 节点: input_file_url 里的第一张图
        if input_images and "27" in workflow:
            # 确保传递的是 URL，如果是一个相对路径或本地文件，可能需要拼接 OSS 域名
            if "inputs" in workflow["27"]:
                workflow["27"]["inputs"]["value"] = input_images[0]
                
        # 35 节点: api_base
        if "35" in workflow:
            if "inputs" in workflow["35"]:
                workflow["35"]["inputs"]["value"] = api_base
                
        # 36 节点: api_key
        if "36" in workflow:
            if "inputs" in workflow["36"]:
                workflow["36"]["inputs"]["value"] = api_key

        # 如果未来你指定了要拼接待替换变量 prompt_template (节点 12) 或者纯 prompt (节点 34)，
        # 可以用类似的方法：
        # if "34" in workflow and "inputs" in workflow["34"]:
        #     workflow["34"]["inputs"]["value"] = prompt
        
        client_id = str(uuid.uuid4())

        return {
            "prompt": workflow,
            "client_id": client_id
        }

    def is_async_task(self) -> bool:
        return True

    def parse_submit_response(self, response_data: dict) -> Optional[str]:
        """
        解析 ComfyUI 返回的 prompt_id
        """
        return response_data.get("prompt_id")

    def get_polling_config(self) -> dict:
        return {
            "max_timeout": 600,   
            "interval": 2,        
            "status_url_pattern": "{base}/history/{task_id}"
        }

    def parse_status_response(self, response_data: dict) -> dict:
        """
        解析 ComfyUI /history 接口返回的结果
        """
        if not response_data:
            return {
                "status": "RUNNING",
                "progress": 50,
                "result_url": None,
                "fail_reason": None
            }
            
        prompt_id = list(response_data.keys())[0] if response_data else None
        if not prompt_id:
            return {
                "status": "RUNNING",
                "progress": 50,
                "result_url": None,
                "fail_reason": None
            }

        task_info = response_data.get(prompt_id, {})
        outputs = task_info.get("outputs", {})
        
        if not outputs:
            return {
                "status": "RUNNING",
                "progress": 50,
                "result_url": None,
                "fail_reason": None
            }
        
        # 此处我们无法仅仅遍历查找 images 数组了，因为生成的内容可能在节点 40 的某个地方，
        # 或者从执行记录中查找 40 节点的输出。
        
        # 由于用户说最终输出结果在节点 40，我们就专门定位 40 的结果：
        # PreviewAny 或 SaveImage 等节点的输出结构可能不一定在 ['images'] 数组。
        # 如果是 PreviewAny 生成网络 URL：
        # 如果是标准的 ComfyUI 生成了具体文件，它会在 'images' 数组中。
        image_filename = None
        result_url = None
        
        # 获取 node 38 或者 node 40 的输出
        node_38_output = outputs.get("38", {})
        node_40_output = outputs.get("40", {})
        
        # 因为 38 节点是 GoGen_Nano_Banana2_Edit，如果 response_format 是 url
        # 它通常会把生成的 URL 放在 text 数组或者直接通过某个输出抛出来。
        # 很多自定义节点会把字符串结果放在 "text" 数组，图片文件放在 "images" 数组
        if "text" in node_38_output and len(node_38_output["text"]) > 0:
            result_url = node_38_output["text"][0]
        elif "text" in node_40_output and len(node_40_output["text"]) > 0:
            result_url = node_40_output["text"][0]
        elif "images" in node_38_output and len(node_38_output["images"]) > 0:
            image_filename = node_38_output["images"][0].get("filename")
            if image_filename:
                # 使用传入的 api_base（由 worker 传递进来的 target_host 或者外部地址）
                # 这里为了适配各种情况先做兼容处理
                base_host = self.api_base.rstrip("/")
                if "|" in base_host:
                     base_host = base_host.split("|")[-1]
                result_url = f"{base_host}/view?filename={image_filename}"
        elif "images" in node_40_output and len(node_40_output["images"]) > 0:
            image_filename = node_40_output["images"][0].get("filename")
            if image_filename:
                base_host = self.api_base.rstrip("/")
                if "|" in base_host:
                     base_host = base_host.split("|")[-1]
                result_url = f"{base_host}/view?filename={image_filename}"
        else:
            # fallback 保障兜底，找整个 outputs 中任意的图片或者文本链接
            for node_id, output_data in outputs.items():
                if "text" in output_data and len(output_data["text"]) > 0:
                    cand = str(output_data["text"][0])
                    if cand.startswith("http"):
                        result_url = cand
                        break
                elif "images" in output_data and len(output_data["images"]) > 0:
                    image_filename = output_data["images"][0].get("filename")
                    break
                    
            if not result_url and image_filename:
                 base_host = self.api_base.rstrip("/")
                 if "|" in base_host:
                     base_host = base_host.split("|")[-1]
                 result_url = f"{base_host}/view?filename={image_filename}"
                
        if result_url:
            return {
                "status": "SUCCESS",
                "progress": 100,
                "result_url": result_url,
                "fail_reason": None
            }
            
        return {
            "status": "FAILED",
            "progress": 0,
            "result_url": None,
            "fail_reason": "No image generated"
        }
