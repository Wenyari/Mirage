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

# 检查是否需要初始化数据库（判断表是否存在）
echo "Checking if database initialization is needed..."
TABLES_EXIST=$(python -c "
from app.extensions import db
from app import create_app
app = create_app()
with app.app_context():
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    print('yes' if tables else 'no')
" 2>/dev/null || echo "no")

if [ "$TABLES_EXIST" = "no" ]; then
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
