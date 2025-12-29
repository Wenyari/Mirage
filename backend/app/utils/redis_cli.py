"""
Redis 操作封装
提供常用的 Redis 操作函数
"""
from app.extensions import redis_client


def set_cache(key: str, value: str, expire: int = 3600):
    """
    设置缓存

    Args:
        key: 缓存键
        value: 缓存值
        expire: 过期时间 (秒)，默认 1 小时
    """
    redis_client.setex(key, expire, value)


def get_cache(key: str) -> str:
    """
    获取缓存

    Args:
        key: 缓存键

    Returns:
        str: 缓存值，不存在返回 None
    """
    return redis_client.get(key)


def delete_cache(key: str):
    """
    删除缓存

    Args:
        key: 缓存键
    """
    redis_client.delete(key)


def incr_counter(key: str, expire: int = None) -> int:
    """
    计数器自增

    Args:
        key: 计数器键
        expire: 过期时间 (秒)，None 表示不过期

    Returns:
        int: 自增后的值
    """
    value = redis_client.incr(key)

    if expire and value == 1:  # 第一次设置时添加过期时间
        redis_client.expire(key, expire)

    return value


def acquire_lock(lock_name: str, timeout: int = 10) -> bool:
    """
    获取分布式锁 (简单实现)

    Args:
        lock_name: 锁名称
        timeout: 锁超时时间 (秒)

    Returns:
        bool: 是否获取成功
    """
    lock_key = f"lock:{lock_name}"
    return redis_client.set(lock_key, "1", nx=True, ex=timeout)


def release_lock(lock_name: str):
    """
    释放分布式锁

    Args:
        lock_name: 锁名称
    """
    lock_key = f"lock:{lock_name}"
    redis_client.delete(lock_key)


def push_to_queue(queue_name: str, data: str):
    """
    推送数据到队列 (List)

    Args:
        queue_name: 队列名称
        data: 数据 (JSON 字符串)
    """
    redis_client.rpush(queue_name, data)


def pop_from_queue(queue_name: str, timeout: int = 0) -> str:
    """
    从队列中弹出数据 (阻塞)

    Args:
        queue_name: 队列名称
        timeout: 阻塞超时时间 (秒)，0 表示无限等待

    Returns:
        str: 队列数据，超时返回 None
    """
    result = redis_client.blpop(queue_name, timeout=timeout)
    if result:
        return result[1]  # (queue_name, value)
    return None


def get_queue_length(queue_name: str) -> int:
    """
    获取队列长度

    Args:
        queue_name: 队列名称

    Returns:
        int: 队列长度
    """
    return redis_client.llen(queue_name)
