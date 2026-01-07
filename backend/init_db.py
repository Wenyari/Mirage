"""
项目初始化脚本
用于创建数据库表、初始化数据等

重要更新：
- Task 表新增 upstream_task_id 字段（上游API任务ID）
- Task 表新增 progress 字段（任务进度 0-100）
- Task 表 status 新增 cancelled 状态（已取消）
"""
from app import create_app
from app.extensions import db
from app.models import User, MembershipConfig, Model, ModelConfig, ApiKey, ApiKeyModel, Task
import bcrypt

app = create_app()


def init_database():
    """
    初始化数据库表

    创建的表包括：
    - users: 用户表
    - membership_configs: 会员等级配置表
    - models: 模型基本信息表
    - model_configs: 模型配置表（包含价格、允许等级）
    - api_keys: API密钥池管理表
    - tasks: 任务表（包含 upstream_task_id, progress 等字段）
    - cdk: CDK兑换码表
    - transactions: 资金流水表
    """
    with app.app_context():
        print("Dropping existing database tables...")
        db.drop_all()
        print("✓ Existing tables dropped")

        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created successfully")
        print("\nCreated tables:")
        print("  - users (with balance, level)")
        print("  - membership_configs (T1-T5 tiers)")
        print("  - models (model registry)")
        print("  - model_configs (pricing & permissions)")
        print("  - api_keys (key pool management)")
        print("  - tasks (with upstream_task_id, progress, status)")
        print("  - cdk (redemption codes)")
        print("  - transactions (financial records)")


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


def init_models():
    """初始化模型基本信息"""
    with app.app_context():
        models = [
            {
                'key': 'sora-2',
                'name': 'sora-2',
                'enabled': 1,
                'description': 'OpenAI Sora 视频生成模型',
                'color': 'bg-blue-500',
                'icon_url': None,
                'max_concurrency_limit': 10,
                'tags': ['video', 'generation']
            },
            {
                'key': 'nano-banana',
                'name': 'nano-banana',
                'enabled': 1,
                'description': 'Nano Banana 图片生成模型',
                'color': 'bg-purple-500',
                'icon_url': None,
                'max_concurrency_limit': 10,
                'tags': ['image', 'generation']
            }
        ]

        print("Initializing models...")
        for model_data in models:
            model = Model.query.filter_by(key=model_data['key']).first()
            if not model:
                model = Model(**model_data)
                db.session.add(model)
                print(f"  ✓ Created {model_data['name']}")
            else:
                print(f"  - {model_data['name']} already exists")

        db.session.commit()
        print("✓ Models initialized")


def init_model_configs():
    """初始化模型配置"""
    with app.app_context():
        configs = [
            {
                'model': 'sora-2',
                'allowed_tiers': ["T3", "T4", "T5"],
                'cost_per_call': 100.00,
                # params 用于存放模型特定的可配置项（如 durations、hd 等）
                'params': {"durations": [10, 15], "hd_supported": True,
                    "aspect_ratio": [
                        "16:9",
                        "9:16"
                    ]},
                'token_cost_config': {"enabled": False},
                'is_active': 1,
                'description': 'Sora 视频生成配置'
            },
            {
                'model': 'nano-banana',
                'allowed_tiers': ["T3", "T4", "T5"],
                'cost_per_call': 20.00,
                # params 用于存放模型特定的可配置项（如 aspect_ratio 等）
                'params': {
                    "aspect_ratio": [
                        "16:9",
                        "1:1",
                        "9:16"
                    ]
                },
                'token_cost_config': {"enabled": False},
                'is_active': 1,
                'description': 'Nano Banana 图片生成配置'
            }
        ]

        print("Initializing model configs...")
        for config_data in configs:
            config = ModelConfig.query.filter_by(model=config_data['model']).first()
            if not config:
                config = ModelConfig(**config_data)
                db.session.add(config)
                print(f"  ✓ Created config for {config_data['model']}")
            else:
                print(f"  - Config for {config_data['model']} already exists")

        db.session.commit()
        print("✓ Model configs initialized")


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
        print("  Note: api_base is the default base URL, each model can have its own endpoint")

        keys = [
            {
                "api_base": "https://ai.t8star.cn",  # 默认基础地址
                "key_secret": "***REMOVED***",
                "max_concurrency": 5,
                "status": 1,
                "weight": 10,
                # 模型配置：每个模型可以有独立的 api_base
                "model_configs": [
                    {
                        "model": "nano-banana",
                        "api_base": "https://ai.t8star.cn/v1/images/generations"
                    },
                    {
                        "model": "sora-2",
                        "api_base": "https://ai.t8star.cn/v2/videos/generations"
                    }
                ]
            }
        ]

        for key_data in keys:
            # 提取 model_configs（不能直接传给 ApiKey 构造函数）
            model_configs = key_data.pop('model_configs', [])

            # 创建 ApiKey 对象（只包含基本字段）
            api_key = ApiKey(
                api_base=key_data['api_base'],
                key_secret=key_data['key_secret'],
                max_concurrency=key_data['max_concurrency'],
                status=key_data['status'],
                weight=key_data['weight']
            )

            # 添加到 session 并 flush，以获取 api_key.id
            db.session.add(api_key)
            db.session.flush()

            # 为每个模型创建关联记录
            for config in model_configs:
                # 检查模型是否存在
                model = Model.query.filter_by(key=config['model']).first()
                if not model:
                    print(f"  ⚠️  Model '{config['model']}' not found, skipping...")
                    continue

                # 创建 ApiKeyModel 关联记录
                api_key_model = ApiKeyModel(
                    api_key_id=api_key.id,
                    model=config['model'],
                    api_base=config['api_base']
                )
                db.session.add(api_key_model)

            models_str = ', '.join([c['model'] for c in model_configs])
            print(f"  ✓ Created API key for models: {models_str}")

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

        # 创建测试普通用户
        password_hash = bcrypt.hashpw('***REMOVED***'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        normal = User(
            email="demo@example.com",
            password_hash=password_hash,
            balance=10000.00,
            level=1,
            role='user',
            status=1
        )

        db.session.add(normal)  
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

    # 3. 初始化模型信息
    init_models()
    print()

    # 4. 初始化模型配置
    init_model_configs()
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
    print("Database Schema Updates:")
    print("  ✓ tasks.upstream_task_id - 上游API任务ID")
    print("  ✓ tasks.progress - 任务进度（0-100）")
    print("  ✓ tasks.status - 新增 'cancelled' 状态")
    print()
    print("Next steps:")
    print("1. Update API keys in the database with your actual keys")
    print("2. Enable API keys by setting status=1")
    print("3. Start the application:")
    print("   Terminal 1: python run.py")
    print("   Terminal 2: python worker.py")
    print("   Terminal 3: python scheduler.py")
    print()
    print("Note: If upgrading from old schema, run:")
    print("   python migrations/add_upstream_task_id.py")


if __name__ == '__main__':
    main()
