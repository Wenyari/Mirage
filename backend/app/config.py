"""
Flask Configuration
读取 .env 环境变量并加载配置
"""
import os
from datetime import timedelta
from urllib.parse import quote_plus
from dotenv import load_dotenv

# 加载 .env 文件
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """应用配置类"""

    # Flask 基础配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-please-change')
    DEBUG = os.getenv('FLASK_ENV') == 'development'

    # 数据库配置 (MySQL)
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'admin')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'sora_platform')
    
    # 自动处理密码中的特殊字符
    if MYSQL_PASSWORD:
        MYSQL_PASSWORD = quote_plus(MYSQL_PASSWORD)
        
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG  # 开发环境打印 SQL 语句
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

    # JWT 配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-please-change')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 604800)))  # 默认7天
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # Redis 配置
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    
    if REDIS_PASSWORD:
        REDIS_PASSWORD = quote_plus(REDIS_PASSWORD)
        REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
    else:
        REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

    # 邮件配置 (SMTP)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@example.com')

    # 第三方 Sora API 配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SORA_API_BASE_URL = os.getenv('SORA_API_BASE_URL', 'https://ai.t8star.cn')
    SORA_API_ENDPOINT = os.getenv('SORA_API_ENDPOINT', 'https://api.openai.com/v1')  # 兼容旧配置

    # 限流配置
    RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', 100))

    # CORS 配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')

    # RQ 队列配置
    RQ_REDIS_URL = REDIS_URL
    RQ_QUEUES = ['high_priority', 'default']  # 高优先级队列、普通队列

    # Cloudflare R2 对象存储配置
    R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID')
    R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
    R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
    R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')
    R2_PUBLIC_URL = os.getenv('R2_PUBLIC_URL')  # R2 自定义域名（如 https://files.yourdomain.com）
