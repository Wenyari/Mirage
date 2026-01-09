"""
用户管理服务
提供管理员对用户的各种管理操作
"""
from datetime import datetime
from sqlalchemy import or_, and_
from app.extensions import db
from app.models import User, Transaction


def get_user_list(page=1, limit=10, email=None, status=None, level=None):
    """
    获取用户列表（带分页和筛选）

    Args:
        page: 页码，从1开始
        limit: 每页数量
        email: 搜索关键词（邮箱，模糊匹配）
        status: 状态筛选 (1=正常, 0=封禁, None=全部)
        level: 等级筛选 (1-5, None=全部)

    Returns:
        dict: {
            'items': [用户列表],
            'total': 总记录数,
            'page': 当前页,
            'limit': 每页数量
        }
    """
    # 构建查询条件
    query = User.query

    # 关键词搜索（邮箱）
    if email:
        query = query.filter(User.email.like(f'%{email}%'))

    # 状态筛选
    if status is not None:
        query = query.filter(User.status == status)

    # 等级筛选
    if level is not None:
        query = query.filter(User.level == level)

    # 按创建时间倒序排列
    query = query.order_by(User.created_at.desc())

    # 分页查询
    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    return {
        'items': [user.to_dict() for user in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'limit': limit
    }


def update_user_profile(user_id, level=None, status=None, admin_id=None):
    """
    修改用户资料（等级和状态）

    Args:
        user_id: 用户ID
        level: 新等级 (1-5, None=不修改)
        status: 新状态 (1=正常, 0=封禁, None=不修改)
        admin_id: 执行操作的管理员ID

    Returns:
        dict: 操作结果

    Raises:
        ValueError: 用户不存在、等级无效或尝试修改管理员
    """
    user = User.query.get(user_id)

    if not user:
        raise ValueError("User not found")

    # 不允许修改管理员账号
    if user.role == 'admin':
        raise ValueError("Cannot modify admin user")

    changes = []

    # 修改等级
    if level is not None:
        if level not in [1, 2, 3, 4, 5]:
            raise ValueError("Invalid level. Must be between 1 and 5")
        old_level = user.level
        user.level = level
        changes.append(f"level: T{old_level} -> T{level}")

    # 修改状态
    if status is not None:
        if status not in [0, 1]:
            raise ValueError("Invalid status. Must be 0 (banned) or 1 (active)")
        old_status = user.status
        user.status = status
        status_names = {0: 'banned', 1: 'active'}
        changes.append(f"status: {status_names[old_status]} -> {status_names[status]}")

    if not changes:
        raise ValueError("No changes specified")

    db.session.commit()

    return {
        'user_id': user_id,
        'changes': changes,
        'message': f'User {user.email} profile updated: {", ".join(changes)}'
    }


def ban_user(user_id, admin_id):
    """
    封禁用户（旧版接口，建议使用update_user_profile）

    Args:
        user_id: 被封禁的用户ID
        admin_id: 执行操作的管理员ID

    Returns:
        dict: 操作结果

    Raises:
        ValueError: 用户不存在或已经封禁
    """
    user = User.query.get(user_id)

    if not user:
        raise ValueError("User not found")

    if user.role == 'admin':
        raise ValueError("Cannot ban admin user")

    if user.status == 0:
        raise ValueError("User is already banned")

    # 更新用户状态
    user.status = 0
    db.session.commit()

    return {
        'user_id': user_id,
        'status': 'banned',
        'message': f'User {user.email} has been banned'
    }


def unban_user(user_id, admin_id):
    """
    解封用户

    Args:
        user_id: 被解封的用户ID
        admin_id: 执行操作的管理员ID

    Returns:
        dict: 操作结果

    Raises:
        ValueError: 用户不存在或未被封禁
    """
    user = User.query.get(user_id)

    if not user:
        raise ValueError("User not found")

    if user.status == 1:
        raise ValueError("User is not banned")

    # 更新用户状态
    user.status = 1
    db.session.commit()

    return {
        'user_id': user_id,
        'status': 'active',
        'message': f'User {user.email} has been unbanned'
    }


def update_user_level(user_id, new_level, admin_id):
    """
    修改用户等级

    Args:
        user_id: 用户ID
        new_level: 新等级 (1-5)
        admin_id: 执行操作的管理员ID

    Returns:
        dict: 操作结果

    Raises:
        ValueError: 用户不存在或等级无效
    """
    if new_level not in [1, 2, 3, 4, 5]:
        raise ValueError("Invalid level. Must be between 1 and 5")

    user = User.query.get(user_id)

    if not user:
        raise ValueError("User not found")

    old_level = user.level

    # 更新用户等级
    user.level = new_level
    db.session.commit()

    return {
        'user_id': user_id,
        'old_level': old_level,
        'new_level': new_level,
        'message': f'User {user.email} level updated from T{old_level} to T{new_level}'
    }


def adjust_user_balance(user_id, amount, remark, admin_id, balance_type='recharge'):
    """
    调整用户余额（管理员手动调整）

    Args:
        user_id: 用户ID
        amount: 调整金额（正数=增加，负数=扣除）
        remark: 调整原因备注
        admin_id: 执行操作的管理员ID
        balance_type: 调整类型 ('recharge' 或 'activity')，默认为充值积分

    Returns:
        dict: 操作结果

    Raises:
        ValueError: 用户不存在或余额不足
    """
    from decimal import Decimal

    user = User.query.get(user_id)

    if not user:
        raise ValueError("User not found")

    # 根据类型选择余额字段
    if balance_type == 'activity':
        old_balance = float(user.activity_balance)
        new_balance_decimal = user.activity_balance + Decimal(str(amount))

        # 检查余额不能为负数
        if new_balance_decimal < 0:
            raise ValueError(f"Insufficient activity balance. Current: {old_balance}, Adjustment: {amount}")

        user.activity_balance = new_balance_decimal
        new_balance = float(new_balance_decimal)
    else:  # recharge
        old_balance = float(user.recharge_balance)
        new_balance_decimal = user.recharge_balance + Decimal(str(amount))

        # 检查余额不能为负数
        if new_balance_decimal < 0:
            raise ValueError(f"Insufficient recharge balance. Current: {old_balance}, Adjustment: {amount}")

        user.recharge_balance = new_balance_decimal
        new_balance = float(new_balance_decimal)

    # 记录交易流水
    transaction = Transaction(
        user_id=user_id,
        type='system',
        balance_type=balance_type,
        amount=Decimal(str(amount)),
        balance_snapshot=new_balance_decimal,
        related_id=f'admin_{admin_id}',
        remark=remark or 'Admin adjustment'
    )

    db.session.add(transaction)
    db.session.commit()

    return {
        'user_id': user_id,
        'balance_type': balance_type,
        'old_balance': old_balance,
        'new_balance': new_balance,
        'adjustment': amount,
        'transaction_id': transaction.id,
        'message': f'User {user.email} {balance_type} balance adjusted: {old_balance} -> {new_balance}'
    }


def get_user_detail(user_id):
    """
    获取用户详细信息（包括最近交易和任务记录）

    Args:
        user_id: 用户ID

    Returns:
        dict: {
            'user': 用户基本信息,
            'recent_transactions': 最近交易记录（前10条）,
            'recent_tasks': 最近任务记录（前10条）
        }

    Raises:
        ValueError: 用户不存在
    """
    user = User.query.get(user_id)

    if not user:
        raise ValueError("User not found")

    # 获取最近10条交易记录
    from app.models import Task
    recent_transactions = Transaction.query.filter_by(
        user_id=user_id
    ).order_by(
        Transaction.created_at.desc()
    ).limit(10).all()

    # 获取最近10条任务记录
    recent_tasks = Task.query.filter_by(
        user_id=user_id
    ).order_by(
        Task.created_at.desc()
    ).limit(10).all()

    # 转换交易记录
    transactions_list = []
    for tx in recent_transactions:
        transactions_list.append({
            'id': tx.id,
            'type': tx.type,
            'amount': float(tx.amount),
            'reason': tx.remark or '',
            'created_at': tx.created_at.isoformat() if tx.created_at else None
        })

    # 转换任务记录
    tasks_list = []
    for task in recent_tasks:
        # 从params中提取model信息（如果有）
        model_name = 'unknown'
        if task.params and isinstance(task.params, dict):
            model_name = task.params.get('model', task.model)

        # 计算token使用量
        token_used = 0
        if task.token_usage and isinstance(task.token_usage, dict):
            token_used = task.token_usage.get('input', 0) + task.token_usage.get('output', 0)

        tasks_list.append({
            'id': task.id,
            'model': model_name,
            'prompt': task.prompt[:50] + '...' if task.prompt and len(task.prompt) > 50 else task.prompt,
            'status': task.status,
            'token_used': token_used,
            'created_at': task.created_at.isoformat() if task.created_at else None
        })

    return {
        'user': user.to_dict(),
        'recent_transactions': transactions_list,
        'recent_tasks': tasks_list
    }
