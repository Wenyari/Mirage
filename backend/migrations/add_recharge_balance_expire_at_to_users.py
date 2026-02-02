#!/usr/bin/env python3
"""
添加 recharge_balance_expire_at 字段到 users 表
用于记录充值积分的过期时间
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
        print("Adding 'recharge_balance_expire_at' column to users table...")

        # 1. 添加列
        # DEFAULT NULL: 允许为空
        sql_add_column = """
        ALTER TABLE users
        ADD COLUMN recharge_balance_expire_at DATETIME NULL COMMENT '充值积分过期时间'
        """

        try:
            # 执行添加列
            db.session.execute(text(sql_add_column))
            print("✓ Successfully added 'recharge_balance_expire_at' column")
            
            db.session.commit()
            
        except Exception as e:
            print(f"✗ Failed to add column: {e}")
            db.session.rollback()
            raise

def downgrade():
    """回滚数据库"""
    app = create_app()
    with app.app_context():
        print("Removing 'recharge_balance_expire_at' column from users table...")

        sql = "ALTER TABLE users DROP COLUMN recharge_balance_expire_at"

        try:
            db.session.execute(text(sql))
            db.session.commit()
            print("✓ Successfully removed 'recharge_balance_expire_at' column")
        except Exception as e:
            print(f"✗ Failed to remove column: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Add recharge_balance_expire_at column to users table')
    parser.add_argument('--downgrade', action='store_true', help='Downgrade the migration')

    args = parser.parse_args()

    if args.downgrade:
        print("Running downgrade...")
        downgrade()
    else:
        print("Running upgrade...")
        upgrade()

    print("Migration completed!")
