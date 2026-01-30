"""
Flask 应用工厂 (Factory Pattern)
使用工厂模式创建 Flask 应用实例
"""
from flask import Flask, jsonify
from app.config import Config
from app.extensions import db, jwt, cors, migrate, mail, init_redis


def create_app(config_class=Config):
    """
    创建并配置 Flask 应用

    Args:
        config_class: 配置类，默认使用 Config

    Returns:
        Flask app 实例
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 1. 初始化所有插件
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
    migrate.init_app(app, db)
    mail.init_app(app)
    init_redis(app)

    # 2. 注册蓝图 (Blueprint)
    register_blueprints(app)

    # 3. 注册错误处理器
    register_error_handlers(app)

    # 4. 注册 JWT 回调
    register_jwt_callbacks(app)

    # 5. 健康检查路由
    @app.route('/health')
    def health_check():
        return jsonify({"status": "ok", "message": "Service is running"}), 200

    return app


def register_blueprints(app):
    """注册所有蓝图"""
    from app.api import auth_bp, users_bp, tasks_bp, wallet_bp, activities_bp, models_bp, admin_bp, announcements_bp
    from app.api.upload import bp as upload_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(wallet_bp)
    app.register_blueprint(activities_bp)
    app.register_blueprint(models_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(announcements_bp)


def register_error_handlers(app):
    """注册全局错误处理器"""

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"code": 400, "msg": "Bad Request", "data": None}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"code": 401, "msg": "Unauthorized", "data": None}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"code": 403, "msg": "Forbidden", "data": None}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"code": 404, "msg": "Resource Not Found", "data": None}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"code": 500, "msg": "Internal Server Error", "data": None}), 500


def register_jwt_callbacks(app):
    """注册 JWT 回调函数"""

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"code": 401, "msg": "Token has expired", "data": None}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"code": 401, "msg": "Invalid token", "data": None}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"code": 401, "msg": "Authorization token is missing", "data": None}), 401
