"""
数据库迁移：添加 upstream_task_id 字段
用于存储上游 API 返回的任务 ID

运行方式:
    python migrations/add_upstream_task_id.py
"""
from app import create_app
from app.extensions import db

app = create_app()


def upgrade():
    """添加 upstream_task_id 字段"""
    with app.app_context():
        print("Adding upstream_task_id column to tasks table...")

        try:
            # 检查字段是否已存在
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('tasks')]

            if 'upstream_task_id' in columns:
                print("  - upstream_task_id column already exists, skipping...")
                return

            # 添加字段
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE tasks
                    ADD COLUMN upstream_task_id VARCHAR(255) NULL
                """))
                conn.commit()

                # 添加索引
                conn.execute(text("""
                    CREATE INDEX idx_upstream_task_id ON tasks(upstream_task_id)
                """))
                conn.commit()

            print("✓ Successfully added upstream_task_id column and index")

        except Exception as e:
            print(f"✗ Migration failed: {e}")
            print("\nAlternative SQL commands (run manually if needed):")
            print("ALTER TABLE tasks ADD COLUMN upstream_task_id VARCHAR(255) NULL;")
            print("CREATE INDEX idx_upstream_task_id ON tasks(upstream_task_id);")
            raise


def downgrade():
    """移除 upstream_task_id 字段"""
    with app.app_context():
        print("Removing upstream_task_id column from tasks table...")

        try:
            from sqlalchemy import text

            with db.engine.connect() as conn:
                # 删除索引
                conn.execute(text("""
                    DROP INDEX IF EXISTS idx_upstream_task_id
                """))
                conn.commit()

                # 删除字段
                conn.execute(text("""
                    ALTER TABLE tasks
                    DROP COLUMN upstream_task_id
                """))
                conn.commit()

            print("✓ Successfully removed upstream_task_id column and index")

        except Exception as e:
            print(f"✗ Rollback failed: {e}")
            raise


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        downgrade()
    else:
        upgrade()
