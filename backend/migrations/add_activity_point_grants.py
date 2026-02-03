#!/usr/bin/env python3
"""
添加 activity_point_grants 表
用于实现活动积分的账本化管理（分笔记录、独立过期）
并迁移现有用户的 activity_balance 到 legacy 账本
"""

import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from sqlalchemy import text

def upgrade():
    """升级数据库"""
    app = create_app()
    with app.app_context():
        print("Creating 'activity_point_grants' table...")

        # 1. 创建表
        # id: 主键
        # user_id: 用户ID
        # initial_amount: 初始金额
        # current_balance: 当前剩余金额
        # expire_at: 过期时间 (NULL表示不过期)
        # source: 来源 (legacy, checkin, activity:CODE)
        # created_at: 创建时间
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS activity_point_grants (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            user_id INTEGER NOT NULL,
            initial_amount DECIMAL(10, 2) NOT NULL,
            current_balance DECIMAL(10, 2) NOT NULL,
            expire_at DATETIME NULL,
            source VARCHAR(100) NOT NULL,
            created_at DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        
        # 创建索引
        create_index_sql = """
        CREATE INDEX idx_grants_user_expire 
        ON activity_point_grants (user_id, expire_at)
        """

        try:
            db.session.execute(text(create_table_sql))
            print("✓ Created table 'activity_point_grants' (if not exists)")
            
            try:
                db.session.execute(text(create_index_sql))
                print("✓ Created index 'idx_grants_user_expire'")
            except Exception as e:
                # 忽略索引已存在的错误 (MySQL Error 1061: Duplicate key name)
                if "1061" in str(e):
                    print("✓ Index 'idx_grants_user_expire' already exists")
                else:
                    raise e
            
            # 2. 迁移现有数据
            print("Migrating existing activity balances...")
            
            # 查询所有有活动积分的用户
            users_sql = "SELECT id, activity_balance FROM users WHERE activity_balance > 0"
            users = db.session.execute(text(users_sql)).fetchall()
            
            migrated_count = 0
            now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime('%Y-%m-%d %H:%M:%S')
            
            for user in users:
                user_id = user[0]
                balance = user[1]
                
                # 插入 legacy 记录
                insert_sql = """
                INSERT INTO activity_point_grants 
                (user_id, initial_amount, current_balance, expire_at, source, created_at)
                VALUES (:uid, :amt, :amt, NULL, 'legacy', :now)
                """
                
                db.session.execute(text(insert_sql), {
                    "uid": user_id, 
                    "amt": balance,
                    "now": now
                })
                migrated_count += 1
                
            db.session.commit()
            print(f"✓ Migrated {migrated_count} users' balances to legacy grants")
            
        except Exception as e:
            print(f"✗ Failed to migration: {e}")
            db.session.rollback()
            raise

def downgrade():
    """回滚数据库"""
    app = create_app()
    with app.app_context():
        print("Dropping 'activity_point_grants' table...")

        sql = "DROP TABLE IF EXISTS activity_point_grants"

        try:
            db.session.execute(text(sql))
            db.session.commit()
            print("✓ Successfully dropped table")
        except Exception as e:
            print(f"✗ Failed to drop table: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Add activity_point_grants table')
    parser.add_argument('--downgrade', action='store_true', help='Downgrade the migration')

    args = parser.parse_args()

    if args.downgrade:
        print("Running downgrade...")
        downgrade()
    else:
        print("Running upgrade...")
        upgrade()
