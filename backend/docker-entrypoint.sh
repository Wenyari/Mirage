#!/bin/bash
# Docker 容器启动脚本

set -e

echo "========================================"
echo "Mirage Backend - Docker Entrypoint"
echo "========================================"

# 1. 等待 MySQL 就绪
echo "Waiting for MySQL to be ready..."
RETRIES=60
until python -c "
from app import create_app, db
from sqlalchemy import text
try:
    app = create_app()
    with app.app_context():
        # 尝试执行一个简单的查询
        with db.engine.connect() as conn:
            conn.execute(text('SELECT 1'))
    exit(0)
except Exception as e:
    exit(1)
" >/dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
    echo "  Waiting for MySQL... ($RETRIES attempts left)"
    RETRIES=$((RETRIES-1))
    sleep 1
done

if [ $RETRIES -eq 0 ]; then
    echo "❌ Failed to connect to MySQL after 60 seconds"
    exit 1
fi
echo "✓ MySQL is ready"

# 2. 检查是否需要初始化 (使用 SQLAlchemy 检查，更稳健)
echo "Checking database state..."

# 逻辑说明：
# 只有明确检测到 'Target table exists' 也就是有表时，才跳过。
# 只有明确检测到 'No tables found' 时，才初始化。
# 如果报错，脚本会直接退出 (exit 1)，保护数据不被误删。

if [ "$SKIP_INIT_DB" = "true" ]; then
    echo "✓ Skipping database initialization (SKIP_INIT_DB=true is set)"
elif [ "$TABLES_EXIST" = "no" ]; then
    echo "Database is empty, initializing..."
    python init_db.py
    echo "✓ Database initialized successfully"
elif [ "$DB_STATUS" = "exists" ]; then
    echo "✓ Database tables found. Skipping initialization."
else
    echo "⚠️ Unknown database state: '$DB_STATUS'. Skipping initialization for safety."
fi

echo ""
echo "========================================"
echo "Starting application: $@"
echo "========================================"

exec "$@"