"""
数据库迁移：将 tasks 表的 input_file_url 字段从 TEXT 改为 JSON (str list)
支持多个文件 URL 的存储

运行方式:
    python migrations/change_input_file_url_to_json.py           # 升级
    python migrations/change_input_file_url_to_json.py downgrade  # 回滚
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
    """将 input_file_url 从 TEXT 改为 JSON"""
    with app.app_context():
        print("=" * 60)
        print("Starting migration: Change input_file_url to JSON")
        print("=" * 60)

        try:
            inspector = inspect(db.engine)

            # Step 1: 检查字段类型
            print("\n[1/4] Checking current column type...")
            columns = {col['name']: col for col in inspector.get_columns('tasks')}

            if 'input_file_url' not in columns:
                print("  - input_file_url column doesn't exist!")
                return

            current_type = str(columns['input_file_url']['type']).upper()
            print(f"  - Current type: {current_type}")

            if 'JSON' in current_type:
                print("  - Column is already JSON type, skipping...")
                return

            # Step 2: 创建临时列
            print("\n[2/4] Creating temporary JSON column...")
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE tasks
                    ADD COLUMN input_file_url_new JSON NULL
                    COMMENT '参考图/视频 URL 列表'
                """))
                conn.commit()
            print("  ✓ Temporary column created")

            # Step 3: 迁移数据（将 TEXT 转换为 JSON 数组）
            print("\n[3/4] Migrating data from TEXT to JSON...")
            with db.engine.connect() as conn:
                # 将非空的 TEXT 值转换为单元素 JSON 数组
                # 空值或 NULL 保持为 NULL
                conn.execute(text("""
                    UPDATE tasks
                    SET input_file_url_new = CASE
                        WHEN input_file_url IS NULL OR input_file_url = '' THEN NULL
                        ELSE JSON_ARRAY(input_file_url)
                    END
                """))
                conn.commit()
            print("  ✓ Data migrated successfully")

            # Step 4: 删除旧列，重命名新列
            print("\n[4/4] Replacing old column with new one...")
            with db.engine.connect() as conn:
                # 删除旧列
                conn.execute(text("ALTER TABLE tasks DROP COLUMN input_file_url"))
                # 重命名新列
                conn.execute(text("ALTER TABLE tasks CHANGE input_file_url_new input_file_url JSON NULL"))
                conn.commit()
            print("  ✓ Column replaced successfully")

            print("\n" + "=" * 60)
            print("✓ Migration completed successfully!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Update API code to accept input_file_url as an array")
            print("2. Update frontend to support multiple file uploads")
            print("3. Test with both single and multiple file URLs")

        except Exception as e:
            print(f"\n{'=' * 60}")
            print("✗ Migration failed!")
            print("=" * 60)
            print(f"\nError: {e}")
            print("\nManual rollback SQL:")
            print("  ALTER TABLE tasks DROP COLUMN input_file_url_new;")
            raise


def downgrade():
    """将 input_file_url 从 JSON 改回 TEXT"""
    with app.app_context():
        print("=" * 60)
        print("Starting rollback: Change input_file_url back to TEXT")
        print("=" * 60)

        try:
            inspector = inspect(db.engine)

            # Step 1: 检查字段类型
            print("\n[1/4] Checking current column type...")
            columns = {col['name']: col for col in inspector.get_columns('tasks')}

            if 'input_file_url' not in columns:
                print("  - input_file_url column doesn't exist!")
                return

            current_type = str(columns['input_file_url']['type']).upper()
            print(f"  - Current type: {current_type}")

            if 'TEXT' in current_type:
                print("  - Column is already TEXT type, skipping...")
                return

            # Step 2: 创建临时列
            print("\n[2/4] Creating temporary TEXT column...")
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE tasks
                    ADD COLUMN input_file_url_old TEXT NULL
                    COMMENT '参考图/视频'
                """))
                conn.commit()
            print("  ✓ Temporary column created")

            # Step 3: 迁移数据（JSON 数组转回 TEXT，取第一个元素）
            print("\n[3/4] Migrating data from JSON to TEXT...")
            with db.engine.connect() as conn:
                # 取 JSON 数组的第一个元素（如果存在）
                conn.execute(text("""
                    UPDATE tasks
                    SET input_file_url_old = CASE
                        WHEN input_file_url IS NULL THEN NULL
                        WHEN JSON_LENGTH(input_file_url) > 0 THEN JSON_UNQUOTE(JSON_EXTRACT(input_file_url, '$[0]'))
                        ELSE NULL
                    END
                """))
                conn.commit()
            print("  ✓ Data migrated successfully")
            print("  ⚠️  WARNING: Only the first URL was preserved for each task")

            # Step 4: 删除旧列，重命名新列
            print("\n[4/4] Replacing old column with new one...")
            with db.engine.connect() as conn:
                # 删除旧列
                conn.execute(text("ALTER TABLE tasks DROP COLUMN input_file_url"))
                # 重命名新列
                conn.execute(text("ALTER TABLE tasks CHANGE input_file_url_old input_file_url TEXT NULL"))
                conn.commit()
            print("  ✓ Column replaced successfully")

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
        print("\n⚠️  WARNING: This will convert input_file_url back to TEXT!")
        print("⚠️  Only the FIRST URL in each array will be preserved!")
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
            print("  mysqldump -u root -p sora_platform > backup_$(date +%Y%m%d_%H%M%S).sql")
