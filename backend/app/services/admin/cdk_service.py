"""
CDK管理服务
提供CDK的生成、查询、作废等功能
"""
import secrets
import string
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import or_
from app.extensions import db
from app.models import CDK, User


def generate_cdk_code():
    """
    生成唯一的CDK码
    格式：CDK-XXXXXXXXXXXXXXXXXXXX (24位字符)

    Returns:
        str: CDK码
    """
    # 使用大写字母和数字，排除易混淆字符（0, O, I, 1）
    chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')
    code_part = ''.join(secrets.choice(chars) for _ in range(20))
    return f'CDK-{code_part}'


def generate_batch_no():
    """
    生成批次号
    格式：BATCH + 年月日 + 3位序号

    Returns:
        str: 批次号
    """
    date_part = datetime.now(ZoneInfo("Asia/Shanghai")).strftime('%Y%m%d')

    # 查询今天已有的批次数量（需要处理表不存在的情况）
    try:
        today_start = datetime.now(ZoneInfo("Asia/Shanghai")).replace(hour=0, minute=0, second=0, microsecond=0)
        today_batches = db.session.query(CDK.batch_no).filter(
            CDK.created_at >= today_start,
            CDK.batch_no.like(f'BATCH{date_part}%')
        ).distinct().count()
    except Exception:
        # 如果表不存在或查询失败，从001开始
        today_batches = 0

    seq = str(today_batches + 1).zfill(3)
    return f'BATCH{date_part}{seq}'


def generate_cdk_batch(amount, count, type='once', batch_name=None, grant_level=None, expire_at=None):
    """
    批量生成CDK

    Args:
        amount: 单个CDK面额（积分）
        count: 生成数量
        type: 类型 (once/multi)，接口使用multi，数据库存储为universal
        batch_name: 批次名称
        grant_level: 授予等级
        expire_at: 过期时间 (str, ISO format)

    Returns:
        dict: {
            'batch_no': 批次号,
            'batch_name': 批次名称,
            'cdks': [CDK列表]
        }

    Raises:
        ValueError: 参数无效
    """
    # 参数验证
    if amount <= 0:
        raise ValueError("Amount must be positive")

    if count <= 0 or count > 1000:
        raise ValueError("Count must be between 1 and 1000")

    # 先验证类型
    if type not in ['once', 'multi']:
        raise ValueError("Type must be 'once' or 'multi'")

    # 类型转换：接口的multi对应数据库的universal
    db_type = 'universal' if type == 'multi' else 'once'

    # 生成批次号（如果提供了batch_name，可以拼接到batch_no中）
    batch_no = generate_batch_no()
    if batch_name:
        # 将batch_name存储在batch_no中，格式：BATCH20240320001|春节活动
        batch_no = f"{batch_no}|{batch_name}"

    # 处理过期时间
    expire_dt = None
    if expire_at:
        try:
            # 尝试解析 ISO 格式 (YYYY-MM-DDTHH:mm)
            expire_dt = datetime.fromisoformat(expire_at)
        except ValueError:
            # 如果解析失败，尝试加上秒 (YYYY-MM-DDTHH:mm:ss)
            try:
                expire_dt = datetime.strptime(expire_at, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                 pass # 如果还是失败，保持None或者抛出异常？这里暂时忽略错误格式
    
    # 批量生成CDK
    cdks = []
    for _ in range(count):
        # 生成唯一的CDK码
        max_attempts = 10
        for attempt in range(max_attempts):
            code = generate_cdk_code()
            # 检查是否已存在
            exists = CDK.query.filter_by(code=code).first()
            if not exists:
                break
            if attempt == max_attempts - 1:
                raise ValueError("Failed to generate unique CDK code")

        cdk = CDK(
            code=code,
            points=amount,
            type=db_type,
            batch_no=batch_no,
            status=0,  # 未使用
            grant_level=grant_level,
            expire_at=expire_dt
        )
        db.session.add(cdk)
        cdks.append(cdk)

    db.session.commit()

    # 转换为接口格式
    return {
        'batch_no': batch_no.split('|')[0] if '|' in batch_no else batch_no,
        'batch_name': batch_name,
        'cdks': [_cdk_to_api_dict(cdk) for cdk in cdks]
    }


def get_cdk_list(page=1, limit=10, batch_no=None, status=None, search=None):
    """
    获取CDK列表（带分页和筛选）

    Args:
        page: 页码，从1开始
        limit: 每页数量
        batch_no: 批次号筛选
        status: 状态筛选 (unused/used/void)
        search: 模糊搜索（批次号或CDK码）

    Returns:
        dict: {
            'items': [CDK列表],
            'total': 总记录数,
            'page': 当前页,
            'limit': 每页数量
        }
    """
    # 构建查询条件
    query = CDK.query

    # 模糊搜索（批次号或CDK码）
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            or_(
                CDK.batch_no.like(search_pattern),
                CDK.code.like(search_pattern)
            )
        )

    # 批次号筛选（支持模糊匹配，因为batch_no可能包含batch_name）
    if batch_no:
        query = query.filter(CDK.batch_no.like(f'{batch_no}%'))

    # 状态筛选（转换字符串为数字：unused=0, used=1, void=2）
    if status:
        status_map = {'unused': 0, 'used': 1, 'void': 2}
        if status not in status_map:
            raise ValueError("Invalid status. Must be 'unused', 'used', or 'void'")
        query = query.filter(CDK.status == status_map[status])

    # 按创建时间倒序排列
    query = query.order_by(CDK.created_at.desc())

    # 分页查询
    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    # 获取使用者邮箱（如果有）
    items = []
    for cdk in pagination.items:
        item = _cdk_to_api_dict(cdk)

        # 添加使用者邮箱
        if cdk.used_by:
            user = User.query.get(cdk.used_by)
            item['used_by'] = user.email if user else None
        else:
            item['used_by'] = None

        items.append(item)

    return {
        'items': items,
        'total': pagination.total,
        'page': pagination.page,
        'limit': limit
    }


def void_cdk_batch(batch_no=None, ids=None):
    """
    批量作废CDK

    Args:
        batch_no: 批次号（方式一：按批次作废）
        ids: CDK ID列表（方式二：按ID作废）

    Returns:
        dict: {
            'voided_count': 作废数量
        }

    Raises:
        ValueError: 参数无效
    """
    if not batch_no and not ids:
        raise ValueError("Either batch_no or ids must be provided")

    if batch_no and ids:
        raise ValueError("Cannot specify both batch_no and ids")

    # 构建查询条件
    query = CDK.query

    if batch_no:
        # 按批次作废（支持模糊匹配，因为batch_no可能包含batch_name）
        query = query.filter(CDK.batch_no.like(f'{batch_no}%'))
    else:
        # 按ID作废
        query = query.filter(CDK.id.in_(ids))

    # 只作废未使用的CDK（已使用的不能作废）
    query = query.filter(CDK.status == 0)

    # 更新状态为已作废
    voided_count = query.update({'status': 2}, synchronize_session=False)
    db.session.commit()

    return {
        'voided_count': voided_count
    }


def _cdk_to_api_dict(cdk):
    """
    将CDK模型转换为API格式的字典

    Args:
        cdk: CDK模型实例

    Returns:
        dict: API格式的CDK数据
    """
    # 解析batch_no和batch_name
    batch_no = cdk.batch_no
    batch_name = None
    if batch_no and '|' in batch_no:
        parts = batch_no.split('|', 1)
        batch_no = parts[0]
        batch_name = parts[1]

    # 状态转换：0=unused, 1=used, 2=void
    status_map = {0: 'unused', 1: 'used', 2: 'void'}
    status = status_map.get(cdk.status, 'unused')

    # 类型转换：universal=multi, once=once
    type_display = 'multi' if cdk.type == 'universal' else 'once'

    return {
        'id': cdk.id,
        'code': cdk.code,
        'value': cdk.points,  # 接口使用value，数据库是points
        'batch_no': batch_no,
        'batch_name': batch_name,
        'type': type_display,
        'status': status,
        'used_at': cdk.used_at.isoformat() if cdk.used_at else None,
        'grant_level': cdk.grant_level,
        'expire_at': cdk.expire_at.isoformat() if cdk.expire_at else None,
        'created_at': cdk.created_at.isoformat() if cdk.created_at else None,
    }
