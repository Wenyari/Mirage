"""
项目初始化脚本
用于创建数据库表、初始化数据等
"""
from app import create_app
from app.extensions import db
from app.models import User, MembershipConfig, ModelPricing
import bcrypt

app = create_app()


def init_database():
    """初始化数据库表"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created successfully")


def init_membership_configs():
    """初始化会员等级配置"""
    with app.app_context():
        configs = [
            {'level': 1, 'name': 'T1', 'concurrency_limit': 1, 'queue_priority': 0, 'remark': '基础用户 - 1个并发'},
            {'level': 2, 'name': 'T2', 'concurrency_limit': 2, 'queue_priority': 5, 'remark': '进阶用户 - 2个并发'},
            {'level': 3, 'name': 'T3', 'concurrency_limit': 3, 'queue_priority': 10, 'remark': '高级用户 - 3个并发'},
            {'level': 4, 'name': 'T4', 'concurrency_limit': 4, 'queue_priority': 15, 'remark': 'VIP用户 - 4个并发 + 优先队列'},
            {'level': 5, 'name': 'T5', 'concurrency_limit': 5, 'queue_priority': 20, 'remark': '至尊VIP - 5个并发 + 最高优先级'},
        ]

        print("Initializing membership configs...")
        for config_data in configs:
            config = MembershipConfig.query.filter_by(level=config_data['level']).first()
            if not config:
                config = MembershipConfig(**config_data)
                db.session.add(config)
                print(f"  ✓ Created {config_data['name']}")
            else:
                print(f"  - {config_data['name']} already exists")

        db.session.commit()
        print("✓ Membership configs initialized")


def init_model_pricing():
    """初始化模型定价"""
    with app.app_context():
        models = [
            {
                'model_key': 'sora-v2',
                'base_cost': 100.00,
                'is_active': 1,
                'config': {'max_duration': 60, 'quality_options': ['standard', 'hd']}
            },
            {
                'model_key': 'sora-turbo',
                'base_cost': 50.00,
                'is_active': 1,
                'config': {'max_duration': 30, 'quality_options': ['standard']}
            },
            {
                'model_key': 'midjourney-v6',
                'base_cost': 80.00,
                'is_active': 1,
                'config': {'aspect_ratios': ['1:1', '16:9', '9:16']}
            },
        ]

        print("Initializing model pricing...")
        for model_data in models:
            model = ModelPricing.query.filter_by(model_key=model_data['model_key']).first()
            if not model:
                model = ModelPricing(**model_data)
                db.session.add(model)
                print(f"  ✓ Created {model_data['model_key']}")
            else:
                print(f"  - {model_data['model_key']} already exists")

        db.session.commit()
        print("✓ Model pricing initialized")


def create_admin_user(email='admin@example.com', password='admin123'):
    """创建管理员账号"""
    with app.app_context():
        print(f"Creating admin user: {email}")

        # 检查是否已存在
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"  - Admin user already exists")
            return

        # Hash 密码
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # 创建管理员
        admin = User(
            email=email,
            password_hash=password_hash,
            balance=10000.00,
            level=5,
            role='admin',
            status=1
        )

        db.session.add(admin)
        db.session.commit()

        print(f"✓ Admin user created")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"  ⚠️  Please change the password after first login!")


def main():
    """主函数"""
    print("=" * 60)
    print("AIGC Video Platform - Database Initialization")
    print("=" * 60)
    print()

    # 1. 创建数据库表
    init_database()
    print()

    # 2. 初始化会员配置
    init_membership_configs()
    print()

    # 3. 初始化模型定价
    init_model_pricing()
    print()

    # 4. 创建管理员账号
    create_admin_user()
    print()

    print("=" * 60)
    print("✓ Initialization completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()
