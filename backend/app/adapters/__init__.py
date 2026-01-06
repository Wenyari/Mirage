"""API 适配器模块"""
from .api_adapter import (
    ApiAdapter,
    T8StarAdapter,
    T8StarImageGenerationAdapter,
    T8StarImageEditAdapter,
    DefaultAdapter,
    get_adapter
)

__all__ = [
    'ApiAdapter',
    'T8StarAdapter',
    'T8StarImageGenerationAdapter',
    'T8StarImageEditAdapter',
    'DefaultAdapter',
    'get_adapter',
]
