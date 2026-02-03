#!/usr/bin/env python3
"""
添加 valid_days 字段到 cdk 表
用于支持积分时效策略
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
        print("Adding 'valid_days' column to cdk table...")

        # 使用原生SQL添加列
        sql = """
        ALTER TABLE cdk
        ADD COLUMN valid_days INTEGER NULL COMMENT '积分有效期(天)'
        """

        try:
            db.session.execute(db.text(sql))
            db.session.commit()
            print("✓ Successfully added 'valid_days' column to cdk table")
        except Exception as e:
            print(f"✗ Failed to add column: {e}")
            db.session.rollback()
            raise

def downgrade():
    """回滚数据库"""
    app = create_app()
    with app.app_context():
        print("Removing 'valid_days' column from cdk table...")

        sql = "ALTER TABLE cdk DROP COLUMN valid_days"

        try:
            db.session.execute(db.text(sql))
            db.session.commit()
            print("✓ Successfully removed 'valid_days' column from cdk table")
        except Exception as e:
            print(f"✗ Failed to remove column: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Add valid_days column to cdk table')
    parser.add_argument('--downgrade', action='store_true', help='Downgrade the migration')

    args = parser.parse_args()

    if args.downgrade:
        print("Running downgrade...")
        downgrade()
    else:
        print("Running upgrade...")
        upgrade()
