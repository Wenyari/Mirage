"""
Flask 插件统一管理
防止循环引用，所有第三方插件在这里实例化
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from flask_mail import Mail
import redis

# 初始化插件但不绑定 app（工厂模式）
db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
migrate = Migrate()
mail = Mail()

# Redis 客户端（手动初始化）
redis_client = None


def init_redis(app):
    """初始化 Redis 客户端"""
    global redis_client
    redis_url = app.config['REDIS_URL']
    redis_client = redis.from_url(redis_url, decode_responses=True)
    return redis_client
