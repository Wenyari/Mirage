"""
异步任务包初始化
"""
from app.tasks.sora_job import process_sora_task

__all__ = [
    'process_sora_task',
]
