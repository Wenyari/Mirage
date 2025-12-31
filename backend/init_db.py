"""
项目初始化脚本
用于创建数据库表、初始化数据等
"""
from app import create_app
from app.extensions import db
from app.models import User, MembershipConfig, Platform, PlatformConfig, ApiKey
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
            {'level': 1, 'name': 'T1', 'concurrent_limit': 1, 'queue_weight': 1, 'price': 0.00, 'description': '免费用户'},
            {'level': 2, 'name': 'T2', 'concurrent_limit': 3, 'queue_weight': 2, 'price': 29.00, 'description': '基础会员'},
            {'level': 3, 'name': 'T3', 'concurrent_limit': 5, 'queue_weight': 3, 'price': 99.00, 'description': '高级会员'},
            {'level': 4, 'name': 'T4', 'concurrent_limit': 10, 'queue_weight': 4, 'price': 299.00, 'description': '专业会员'},
            {'level': 5, 'name': 'T5', 'concurrent_limit': 20, 'queue_weight': 5, 'price': 999.00, 'description': '旗舰会员'},
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


def init_platforms():
    """初始化平台基本信息"""
    with app.app_context():
        platforms = [
            {
                'key': 'openai',
                'name': 'OpenAI',
                'enabled': 1,
                'description': 'OpenAI GPT 系列模型',
                'color': 'bg-green-500',
                'icon_url': None,
                'max_concurrency_limit': 20
            },
            {
                'key': 'sora',
                'name': 'Sora',
                'enabled': 1,
                'description': 'OpenAI Sora 视频生成模型',
                'color': 'bg-blue-500',
                'icon_url': None,
                'max_concurrency_limit': 10
            },
            {
                'key': 'midjourney',
                'name': 'Midjourney',
                'enabled': 1,
                'description': 'Midjourney 图像生成',
                'color': 'bg-purple-500',
                'icon_url': None,
                'max_concurrency_limit': 15
            },
        ]

        print("Initializing platforms...")
        for platform_data in platforms:
            platform = Platform.query.filter_by(key=platform_data['key']).first()
            if not platform:
                platform = Platform(**platform_data)
                db.session.add(platform)
                print(f"  ✓ Created {platform_data['name']}")
            else:
                print(f"  - {platform_data['name']} already exists")

        db.session.commit()
        print("✓ Platforms initialized")


def init_platform_configs():
    """初始化平台配置"""
    with app.app_context():
        configs = [
            {
                'platform': 'openai',
                'allowed_tiers': ["T1", "T2", "T3", "T4", "T5"],
                'cost_per_call': 10.00,
                'token_cost_config': {
                    "enabled": True,
                    "input_cost": 0.03,
                    "output_cost": 0.06
                },
                'is_active': 1,
                'description': 'OpenAI GPT 模型配置'
            },
            {
                'platform': 'sora',
                'allowed_tiers': ["T3", "T4", "T5"],
                'cost_per_call': 100.00,
                'token_cost_config': {"enabled": False},
                'is_active': 1,
                'description': 'Sora 视频生成配置'
            },
            {
                'platform': 'midjourney',
                'allowed_tiers': ["T2", "T3", "T4", "T5"],
                'cost_per_call': 50.00,
                'token_cost_config': {"enabled": False},
                'is_active': 1,
                'description': 'Midjourney 图像生成配置'
            },
        ]

        print("Initializing platform configs...")
        for config_data in configs:
            config = PlatformConfig.query.filter_by(platform=config_data['platform']).first()
            if not config:
                config = PlatformConfig(**config_data)
                db.session.add(config)
                print(f"  ✓ Created config for {config_data['platform']}")
            else:
                print(f"  - Config for {config_data['platform']} already exists")

        db.session.commit()
        print("✓ Platform configs initialized")


def init_api_keys():
    """初始化示例 API 密钥（仅用于演示，实际使用时请替换）"""
    with app.app_context():
        # 检查是否已有密钥
        existing_keys = ApiKey.query.count()
        if existing_keys > 0:
            print("  - API keys already exist, skipping...")
            return

        print("Initializing sample API keys...")
        print("  ⚠️  Please replace these with your actual API keys!")

        keys = [
            {
                'platform': 'openai',
                'key_secret': 'sk-proj-REPLACE-WITH-YOUR-OPENAI-KEY',
                'max_concurrency': 5,
                'weight': 10,
                'status': 0  # 默认停用，需要替换后启用
            },
            {
                'platform': 'sora',
                'key_secret': 'sk-sora-REPLACE-WITH-YOUR-SORA-KEY',
                'max_concurrency': 2,
                'weight': 5,
                'status': 0
            },
        ]

        for key_data in keys:
            api_key = ApiKey(**key_data)
            db.session.add(api_key)
            print(f"  ✓ Created API key for {key_data['platform']} (DISABLED)")

        db.session.commit()
        print("✓ Sample API keys initialized")


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

    # 3. 初始化平台信息
    init_platforms()
    print()

    # 4. 初始化平台配置
    init_platform_configs()
    print()

    # 5. 初始化 API 密钥
    init_api_keys()
    print()

    # 6. 创建管理员账号
    create_admin_user()
    print()

    print("=" * 60)
    print("✓ Initialization completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Update API keys in the database with your actual keys")
    print("2. Enable API keys by setting status=1")
    print("3. Start the application: python run.py")
    print("4. Start the worker: python worker.py")


if __name__ == '__main__':
    main()
