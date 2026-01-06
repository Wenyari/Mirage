"""
数据库迁移：将 ApiKey-Model 关系从一对多改为多对多

运行方式:
    python migrations/convert_apikey_to_many_to_many.py           # 升级
    python migrations/convert_apikey_to_many_to_many.py downgrade  # 回滚
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
    """升级：创建关联表并迁移数据"""
    with app.app_context():
        print("=" * 60)
        print("Starting migration: ApiKey one-to-many -> many-to-many")
        print("=" * 60)

        try:
            inspector = inspect(db.engine)

            # Step 1: 创建关联表
            print("\n[1/4] Creating api_key_models table...")
            if 'api_key_models' not in inspector.get_table_names():
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        CREATE TABLE api_key_models (
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            api_key_id INT NOT NULL,
                            model VARCHAR(50) NOT NULL,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                            FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE CASCADE,
                            FOREIGN KEY (model) REFERENCES models(`key`) ON DELETE CASCADE,

                            UNIQUE KEY uk_key_model (api_key_id, model),
                            INDEX idx_model (model),
                            INDEX idx_api_key_id (api_key_id)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """))
                    conn.commit()
                print("  ✓ Table created successfully")
            else:
                print("  - Table already exists, skipping...")

            # Step 2: 迁移现有数据
            print("\n[2/4] Migrating existing data...")
            with db.engine.connect() as conn:
                # 从 api_keys 表读取现有的 model 关联
                result = conn.execute(text("""
                    SELECT id, model FROM api_keys WHERE model IS NOT NULL
                """))

                rows = result.fetchall()
                migrated = 0

                for row in rows:
                    api_key_id, model = row
                    # 插入到关联表（忽略重复）
                    conn.execute(text("""
                        INSERT IGNORE INTO api_key_models (api_key_id, model)
                        VALUES (:key_id, :model)
                    """), {"key_id": api_key_id, "model": model})
                    migrated += 1

                conn.commit()
                print(f"  ✓ Migrated {migrated} relationships")

            # Step 3: 删除旧索引
            print("\n[3/4] Dropping old indexes...")
            with db.engine.connect() as conn:
                try:
                    conn.execute(text("DROP INDEX idx_model_status ON api_keys"))
                    print("  ✓ Dropped idx_model_status")
                except Exception as e:
                    if "check that column/key exists" in str(e) or "doesn't exist" in str(e):
                        print(f"  - Index idx_model_status not found, skipping...")
                    else:
                        print(f"  ! Warning: {e}")

                conn.commit()

            # Step 4: 删除旧字段
            print("\n[4/4] Dropping old model column...")
            columns = [col['name'] for col in inspector.get_columns('api_keys')]
            if 'model' in columns:
                with db.engine.connect() as conn:
                    # 先删除外键约束
                    try:
                        conn.execute(text("""
                            ALTER TABLE api_keys
                            DROP FOREIGN KEY api_keys_ibfk_1
                        """))
                        print("  ✓ Dropped foreign key constraint")
                    except Exception as e:
                        if "check that column/key exists" in str(e) or "doesn't exist" in str(e):
                            print(f"  - Foreign key not found, skipping...")
                        else:
                            print(f"  ! Warning: {e}")

                    # 删除 model 列
                    conn.execute(text("ALTER TABLE api_keys DROP COLUMN model"))
                    conn.commit()
                print("  ✓ Column dropped successfully")
            else:
                print("  - Column already removed, skipping...")

            print("\n" + "=" * 60)
            print("✓ Migration completed successfully!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Verify data migration:")
            print("   SELECT ak.id, COUNT(akm.id) FROM api_keys ak")
            print("   LEFT JOIN api_key_models akm ON ak.id = akm.api_key_id")
            print("   GROUP BY ak.id;")
            print("2. Update service layer code to handle model arrays")
            print("3. Update API endpoints")
            print("4. Test key allocation logic")

        except Exception as e:
            print(f"\n{'=' * 60}")
            print("✗ Migration failed!")
            print("=" * 60)
            print(f"\nError: {e}")
            print("\nManual rollback commands:")
            print("  ALTER TABLE api_keys ADD COLUMN model VARCHAR(50);")
            print("  ALTER TABLE api_keys ADD FOREIGN KEY (model) REFERENCES models(`key`);")
            print("  DROP TABLE api_key_models;")
            raise


def downgrade():
    """降级：恢复到一对多关系"""
    with app.app_context():
        print("=" * 60)
        print("Starting rollback: many-to-many -> one-to-many")
        print("=" * 60)

        try:
            inspector = inspect(db.engine)

            # Step 1: 重新添加 model 字段
            print("\n[1/4] Adding model column back...")
            columns = [col['name'] for col in inspector.get_columns('api_keys')]
            if 'model' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        ALTER TABLE api_keys
                        ADD COLUMN model VARCHAR(50) NULL
                    """))
                    conn.commit()
                print("  ✓ Column added successfully")
            else:
                print("  - Column already exists, skipping...")

            # Step 2: 迁移数据回 model 字段（取第一个关联）
            print("\n[2/4] Migrating data back...")
            with db.engine.connect() as conn:
                # 对每个密钥，取第一个关联的模型
                conn.execute(text("""
                    UPDATE api_keys ak
                    SET model = (
                        SELECT model
                        FROM api_key_models akm
                        WHERE akm.api_key_id = ak.id
                        LIMIT 1
                    )
                    WHERE EXISTS (
                        SELECT 1 FROM api_key_models akm2
                        WHERE akm2.api_key_id = ak.id
                    )
                """))
                conn.commit()

            print("  ✓ Data migrated (WARNING: Multiple models reduced to first)")

            # Step 3: 重建外键约束
            print("\n[3/4] Recreating foreign key...")
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE api_keys
                    ADD FOREIGN KEY (model) REFERENCES models(`key`)
                """))
                conn.commit()
            print("  ✓ Foreign key recreated")

            # Step 4: 删除关联表
            print("\n[4/4] Dropping api_key_models table...")
            with db.engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS api_key_models"))
                conn.commit()
            print("  ✓ Table dropped")

            # Step 5: 重建索引
            print("\n[5/5] Recreating indexes...")
            with db.engine.connect() as conn:
                try:
                    conn.execute(text("""
                        CREATE INDEX idx_model_status ON api_keys(model, status)
                    """))
                    conn.commit()
                    print("  ✓ Index recreated")
                except Exception as e:
                    if "Duplicate key name" in str(e):
                        print("  - Index already exists, skipping...")
                    else:
                        raise

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
        print("\n⚠️  WARNING: This will rollback the many-to-many migration!")
        print("⚠️  If you have created multi-model keys, only the first model will be kept.")
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
