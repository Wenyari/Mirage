"""
鉴权服务层 (Auth Service)
包含注册、登录、验证码发送等核心业务逻辑
"""
import random
import re
import bcrypt
from datetime import datetime
from flask import current_app
from flask_jwt_extended import create_access_token
from flask_mail import Message
from app.extensions import db, mail
from app.models import User


def send_verify_code(email: str):
    """
    发送邮箱验证码

    1. 校验 email 格式
    2. 检查 Redis 限流
    3. 生成 6 位随机数
    4. 存入 Redis (key=verify:email:{email}, ex=300s)
    5. 调用 SMTP 发送邮件

    Args:
        email: 用户邮箱

    Raises:
        ValueError: 邮箱格式错误、发送频繁等
    """
    # Import Redis client at the beginning
    from app.extensions import redis_client
    if redis_client is None:
        raise ValueError("Redis service unavailable")

    # 1. 校验邮箱格式 (使用正则表达式进行更完善的验证)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format")

    # 2. 检查限流 (60秒内不能重复发送)
    rate_key = f"rate:limit:email:{email}"
    if redis_client.get(rate_key):
        raise ValueError("Verification code sent too frequently, please try again later")

    # 3. 生成 6 位随机验证码
    code = str(random.randint(100000, 999999))

    # 4. 存入 Redis (5分钟过期)
    verify_key = f"verify:email:{email}"
    redis_client.setex(verify_key, 300, code)

    # 5. 发送邮件
    try:
        msg = Message(
            subject="Your Verification Code",
            recipients=[email],
            body=f"Your verification code is: {code}\n\nThis code will expire in 5 minutes."
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {e}")
        raise ValueError("Failed to send verification code")

    # 设置限流 (60秒内不能重复发送)
    redis_client.setex(rate_key, 60, "1")


def register_user(email: str, code: str, password: str) -> int:
    """
    用户注册

    1. 从 Redis 取验证码比对
    2. 检查用户是否已存在
    3. Hash 加密密码
    4. 写入数据库，默认 level=1

    Args:
        email: 用户邮箱
        code: 验证码
        password: 明文密码

    Returns:
        int: 新用户的 ID

    Raises:
        ValueError: 验证码错误、用户已存在等
    """
    # 1. 验证码校验
    from app.extensions import redis_client
    if redis_client is None:
        raise ValueError("Redis service unavailable - redis_client is None. Check if init_redis() was called during app initialization.")

    verify_key = f"verify:email:{email}"
    stored_code = redis_client.get(verify_key)

    if not stored_code:
        raise ValueError("Verification code expired or not sent")

    if stored_code != code:
        raise ValueError("Invalid verification code")

    # 2. 检查用户是否已存在
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        raise ValueError("Email already registered")

    # 3. Hash 加密密码 (Bcrypt)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 4. 创建新用户
    new_user = User(
        email=email,
        password_hash=password_hash,
        balance=0.00,
        level=1,
        role='user',
        status=1
    )

    db.session.add(new_user)
    db.session.commit()

    # Delete verification code from Redis
    redis_client.delete(verify_key)

    return new_user.id


def login_user(email: str, password: str, login_ip: str = None) -> dict:
    """
    用户登录 (含单点登录互斥逻辑)

    1. 校验账号密码
    2. 生成 JWT Token
    3. 【核心】Redis 顶号操作: redis.set(f"auth:token:{user_id}", token, ex=7天)
    4. 更新 last_login_at, login_ip
    5. 返回 token 和用户信息

    Args:
        email: 用户邮箱
        password: 明文密码
        login_ip: 登录 IP (可选)

    Returns:
        dict: {"token": "jwt_str", "user": {...}}

    Raises:
        ValueError: 账号密码错误、账号被封禁等
    """
    # 1. 查询用户
    user = User.query.filter_by(email=email).first()
    if not user:
        raise ValueError("Invalid email or password")

    # 2. 验证密码
    if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise ValueError("Invalid email or password")

    # 3. 检查账号状态
    if user.status == 0:
        raise ValueError("Account has been banned")

    # 4. 生成 JWT Token
    # Ensure identity is a string to avoid jwt subject type validation issues
    token = create_access_token(identity=str(user.id))

    # 5. 【核心】单点登录互斥：将新 Token 存入 Redis
    # 当用户请求时，检查 Redis 中的 Token 是否与请求中的一致
    from app.extensions import redis_client
    if redis_client is None:
        raise ValueError("Redis service unavailable")
    auth_token_key = f"auth:token:{user.id}"
    redis_client.setex(auth_token_key, 604800, token)  # 7天过期

    # 6. 更新最后登录时间和 IP
    user.last_login_at = datetime.now()
    if login_ip:
        user.register_ip = login_ip
    db.session.commit()

    # 7. 返回结果
    return {
        "token": token,
        "user": user.to_dict()
    }


def check_token_validity(user_id: int, current_token: str) -> bool:
    """
    检查 Token 是否有效 (单点登录互斥检查)

    Args:
        user_id: 用户 ID
        current_token: 当前请求的 Token

    Returns:
        bool: Token 是否有效
    """
    from app.extensions import redis_client
    if redis_client is None:
        return False

    auth_token_key = f"auth:token:{user_id}"
    stored_token = redis_client.get(auth_token_key)

    if not stored_token:
        return False

    return stored_token == current_token
