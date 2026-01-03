"""
用户管理服务
提供管理员对用户的各种管理操作
"""
from datetime import datetime
from sqlalchemy import or_, and_
from app.extensions import db
from app.models import User, Transaction


def get_user_list(page=1, per_page=20, keyword=None, status=None, level=None):
    """
    获取用户列表（带分页和筛选）

    Args:
        page: 页码，从1开始
        per_page: 每页数量
        keyword: 搜索关键词（邮箱）
        status: 状态筛选 (0=封禁, 1=正常, None=全部)
        level: 等级筛选 (1-5, None=全部)

    Returns:
        dict: {
            'total': 总记录数,
            'pages': 总页数,
            'current_page': 当前页,
            'per_page': 每页数量,
            'users': [用户列表]
        }
    """
    # 构建查询条件
    query = User.query

    # 关键词搜索（邮箱）
    if keyword:
        query = query.filter(User.email.like(f'%{keyword}%'))

    # 状态筛选
    if status is not None:
        query = query.filter(User.status == status)

    # 等级筛选
    if level is not None:
        query = query.filter(User.level == level)

    # 按创建时间倒序排列
    query = query.order_by(User.created_at.desc())

    # 分页查询
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page,
        'per_page': pagination.per_page,
        'users': [user.to_dict() for user in pagination.items]
    }


def ban_user(user_id, admin_id):
    """
    封禁用户

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


def adjust_user_balance(user_id, amount, remark, admin_id):
    """
    调整用户余额（管理员手动调整）

    Args:
        user_id: 用户ID
        amount: 调整金额（正数=增加，负数=扣除）
        remark: 调整原因备注
        admin_id: 执行操作的管理员ID

    Returns:
        dict: 操作结果

    Raises:
        ValueError: 用户不存在或余额不足
    """
    user = User.query.get(user_id)

    if not user:
        raise ValueError("User not found")

    old_balance = float(user.balance)
    new_balance = old_balance + amount

    # 检查余额不能为负数
    if new_balance < 0:
        raise ValueError(f"Insufficient balance. Current: {old_balance}, Adjustment: {amount}")

    # 更新用户余额
    user.balance = new_balance

    # 记录交易流水
    transaction = Transaction(
        user_id=user_id,
        type='system',
        amount=amount,
        balance_snapshot=new_balance,
        related_id=f'admin_{admin_id}',
        remark=remark or 'Admin adjustment'
    )

    db.session.add(transaction)
    db.session.commit()

    return {
        'user_id': user_id,
        'old_balance': old_balance,
        'new_balance': new_balance,
        'adjustment': amount,
        'transaction_id': transaction.id,
        'message': f'User {user.email} balance adjusted: {old_balance} -> {new_balance}'
    }


def get_user_detail(user_id):
    """
    获取用户详细信息（包括统计数据）

    Args:
        user_id: 用户ID

    Returns:
        dict: 用户详细信息

    Raises:
        ValueError: 用户不存在
    """
    user = User.query.get(user_id)

    if not user:
        raise ValueError("User not found")

    # 获取任务统计
    from app.models import Task
    total_tasks = Task.query.filter_by(user_id=user_id).count()
    completed_tasks = Task.query.filter_by(user_id=user_id, status='completed').count()
    processing_tasks = Task.query.filter_by(user_id=user_id, status='processing').count()

    # 获取交易统计
    total_recharge = db.session.query(
        db.func.coalesce(db.func.sum(Transaction.amount), 0)
    ).filter(
        and_(
            Transaction.user_id == user_id,
            Transaction.type == 'recharge'
        )
    ).scalar()

    total_consumed = db.session.query(
        db.func.coalesce(db.func.sum(Transaction.amount), 0)
    ).filter(
        and_(
            Transaction.user_id == user_id,
            Transaction.type == 'task_cost'
        )
    ).scalar()

    # 组合返回数据
    user_data = user.to_dict()
    user_data.update({
        'statistics': {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'processing_tasks': processing_tasks,
            'total_recharge': float(total_recharge or 0),
            'total_consumed': abs(float(total_consumed or 0)),
        },
        'register_ip': user.register_ip,
        'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None,
    })

    return user_data
