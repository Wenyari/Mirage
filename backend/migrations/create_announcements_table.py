"""
数据库迁移：创建公告表
包含公告标题、内容、发布时间等信息

运行方式:
    python migrations/create_announcements_table.py           # 升级
    python migrations/create_announcements_table.py downgrade  # 回滚
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from sqlalchemy import text, inspect
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

app = create_app()


def upgrade():
    """创建 announcements 表"""
    with app.app_context():
        print("=" * 60)
        print("Starting migration: Create announcements table")
        print("=" * 60)

        try:
            inspector = inspect(db.engine)

            # Step 1: 检查表是否已存在
            print("\n[1/3] Checking if announcements table exists...")
            tables = inspector.get_table_names()

            if 'announcements' in tables:
                print("  - announcements table already exists, skipping...")
                return

            # Step 2: 创建表
            print("\n[2/3] Creating announcements table...")
            with db.engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE announcements (
                        id INT AUTO_INCREMENT PRIMARY KEY COMMENT '公告ID',
                        title VARCHAR(200) NOT NULL COMMENT '公告标题',
                        content TEXT NOT NULL COMMENT '公告内容',
                        publish_time DATETIME NOT NULL COMMENT '发布时间',
                        is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用(0=禁用,1=启用)',
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                        INDEX idx_publish_time (publish_time),
                        INDEX idx_is_active (is_active)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='公告配置表';
                """))
                conn.commit()

            print("  ✓ Table created successfully")

            # Step 3: 插入初始数据
            print("\n[3/3] Inserting initial announcements...")
            
            # 获取当前时间
            now = datetime.now(ZoneInfo("Asia/Shanghai"))
            
            # 准备示例公告数据
            sample_announcements = [
                {
                    'title': '欢迎使用 Mirage 平台',
                    'content': '感谢您使用 Mirage AI 平台！我们致力于为您提供最优质的AI服务体验。如有任何问题，请随时联系我们的客服团队。',
                    'publish_time': now - timedelta(days=1)
                },
                {
                    'title': '新功能上线通知',
                    'content': 'AI图像生成功能现已正式上线！您可以通过简单的文字描述，让AI为您创作精美的图片。快来体验吧！',
                    'publish_time': now + timedelta(hours=1)
                }
            ]
            
            with db.engine.connect() as conn:
                for announcement in sample_announcements:
                    conn.execute(text("""
                        INSERT INTO announcements (title, content, publish_time, is_active, created_at, updated_at)
                        VALUES (:title, :content, :publish_time, 1, :created_at, :updated_at)
                    """), {
                        'title': announcement['title'],
                        'content': announcement['content'],
                        'publish_time': announcement['publish_time'],
                        'created_at': now,
                        'updated_at': now
                    })
                conn.commit()

            print(f"  ✓ Inserted {len(sample_announcements)} sample announcements")

            print("\n" + "=" * 60)
            print("✓ Migration completed successfully!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Create announcement service in app/services/admin/announcement_service.py")
            print("2. Create admin API in app/api/admin/announcements.py")
            print("3. Create user API in app/api/announcements.py")

        except Exception as e:
            print(f"\n{'=' * 60}")
            print("✗ Migration failed!")
            print("=" * 60)
            print(f"\nError: {e}")
            raise


def downgrade():
    """删除 announcements 表"""
    with app.app_context():
        print("=" * 60)
        print("Starting rollback: Drop announcements table")
        print("=" * 60)

        try:
            inspector = inspect(db.engine)

            # 检查表是否存在
            print("\n[1/1] Dropping announcements table...")
            tables = inspector.get_table_names()

            if 'announcements' not in tables:
                print("  - announcements table doesn't exist, skipping...")
                return

            with db.engine.connect() as conn:
                conn.execute(text("DROP TABLE announcements"))
                conn.commit()

            print("  ✓ Table dropped successfully")

            print("\n" + "=" * 60)
            print("✓ Rollback completed successfully!")
            print("=" * 60)

        except Exception as e:
            print(f"\n{'=' * 60}")
            print("✗ Rollback failed!")
            print("=" * 60)
            print(f"\nError: {e}")
            raise


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        print("\n⚠️  WARNING: This will drop the announcements table and all data!")
        confirm = input("\nType 'yes' to confirm: ")
        if confirm.lower() == 'yes':
            downgrade()
        else:
            print("Rollback cancelled.")
    else:
        print("\n🚀 Starting upgrade migration...")
        confirm = input("\n⚠️  Have you backed up your database? Type 'yes' to continue: ")
        if confirm.lower() == 'yes':
            upgrade()
        else:
            print("Migration cancelled. Please backup your database first:")
            print("  mysqldump -u root -p mirage_db > backup_$(date +%Y%m%d_%H%M%S).sql")
