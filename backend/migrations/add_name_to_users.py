#!/usr/bin/env python3
"""
添加 name 字段到 users 表
用于支持用户名的设置功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db

def upgrade():
    """升级数据库"""
    app = create_app()
    with app.app_context():
        print("Adding 'name' column to users table...")

        # 使用原生SQL添加列
        sql = """
        ALTER TABLE users
        ADD COLUMN name VARCHAR(50) NULL COMMENT '用户名'
        """

        try:
            db.session.execute(db.text(sql))
            db.session.commit()
            print("✓ Successfully added 'name' column to users table")
        except Exception as e:
            print(f"✗ Failed to add column: {e}")
            db.session.rollback()
            raise

def downgrade():
    """回滚数据库"""
    app = create_app()
    with app.app_context():
        print("Removing 'name' column from users table...")

        sql = "ALTER TABLE users DROP COLUMN name"

        try:
            db.session.execute(db.text(sql))
            db.session.commit()
            print("✓ Successfully removed 'name' column from users table")
        except Exception as e:
            print(f"✗ Failed to remove column: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Add name column to users table')
    parser.add_argument('--downgrade', action='store_true', help='Downgrade the migration')

    args = parser.parse_args()

    if args.downgrade:
        print("Running downgrade...")
        downgrade()
    else:
        print("Running upgrade...")
        upgrade()

    print("Migration completed!")
