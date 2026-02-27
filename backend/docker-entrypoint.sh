#!/bin/bash
# Docker 容器启动脚本
# 用于自动初始化数据库和启动应用

set -e  # 任何命令失败时退出

echo "========================================"
echo "Mirage Backend - Docker Entrypoint"
echo "========================================"

# 等待 MySQL 就绪（最多等待 60 秒）
echo "Waiting for MySQL to be ready..."
RETRIES=60
until python -c "
from app.extensions import db
from app import create_app
try:
    app = create_app()
    with app.app_context():
        db.engine.connect()
    exit(0)
except Exception:
    exit(1)
" 2>/dev/null || [ $RETRIES -eq 0 ]; do
    echo "  Waiting for MySQL... ($RETRIES attempts left)"
    RETRIES=$((RETRIES-1))
    sleep 1
done

if [ $RETRIES -eq 0 ]; then
    echo "❌ Failed to connect to MySQL after 60 seconds"
    exit 1
fi

echo "✓ MySQL is ready"
echo ""

# 检查是否需要初始化数据库（直接使用 pymysql 检查表是否存在）
echo "Checking if database initialization is needed..."
TABLES_EXIST=$(python -c "
import pymysql
import os

# 从环境变量解析数据库连接信息
db_uri = os.getenv('DATABASE_URI', '')
# mysql+pymysql://sora_user:sora_password@mysql:3306/sora_platform?charset=utf8mb4
# 简单解析（实际生产环境可以用 urllib.parse）
parts = db_uri.replace('mysql+pymysql://', '').split('@')
if len(parts) == 2:
    user_pass = parts[0].split(':')
    host_db = parts[1].split('/')
    host_port = host_db[0].split(':')
    
    user = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ''
    host = host_port[0]
    port = int(host_port[1]) if len(host_port) > 1 else 3306
    database = host_db[1].split('?')[0] if len(host_db) > 1 else ''
    
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database)
        cursor = conn.cursor()
        cursor.execute('SHOW TABLES')
        tables = cursor.fetchall()
        conn.close()
        print('yes' if tables else 'no')
    except Exception as e:
        print('no')
else:
    print('no')
" 2>/dev/null || echo "no")

if [ "$SKIP_INIT_DB" = "true" ]; then
    echo "✓ Skipping database initialization (SKIP_INIT_DB=true is set)"
elif [ "$TABLES_EXIST" = "no" ]; then
    echo "Database is empty, initializing..."
    python init_db.py
    echo "✓ Database initialized successfully"
else
    echo "✓ Database already initialized, skipping"
fi

echo ""
echo "========================================"
echo "Starting application: $@"
echo "========================================"
echo ""

# 执行传入的命令（由 docker-compose 指定）
exec "$@"
