"""
模型相关 API
"""
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import get_jwt_identity
from app.models.model import Model, ModelConfig
from app.models.user import MembershipConfig, User
from app.extensions import db

bp = Blueprint('models', __name__, url_prefix='/api/models')


@bp.route('/', methods=['GET'])
def list_models():
    """
    获取模型列表及其配置
    Optional query params:
      - page, size (pagination) -- handled by simple limits
    If request contains Authorization token, will mark `is_available` based on user's membership.
    """
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 50))
        offset = (page - 1) * size

        # fetch models with their config (lazy relationship)
        models = Model.query.order_by(Model.created_at.desc()).offset(offset).limit(size).all()

        # attempt to get current user tier (if token present)
        user_tier = None
        try:
            uid = get_jwt_identity()
            if uid:
                user = User.query.get(int(uid))
                if user:
                    membership = MembershipConfig.query.filter_by(level=user.level).first()
                    user_tier = membership.name if membership else f"T{user.level}"
        except Exception:
            # ignore auth errors, treat as anonymous
            user_tier = None

        result = []
        for m in models:
            md = m.to_dict()
            cfg = None
            try:
                if m.config:
                    cfg = m.config.to_dict()
            except Exception:
                cfg = None

            item = {
                'model': md,
                'config': cfg,
            }

            # availability based on user_tier and config.allowed_tiers
            is_available = True
            if cfg and user_tier:
                allowed = cfg.get('allowed_tiers') or []
                is_available = user_tier in allowed
            item['is_available'] = is_available

            result.append(item)

        return jsonify({"code": 200, "msg": "Success", "data": {"list": result, "page": page, "size": size}}), 200
    except Exception as e:
        current_app.logger.exception("list_models failed")
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


