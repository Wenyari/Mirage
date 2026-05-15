"""
适配器工厂
根据 API Base URL 返回对应的适配器实例
"""
import logging
from .base_adapter import ApiAdapter
from .t8star_video_adapter import T8StarVideoGenerationAdapter
from .t8star_image_adapter import T8StarImageGenerationAdapter
from .t8star_image_edit_adapter import T8StarImageEditAdapter
from .lconai_image_adapter import LconaiImageGenerationAdapter
from .default_adapter import DefaultAdapter

logger = logging.getLogger(__name__)


def get_adapter(api_base: str, model: str = None) -> ApiAdapter:
    """
    根据 API Base URL 和模型名称返回对应的适配器

    Args:
        api_base: API 基础 URL (如 "https://ai.t8star.cn/v2/videos/generations")
        model: 模型名称 (如 "workflow-earing-ad")

    Returns:
        ApiAdapter: 对应的适配器实例
    """
    
    # 检查是否为特定的工作流模型
    if model == 'workflow-earing-ad':
        from .workflow_earing_ad_adapter import WorkflowEaringAdAdapter
        logger.info(f"Using WorkflowEaringAdAdapter for model: {model}, API base: {api_base}")
        return WorkflowEaringAdAdapter(api_base)

    # 规范化 URL
    api_base_lower = api_base.lower()

    # LnAPI 适配器
    if 'lnapi.com' in api_base_lower:
        # 检查是否为 LnAPI 的视频生成模型 (通过模型前缀区分)
        if model and (model.startswith('veo') or model.startswith('grok') or model.startswith('sora')):
            from .lnapi_video_adapter import LnapiVideoGenerationAdapter
            logger.info(f"Using LnapiVideoGenerationAdapter for model: {model}, API base: {api_base}")
            return LnapiVideoGenerationAdapter(api_base)

    # LconAI 适配器
    if 'n.lconai.com' in api_base_lower or 'lconai.com' in api_base_lower:
        if '/v1/images/generations' in api_base_lower:
            logger.info(f"Using LconaiImageGenerationAdapter for API base: {api_base}")
            return LconaiImageGenerationAdapter(api_base)

    # T8Star 适配器 - 使用精确路径匹配
    if 'ai.t8star.cn' in api_base_lower or 't8star.cn' in api_base_lower or 'api.bltcy.ai' in api_base_lower or 'bltcy.ai' in api_base_lower:
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
            logger.info(f"Using T8StarVideoGenerationAdapter for API base: {api_base}")
            return T8StarVideoGenerationAdapter(api_base)

        # 如果路径不匹配，默认使用视频适配器
        else:
            logger.warning(f"Unknown T8Star API path: {api_base}, using T8StarVideoGenerationAdapter")
            return T8StarVideoGenerationAdapter(api_base)

    # 未来可以在这里添加更多适配器
    # elif 'api.openai.com' in api_base_lower:
    #     return OpenAIAdapter(api_base)
    # elif 'another-provider.com' in api_base_lower:
    #     return AnotherAdapter(api_base)

    # 默认适配器
    logger.info(f"Using DefaultAdapter for API base: {api_base}")
    return DefaultAdapter(api_base)
