#!/usr/bin/env python3
"""
添加 consecutive_days 字段到 users 表
用于修复签到逻辑，持久化存储连续签到天数
"""

import sys
import os
# 确保项目根目录在 sys.path 中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from sqlalchemy import text

def upgrade():
    """升级数据库"""
    app = create_app()
    with app.app_context():
        print("Adding 'consecutive_days' column to users table...")

        # 1. 添加列
        # DEFAULT 0: 必须设置默认值，否则旧数据该字段为 NULL 可能导致逻辑报错
        sql_add_column = """
        ALTER TABLE users
        ADD COLUMN consecutive_days INT NOT NULL DEFAULT 0 COMMENT '连续签到天数'
        """

        # 2. (可选) 数据迁移：尝试恢复活跃用户的连续天数
        # 逻辑：如果用户在最近 48 小时内签到过，暂时用 (total_checkin_days % 7) 作为连续天数
        # 这样可以避免上线后所有活跃用户都被重置为第 1 天
        sql_migrate_data = """
        UPDATE users 
        SET consecutive_days = CASE 
            WHEN total_checkin_days % 7 = 0 THEN 7 
            ELSE total_checkin_days % 7 
        END
        WHERE last_checkin_at >= DATE_SUB(NOW(), INTERVAL 2 DAY)
        """

        try:
            # 执行添加列
            db.session.execute(text(sql_add_column))
            print("✓ Successfully added 'consecutive_days' column")
            
            # 执行数据初始化
            print("Initializing data for active users...")
            result = db.session.execute(text(sql_migrate_data))
            print(f"✓ Updated consecutive_days for {result.rowcount} active users")
            
            db.session.commit()
            
        except Exception as e:
            print(f"✗ Failed to add column or migrate data: {e}")
            db.session.rollback()
            raise

def downgrade():
    """回滚数据库"""
    app = create_app()
    with app.app_context():
        print("Removing 'consecutive_days' column from users table...")

        sql = "ALTER TABLE users DROP COLUMN consecutive_days"

        try:
            db.session.execute(text(sql))
            db.session.commit()
            print("✓ Successfully removed 'consecutive_days' column")
        except Exception as e:
            print(f"✗ Failed to remove column: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Add consecutive_days column to users table')
    parser.add_argument('--downgrade', action='store_true', help='Downgrade the migration')

    args = parser.parse_args()

    if args.downgrade:
        print("Running downgrade...")
        downgrade()
    else:
        print("Running upgrade...")
        upgrade()

    print("Migration completed!")