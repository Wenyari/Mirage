"""
数据库迁移脚本：为 api_key_models 表添加 api_base 字段

背景：
之前一个 ApiKey 只有一个统一的 api_base，现在需要支持每个模型有独立的 api_base。
例如：同一个密钥，视频生成模型用 /v2/videos/generations，图片生成用 /v1/images/generations

变更：
- 为 api_key_models 表添加 api_base 字段（VARCHAR(512) NOT NULL DEFAULT ''）
- 迁移现有数据：将 api_keys.api_base 复制到对应的 api_key_models 记录

使用方法：
    python migrations/add_api_base_to_api_key_models.py  # 升级
    python migrations/add_api_base_to_api_key_models.py --downgrade  # 回滚

创建时间: 2026-01-07
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.extensions import db
from app import create_app


def upgrade():
    """升级数据库：添加 api_base 字段"""
    print("=" * 60)
    print("开始迁移：为 api_key_models 添加 api_base 字段")
    print("=" * 60)

    app = create_app()
    with app.app_context():
        conn = db.engine.connect()
        trans = conn.begin()

        try:
            # Step 1: 添加 api_base 字段
            print("\n[1/3] 添加 api_base 字段到 api_key_models 表...")
            conn.execute(text("""
                ALTER TABLE api_key_models
                ADD COLUMN api_base VARCHAR(512) NOT NULL DEFAULT ''
                AFTER model
            """))
            print("✓ api_base 字段添加成功")

            # Step 2: 数据迁移 - 从 api_keys.api_base 复制到 api_key_models.api_base
            print("\n[2/3] 迁移现有数据...")

            # 查询需要迁移的记录数
            result = conn.execute(text("""
                SELECT COUNT(*) as cnt FROM api_key_models
            """))
            total_records = result.fetchone()[0]
            print(f"需要迁移 {total_records} 条关联记录")

            if total_records > 0:
                # 将 api_keys 表的 api_base 复制到对应的 api_key_models 记录
                conn.execute(text("""
                    UPDATE api_key_models akm
                    INNER JOIN api_keys ak ON akm.api_key_id = ak.id
                    SET akm.api_base = ak.api_base
                """))
                print(f"✓ 已将 api_keys.api_base 复制到所有关联记录")
            else:
                print("⚠ 没有需要迁移的数据")

            # Step 3: 验证数据
            print("\n[3/3] 验证数据完整性...")

            # 检查是否有 NULL 值（不应该有，因为设置了 DEFAULT ''）
            result = conn.execute(text("""
                SELECT COUNT(*) as cnt
                FROM api_key_models
                WHERE api_base IS NULL
            """))
            null_count = result.fetchone()[0]

            if null_count > 0:
                raise Exception(f"发现 {null_count} 条记录的 api_base 为 NULL，迁移失败")

            # 统计数据
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total,
                    COUNT(DISTINCT api_key_id) as unique_keys,
                    COUNT(DISTINCT model) as unique_models
                FROM api_key_models
            """))
            row = result.fetchone()
            print(f"✓ 数据验证通过")
            print(f"  - 总关联记录: {row[0]}")
            print(f"  - 唯一密钥数: {row[1]}")
            print(f"  - 唯一模型数: {row[2]}")

            # 提交事务
            trans.commit()

            print("\n" + "=" * 60)
            print("✓ 迁移成功完成！")
            print("=" * 60)
            print("\n后续步骤：")
            print("1. 重启应用服务")
            print("2. 测试创建/更新密钥功能")
            print("3. 验证不同模型使用不同的 api_base")

        except Exception as e:
            trans.rollback()
            print(f"\n✗ 迁移失败：{str(e)}")
            print("已回滚所有更改")
            raise


def downgrade():
    """回滚：删除 api_base 字段"""
    print("=" * 60)
    print("开始回滚：删除 api_key_models 的 api_base 字段")
    print("=" * 60)

    app = create_app()
    with app.app_context():
        conn = db.engine.connect()
        trans = conn.begin()

        try:
            print("\n删除 api_base 字段...")
            conn.execute(text("""
                ALTER TABLE api_key_models DROP COLUMN api_base
            """))

            trans.commit()

            print("\n" + "=" * 60)
            print("✓ 回滚成功！")
            print("=" * 60)
            print("\n注意：请确保代码也回滚到之前的版本")

        except Exception as e:
            trans.rollback()
            print(f"\n✗ 回滚失败：{str(e)}")
            raise


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='数据库迁移：api_key_models 添加 api_base 字段')
    parser.add_argument('--downgrade', action='store_true', help='回滚迁移')

    args = parser.parse_args()

    try:
        if args.downgrade:
            confirm = input("\n⚠ 确认要回滚迁移吗？这将删除 api_key_models.api_base 字段 (y/N): ")
            if confirm.lower() == 'y':
                downgrade()
            else:
                print("已取消回滚")
        else:
            confirm = input("\n⚠ 确认要执行迁移吗？请确保已备份数据库 (y/N): ")
            if confirm.lower() == 'y':
                upgrade()
            else:
                print("已取消迁移")

    except Exception as e:
        print(f"\n发生错误：{str(e)}")
        sys.exit(1)
