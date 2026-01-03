"""
管理员仪表盘服务
提供仪表盘数据查询功能
"""
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from app.extensions import db
from app.models import User, Task, Transaction, CDK


def get_dashboard_overview():
    """
    获取管理员仪表盘核心指标

    Returns:
        dict: 包含今日新增用户、积分消耗、CDK充值和活跃任务数
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. 今日新增用户数
    today_new_users = User.query.filter(User.created_at >= today_start).count()

    # 2. 今日积分消耗量（所有任务的 cost_points 总和）
    today_points_consumed = db.session.query(
        func.coalesce(func.sum(Task.cost_points), 0)
    ).filter(
        Task.created_at >= today_start
    ).scalar()

    # 3. 今日通过CDK兑换充值的积分（transactions 表中 type='recharge' 的记录）
    today_cdk_recharge = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        and_(
            Transaction.created_at >= today_start,
            Transaction.type == 'recharge'
        )
    ).scalar()

    # 4. 当前活跃任务数（status='processing' 的任务）
    active_tasks = Task.query.filter(Task.status == 'processing').count()

    return {
        'today_new_users': today_new_users,
        'today_points_consumed': float(today_points_consumed or 0),
        'today_cdk_recharge': float(today_cdk_recharge or 0),
        'active_tasks': active_tasks
    }


def get_trend_chart_data(days=7):
    """
    获取趋势图数据（最近 N 天）

    Args:
        days: 查询天数，7 或 30

    Returns:
        list: 每日统计数据列表
    """
    if days not in [7, 30]:
        days = 7

    # 计算起始日期（UTC时间，从今天开始往前推N天）
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today - timedelta(days=days - 1)

    # 查询用户注册数据（按日期分组）
    user_stats = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('new_users')
    ).filter(
        User.created_at >= start_date
    ).group_by(
        func.date(User.created_at)
    ).all()

    # 查询积分消耗数据（按日期分组）
    task_stats = db.session.query(
        func.date(Task.created_at).label('date'),
        func.coalesce(func.sum(Task.cost_points), 0).label('points_consumed')
    ).filter(
        Task.created_at >= start_date
    ).group_by(
        func.date(Task.created_at)
    ).all()

    # 查询CDK充值数据（按日期分组）
    recharge_stats = db.session.query(
        func.date(Transaction.created_at).label('date'),
        func.coalesce(func.sum(Transaction.amount), 0).label('cdk_recharge')
    ).filter(
        and_(
            Transaction.created_at >= start_date,
            Transaction.type == 'recharge'
        )
    ).group_by(
        func.date(Transaction.created_at)
    ).all()

    # 转换为字典以便快速查找
    user_dict = {str(row.date): row.new_users for row in user_stats}
    task_dict = {str(row.date): float(row.points_consumed) for row in task_stats}
    recharge_dict = {str(row.date): float(row.cdk_recharge) for row in recharge_stats}

    # 生成完整的日期序列（确保每一天都有数据，即使为0）
    result = []
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')

        result.append({
            'date': date_str,
            'new_users': user_dict.get(date_str, 0),
            'points_consumed': task_dict.get(date_str, 0.0),
            'cdk_recharge': recharge_dict.get(date_str, 0.0)
        })

    return result
