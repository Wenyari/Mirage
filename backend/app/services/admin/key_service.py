"""
密钥管理服务
提供密钥池的管理、状态监控和统计功能
"""
from datetime import datetime, timedelta
from app.extensions import db, redis_client
from app.models import ApiKey, Model


def get_key_list(model_filter=None):
    """
    获取密钥列表（带实时状态）

    Args:
        model_filter: 模型筛选

    Returns:
        list: 密钥列表（含实时状态）
    """
    query = ApiKey.query

    # 模型筛选
    if model_filter:
        query = query.filter(ApiKey.model == model_filter)

    keys = query.all()

    # 为每个密钥添加实时状态
    result = []
    for key in keys:
        key_dict = key.to_dict(include_secret=True)

        # 从 Redis 读取实时状态
        try:
            # 当前并发数
            current_usage = redis_client.get(f"pool:usage:{key.id}")
            key_dict['current_usage'] = int(current_usage) if current_usage else 0

            # 冷却状态
            cooling_until = redis_client.get(f"pool:cooldown:{key.id}")
            if cooling_until:
                key_dict['is_cooling'] = True
                key_dict['cooling_until'] = cooling_until.decode('utf-8') if isinstance(cooling_until, bytes) else cooling_until
            else:
                key_dict['is_cooling'] = False
                key_dict['cooling_until'] = None

        except Exception:
            # Redis 不可用时使用默认值
            key_dict['current_usage'] = 0
            key_dict['is_cooling'] = False
            key_dict['cooling_until'] = None

        result.append(key_dict)

    return result


def create_key(model, api_base, key_secret, max_concurrency=3, weight=10):
    """
    添加新密钥

    Args:
        model: 模型标识
        api_base: API基础地址
        key_secret: API密钥
        max_concurrency: 最大并发数
        weight: 权重

    Returns:
        dict: 创建的密钥数据

    Raises:
        ValueError: 参数无效或模型不存在
    """
    # 验证模型是否存在
    model_obj = Model.query.filter_by(key=model).first()
    if not model_obj:
        raise ValueError(f"Model '{model}' not found")

    # 验证参数
    if max_concurrency < 1 or max_concurrency > 100:
        raise ValueError("max_concurrency must be between 1 and 100")

    if weight < 1 or weight > 100:
        raise ValueError("weight must be between 1 and 100")

    # 创建密钥
    api_key = ApiKey(
        model=model,
        api_base=api_base,
        key_secret=key_secret,
        max_concurrency=max_concurrency,
        weight=weight,
        status=1  # 默认启用
    )

    db.session.add(api_key)
    db.session.commit()

    # 初始化 Redis 状态
    try:
        redis_client.set(f"pool:usage:{api_key.id}", 0)
    except Exception:
        pass

    return api_key.to_dict(include_secret=False)


def batch_create_keys(model, api_base, keys, max_concurrency=3, weight=10):
    """
    批量添加密钥

    Args:
        model: 模型标识
        api_base: API基础地址（可选）
        keys: 密钥数组
        max_concurrency: 统一的最大并发数
        weight: 统一的权重

    Returns:
        dict: {
            'success_count': 成功数量,
            'failed_count': 失败数量,
            'failed_keys': 失败的密钥列表（脱敏）
        }

    Raises:
        ValueError: 参数无效
    """
    # 验证模型是否存在
    model_obj = Model.query.filter_by(key=model).first()
    if not model_obj:
        raise ValueError(f"Model '{model}' not found")

    # 验证数量限制
    if len(keys) > 100:
        raise ValueError("Cannot add more than 100 keys at once")

    success_count = 0
    failed_count = 0
    failed_keys = []

    for key_secret in keys:
        try:
            # 创建密钥
            api_key = ApiKey(
                model=model,
                api_base=api_base or '',
                key_secret=key_secret,
                max_concurrency=max_concurrency,
                weight=weight,
                status=1
            )
            db.session.add(api_key)
            db.session.flush()

            # 初始化 Redis 状态
            try:
                redis_client.set(f"pool:usage:{api_key.id}", 0)
            except Exception:
                pass

            success_count += 1

        except Exception as e:
            failed_count += 1
            # 脱敏密钥
            masked_key = f"{key_secret[:8]}****{key_secret[-4:]}" if len(key_secret) > 12 else "****"
            failed_keys.append({
                'key': masked_key,
                'error': str(e)
            })

    db.session.commit()

    return {
        'success_count': success_count,
        'failed_count': failed_count,
        'failed_keys': failed_keys
    }


def update_key(key_id, max_concurrency=None, weight=None, status=None):
    """
    更新密钥配置

    Args:
        key_id: 密钥ID
        max_concurrency: 最大并发数
        weight: 权重
        status: 状态

    Returns:
        dict: 操作结果

    Raises:
        ValueError: 密钥不存在或参数无效
    """
    api_key = ApiKey.query.get(key_id)
    if not api_key:
        raise ValueError(f"Key {key_id} not found")

    # 更新字段
    if max_concurrency is not None:
        if max_concurrency < 1 or max_concurrency > 100:
            raise ValueError("max_concurrency must be between 1 and 100")
        api_key.max_concurrency = max_concurrency

    if weight is not None:
        if weight < 1 or weight > 100:
            raise ValueError("weight must be between 1 and 100")
        api_key.weight = weight

    if status is not None:
        if status not in [0, 1]:
            raise ValueError("status must be 0 or 1")
        api_key.status = status

    api_key.updated_at = datetime.utcnow()
    db.session.commit()

    return {'message': 'Key updated successfully'}


def delete_key(key_id):
    """
    删除密钥

    Args:
        key_id: 密钥ID

    Returns:
        dict: 操作结果

    Raises:
        ValueError: 密钥不存在或正在使用中
    """
    api_key = ApiKey.query.get(key_id)
    if not api_key:
        raise ValueError(f"Key {key_id} not found")

    # 检查是否正在使用
    try:
        current_usage = redis_client.get(f"pool:usage:{key_id}")
        if current_usage and int(current_usage) > 0:
            raise ValueError("Cannot delete key that is currently in use. Please wait for tasks to complete.")
    except Exception:
        pass

    # 清理 Redis 数据
    try:
        redis_client.delete(f"pool:usage:{key_id}")
        redis_client.delete(f"pool:cooldown:{key_id}")
    except Exception:
        pass

    # 删除密钥
    db.session.delete(api_key)
    db.session.commit()

    return {'message': 'Key deleted successfully'}


def trigger_cooldown(key_id, action, duration=300):
    """
    手动触发熔断或解除熔断

    Args:
        key_id: 密钥ID
        action: 操作类型 (trigger/release)
        duration: 冷却时长（秒）

    Returns:
        dict: 操作结果

    Raises:
        ValueError: 密钥不存在或参数无效
    """
    api_key = ApiKey.query.get(key_id)
    if not api_key:
        raise ValueError(f"Key {key_id} not found")

    if action not in ['trigger', 'release']:
        raise ValueError("action must be 'trigger' or 'release'")

    # 检查Redis是否可用
    if not redis_client:
        raise ValueError("Redis is not available. Cooldown feature requires Redis.")

    try:
        if action == 'trigger':
            # 触发熔断
            cooling_until = datetime.utcnow() + timedelta(seconds=duration)
            cooling_until_str = cooling_until.isoformat() + 'Z'

            redis_client.setex(
                f"pool:cooldown:{key_id}",
                duration,
                cooling_until_str
            )

            return {
                'message': 'Cooldown triggered successfully',
                'cooling_until': cooling_until_str
            }

        else:  # release
            # 解除熔断
            redis_client.delete(f"pool:cooldown:{key_id}")

            return {
                'message': 'Cooldown released successfully',
                'cooling_until': None
            }

    except Exception as e:
        raise ValueError(f"Failed to {action} cooldown: {str(e)}")


def get_key_stats():
    """
    获取密钥统计信息

    Returns:
        dict: 统计数据
    """
    # 按模型统计
    models = Model.query.all()
    by_model = []

    for model in models:
        keys = ApiKey.query.filter_by(model=model.key).all()

        if not keys:
            continue

        total_keys = len(keys)
        active_keys = sum(1 for k in keys if k.status == 1)
        total_concurrency = sum(k.max_concurrency for k in keys)

        # 统计冷却中的密钥和当前使用情况
        cooling_keys = 0
        current_usage = 0

        try:
            for key in keys:
                # 检查冷却状态
                if redis_client.exists(f"pool:cooldown:{key.id}"):
                    cooling_keys += 1

                # 累计当前使用量
                usage = redis_client.get(f"pool:usage:{key.id}")
                if usage:
                    current_usage += int(usage)
        except Exception:
            pass

        by_model.append({
            'model': model.key,
            'total_keys': total_keys,
            'active_keys': active_keys,
            'cooling_keys': cooling_keys,
            'total_concurrency': total_concurrency,
            'current_usage': current_usage
        })

    # 今日统计（简化版，可以后续从数据库聚合）
    total_calls_today = 0
    total_errors_today = 0

    # 计算错误率
    error_rate = (total_errors_today / total_calls_today * 100) if total_calls_today > 0 else 0

    return {
        'by_model': by_model,
        'total_calls_today': total_calls_today,
        'total_errors_today': total_errors_today,
        'error_rate': round(error_rate, 2)
    }
