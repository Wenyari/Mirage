"""
Flask Configuration
读取 .env 环境变量并加载配置
"""
import os
from datetime import timedelta
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
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI',
                                        'mysql+pymysql://root:admin@localhost:3306/sora_platform?charset=utf8mb4')
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
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

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
