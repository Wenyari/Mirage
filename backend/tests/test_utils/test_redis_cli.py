"""
Redis 工具测试
"""
import pytest
from app.utils.redis_cli import (
    set_cache,
    get_cache,
    delete_cache,
    incr_counter,
    acquire_lock,
    release_lock,
    push_to_queue,
    pop_from_queue,
    get_queue_length
)


@pytest.mark.unit
class TestRedisUtils:
    """Redis 工具测试类"""

    def test_set_and_get_cache(self, app, redis_db):
        """测试缓存设置和获取"""
        with app.app_context():
            key = 'test_key'
            value = 'test_value'

            set_cache(key, value, expire=60)
            result = get_cache(key)

            assert result == value

    def test_delete_cache(self, app, redis_db):
        """测试删除缓存"""
        with app.app_context():
            key = 'test_key_delete'
            value = 'test_value'

            set_cache(key, value)
            assert get_cache(key) == value

            delete_cache(key)
            assert get_cache(key) is None

    def test_incr_counter(self, app, redis_db):
        """测试计数器自增"""
        with app.app_context():
            key = 'test_counter'

            # 第一次调用，返回 1
            result = incr_counter(key, expire=60)
            assert result == 1

            # 第二次调用，返回 2
            result = incr_counter(key, expire=60)
            assert result == 2

    def test_acquire_and_release_lock(self, app, redis_db):
        """测试获取和释放锁"""
        with app.app_context():
            lock_name = 'test_lock'

            # 第一次获取锁应该成功
            acquired = acquire_lock(lock_name, timeout=10)
            assert acquired is True

            # 第二次获取同一个锁应该失败
            acquired = acquire_lock(lock_name, timeout=10)
            assert acquired is False

            # 释放锁
            release_lock(lock_name)

            # 再次获取应该成功
            acquired = acquire_lock(lock_name, timeout=10)
            assert acquired is True

    def test_queue_operations(self, app, redis_db):
        """测试队列操作"""
        with app.app_context():
            queue_name = 'test_queue'

            # 推入数据
            push_to_queue(queue_name, 'data1')
            push_to_queue(queue_name, 'data2')
            push_to_queue(queue_name, 'data3')

            # 检查队列长度
            length = get_queue_length(queue_name)
            assert length == 3

            # 弹出数据（FIFO）
            data = pop_from_queue(queue_name, timeout=1)
            assert data == 'data1'

            data = pop_from_queue(queue_name, timeout=1)
            assert data == 'data2'

            # 队列长度应该减少
            length = get_queue_length(queue_name)
            assert length == 1

    def test_pop_from_empty_queue(self, app, redis_db):
        """测试从空队列弹出"""
        with app.app_context():
            queue_name = 'empty_queue'

            # 超时应该返回 None
            data = pop_from_queue(queue_name, timeout=1)
            assert data is None
