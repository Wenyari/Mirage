"""
数据库迁移：为 models 表添加 tags 字段
用于模型分类（如视频生成、对话、图片生成等）

运行方式:
    python migrations/add_tags_to_models.py           # 升级
    python migrations/add_tags_to_models.py downgrade  # 回滚
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from sqlalchemy import text, inspect

app = create_app()


def upgrade():
    """添加 tags 字段"""
    with app.app_context():
        print("=" * 60)
        print("Starting migration: Add tags to models table")
        print("=" * 60)

        try:
            inspector = inspect(db.engine)

            # Step 1: 检查字段是否已存在
            print("\n[1/2] Checking if tags column exists...")
            columns = [col['name'] for col in inspector.get_columns('models')]

            if 'tags' in columns:
                print("  - tags column already exists, skipping...")
                return

            # Step 2: 添加字段
            print("\n[2/2] Adding tags column...")
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE models
                    ADD COLUMN tags JSON NULL
                    COMMENT '模型分类标签，如 ["video", "generation"]'
                """))
                conn.commit()

            print("  ✓ Column added successfully")

            print("\n" + "=" * 60)
            print("✓ Migration completed successfully!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Run init_db.py to populate sample tags for existing models")
            print("2. Update API code to support tags parameter")
            print("3. Update frontend to display and filter by tags")

        except Exception as e:
            print(f"\n{'=' * 60}")
            print("✗ Migration failed!")
            print("=" * 60)
            print(f"\nError: {e}")
            print("\nManual SQL command:")
            print("  ALTER TABLE models ADD COLUMN tags JSON NULL;")
            raise


def downgrade():
    """移除 tags 字段"""
    with app.app_context():
        print("=" * 60)
        print("Starting rollback: Remove tags from models table")
        print("=" * 60)

        try:
            inspector = inspect(db.engine)

            # 检查字段是否存在
            print("\n[1/1] Removing tags column...")
            columns = [col['name'] for col in inspector.get_columns('models')]

            if 'tags' not in columns:
                print("  - tags column doesn't exist, skipping...")
                return

            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE models
                    DROP COLUMN tags
                """))
                conn.commit()

            print("  ✓ Column removed successfully")

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
        print("\n⚠️  WARNING: This will remove the tags column from models table!")
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
