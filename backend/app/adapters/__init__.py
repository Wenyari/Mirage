"""API 适配器模块"""
from .base_adapter import ApiAdapter
from .t8star_video_adapter import T8StarVideoGenerationAdapter
from .t8star_image_adapter import T8StarImageGenerationAdapter
from .t8star_image_edit_adapter import T8StarImageEditAdapter
from .default_adapter import DefaultAdapter
from .adapter_factory import get_adapter

# 向后兼容：T8StarAdapter 作为 T8StarVideoGenerationAdapter 的别名
T8StarAdapter = T8StarVideoGenerationAdapter

__all__ = [
    'ApiAdapter',
    'T8StarVideoGenerationAdapter',
    'T8StarImageGenerationAdapter',
    'T8StarImageEditAdapter',
    'DefaultAdapter',
    'get_adapter',
    # 向后兼容
    'T8StarAdapter',
]
