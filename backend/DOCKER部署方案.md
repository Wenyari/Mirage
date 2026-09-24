# Mirage 后端 Docker 容器化部署方案

本文档提供从 Conda 开发环境迁移到 Docker 容器化部署的完整方案。

---

## 项目架构说明

本项目是一个基于 Flask 的 AIGC 服务平台，包含以下核心服务：

1. **API 服务** (`run.py`) - Flask REST API，提供 HTTP 接口
2. **异步任务 Worker** (`worker_gevent.py`) - 基于 Gevent 的高并发任务处理器
3. **定时任务调度器** (`scheduler.py`) - 后台维护和定时任务

**数据层依赖：**
- MySQL 8.0 - 主数据库
- Redis 7.x - 队列和缓存

---

## 第一步：完善依赖清单

### 1.1 检查 requirements.txt

确保 `requirements.txt` 包含所有依赖，特别是 **gevent** 相关包（worker_gevent.py 需要）：

```bash
# 在你的 sora_env 环境中执行
conda activate sora_env
pip freeze > requirements.txt
```

### 1.2 必需依赖检查清单

请确认以下关键包在 `requirements.txt` 中：

```txt
# Web 框架
Flask==3.0.0
gunicorn==21.2.0

# 异步协程 (关键！worker_gevent.py 依赖)
gevent==23.9.1

# 数据库
PyMySQL==1.1.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5

# 缓存/队列
redis==5.0.1

# 定时任务
schedule==1.2.0

# 其他核心依赖
Flask-JWT-Extended==4.6.0
Flask-CORS==4.0.0
python-dotenv==1.0.0
requests==2.31.0
boto3==1.34.0
```

如果缺少 gevent，手动添加：
```bash
pip install gevent==23.9.1
pip freeze > requirements.txt
```

---

## 第二步：Dockerfile 说明

项目根目录已有 `Dockerfile`，内容如下：

```dockerfile
# Python 3.11 基础镜像
FROM python:3.11-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（使用清华源加速）
RUN pip install --upgrade pip && \
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 5000

# 默认启动命令 (由 docker-compose 覆盖)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

> **注意**: 如果现有 Dockerfile 缺少 `curl`（healthcheck 需要），请在 `RUN apt-get install` 行中添加。

---

## 第三步：编写 docker-compose.yml

在项目根目录创建/更新 `docker-compose.yml`，配置完整的服务编排：

```yaml
version: '3.8'

services:
  # ==================== 数据层 ====================

  # MySQL 数据库
  mysql:
    image: mysql:8.0
    container_name: mirage_mysql
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: sora_platform
      MYSQL_USER: sora_user
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    ports:
      - "3306:3306"  # 开发环境映射端口，方便 Navicat 连接
    volumes:
      - mysql_data:/var/lib/mysql
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis 缓存/队列
  redis:
    image: redis:7-alpine
    container_name: mirage_redis
    restart: always
    ports:
      - "6379:6379"  # 开发环境映射端口
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ==================== 应用层 ====================

  # API 接口服务
  api:
    build: .
    container_name: mirage_api
    restart: always
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URI=mysql+pymysql://sora_user:${MYSQL_PASSWORD}@mysql:3306/sora_platform?charset=utf8mb4
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: gunicorn -w 4 -b 0.0.0.0:5000 run:app
    volumes:
      - .:/app  # 开发时挂载代码，便于热更新
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Gevent 异步任务 Worker
  worker:
    build: .
    container_name: mirage_worker
    restart: always
    environment:
      - FLASK_ENV=production
      - DATABASE_URI=mysql+pymysql://sora_user:${MYSQL_PASSWORD}@mysql:3306/sora_platform?charset=utf8mb4
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: python worker_gevent.py --workers 100
    volumes:
      - .:/app

  # 定时任务调度器
  scheduler:
    build: .
    container_name: mirage_scheduler
    restart: always
    environment:
      - FLASK_ENV=production
      - DATABASE_URI=mysql+pymysql://sora_user:${MYSQL_PASSWORD}@mysql:3306/sora_platform?charset=utf8mb4
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: python scheduler.py
    volumes:
      - .:/app

volumes:
  mysql_data:
    driver: local
  redis_data:
    driver: local
```

### 配置说明

| 服务 | 端口 | 作用 | 启动命令 |
|------|------|------|----------|
| `mysql` | 3306 | 主数据库 | MySQL 8.0 官方镜像 |
| `redis` | 6379 | 队列和缓存 | Redis 7 Alpine |
| `api` | 5000 | REST API 接口 | `gunicorn -w 4 -b 0.0.0.0:5000 run:app` |
| `worker` | - | 异步任务处理 | `python worker_gevent.py --workers 100` |
| `scheduler` | - | 定时任务调度 | `python scheduler.py` |

---

## 第四步：修改代码配置（关键）

### 4.1 理解 Docker 网络

在 Docker Compose 中：
- ❌ `localhost` / `127.0.0.1` - 指向容器自己，无法访问其他容器
- ✅ 服务名（如 `mysql`, `redis`）- Docker DNS 自动解析为容器 IP

### 4.2 环境变量覆盖机制

本项目使用**智能配置切换**，无需修改代码即可在不同环境运行：

```python
# app/config.py
SQLALCHEMY_DATABASE_URI = os.getenv(
    'DATABASE_URI',  # 优先读取环境变量
    'mysql+pymysql://root:admin@localhost:3306/sora_platform'  # 找不到则使用默认值
)
```

**工作流程：**

| 环境 | DATABASE_URI 环境变量 | 实际连接 | 说明 |
|------|----------------------|---------|------|
| 本地开发 | 未设置 | `root:admin@localhost:3306` | 连接本机 MySQL |
| Docker | `sora_user:$MYSQL_PASSWORD@mysql:3306` | `sora_user:$MYSQL_PASSWORD@mysql:3306` | 连接 Docker 容器 |

**为什么不会冲突？**

1. **不同的主机名：**
   - 本地：`localhost` → 你的物理机 MySQL（端口 3306）
   - Docker：`mysql` → Docker 网络中的 MySQL 容器

2. **不同的用户凭证：**
   - 本地：`root / admin`（你本地 MySQL 的现有用户）
   - Docker：`sora_user / $MYSQL_PASSWORD`（Docker 启动时自动创建）

3. **环境隔离：**
   - 本地开发不启动 Docker → 使用默认配置
   - Docker 运行 → `docker-compose.yml` 自动注入环境变量

### 4.3 确认配置文件

检查 `app/config.py`，确保数据库和 Redis 连接使用环境变量：

```python
# app/config.py
import os
from dotenv import load_dotenv

class Config:
    # 数据库配置 - 优先使用环境变量，开发时回退到 localhost
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI',
        'mysql+pymysql://root:admin@localhost:3306/sora_platform?charset=utf8mb4'
    )

    # Redis 配置 - 同样支持环境变量
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
```

**工作原理：**
- 本地开发：`DATABASE_URI` 未设置，使用 `localhost`
- Docker 部署：环境变量指向 `mysql:3306` 和 `redis:6379`

### 4.3 创建 .env 文件

在项目根目录创建 `.env`（不要提交到 Git）：

```env
# Flask 配置
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-me
JWT_SECRET_KEY=your-jwt-secret-key-change-me

# 数据库配置 (Docker Compose 会覆盖)
MYSQL_ROOT_PASSWORD=your-mysql-root-password
MYSQL_PASSWORD=your-mysql-password

# 第三方 API
OPENAI_API_KEY=sk-xxxxx
SORA_API_BASE_URL=https://ai.t8star.cn

# 对象存储 (Cloudflare R2)
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=your-bucket
R2_PUBLIC_URL=https://files.yourdomain.com

# 邮件配置
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

---

## 第五步：本地部署与测试

### 5.1 构建并启动所有服务

```bash
# 在项目根目录执行
docker-compose up -d --build
```

这个命令会：
1. 构建 Python 应用镜像（首次较慢，约 2-5 分钟）
2. 下载 MySQL 和 Redis 镜像
3. 启动 5 个容器：mysql, redis, api, worker, scheduler
4. **自动初始化数据库**（首次启动时）

### 5.2 数据库自动初始化机制

**重要变更：** 本项目已弃用 `init.sql`，改为使用 `docker-entrypoint.sh` + `init_db.py` 自动初始化。

**为什么？**
```
❌ 旧方案：使用 init.sql
   问题：MySQL 启动时立即执行 init.sql
        但此时表结构还未创建（需要 Flask-Migrate）
        导致 "Table doesn't exist" 错误

✅ 新方案：容器启动时自动检测并初始化
   流程：1. MySQL 启动并完成健康检查
        2. API 容器启动，执行 docker-entrypoint.sh
        3. 脚本检查数据库是否为空
        4. 如果为空，自动运行 init_db.py（创建表+插入数据）
        5. 启动应用服务
```

**初始化内容（由 init_db.py 完成）：**
- 创建所有数据库表（users, tasks, models, api_keys 等）
- 插入会员等级配置（T1-T5）
- 插入模型配置（sora-2, nano-banana）
- 创建管理员账号（取自 ADMIN_EMAIL / ADMIN_PASSWORD）
- 创建测试用户（取自 DEMO_USER_EMAIL / DEMO_USER_PASSWORD）
- 插入示例 API 密钥

**查看初始化日志：**
```bash
# 查看 API 容器的启动日志
docker-compose logs api

# 应该看到类似输出：
# ✓ MySQL is ready
# Database is empty, initializing...
# ✓ Database tables created successfully
# ✓ Membership configs initialized
# ✓ Admin user created
```

### 5.3 查看服务状态

```bash
# 查看运行中的容器
docker-compose ps

# 查看日志（实时）
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f scheduler
```

### 5.4 验证服务

**注意：** 首次启动时，数据库会自动初始化，无需手动操作！如果需要重新初始化，请参考下方的"手动重新初始化"部分。

```bash
# 测试 API
curl http://localhost:5000/health

# 进入 MySQL 数据库（会提示输入密码取自 .env 的 MYSQL_PASSWORD）
docker-compose exec mysql mysql -u sora_user -p sora_platform

# 或者直接指定密码（开发环境快捷方式，注意 -p 和密码之间无空格）
docker-compose exec mysql mysql -u sora_user -p"$MYSQL_PASSWORD" sora_platform

# 测试 Redis
docker-compose exec redis redis-cli ping
```

### 5.5 常用运维命令

```bash
# 重启某个服务
docker-compose restart api

# 停止所有服务
docker-compose down

# 停止并删除数据卷（危险！会清空数据库）
docker-compose down -v

# 查看资源占用
docker stats

# 进入容器调试
docker-compose exec api bash
docker-compose exec worker bash

# 手动重新初始化数据库（危险！会清空所有数据）
docker-compose exec api python init_db.py

# 如果需要完全重置（包括删除数据卷）
docker-compose down -v  # 删除所有容器和数据卷
docker-compose up -d --build  # 重新启动，自动初始化
```

**⚠️ 重新初始化警告：**
- `init_db.py` 会执行 `db.drop_all()` 删除所有表和数据
- 生产环境请谨慎使用！
- 建议先备份数据：`docker-compose exec mysql mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" sora_platform > backup.sql`

---

## 第六步：生产环境部署

### 6.1 方案选择

针对国内网络环境，推荐**离线打包部署**（最快最稳）：

#### 方式一：Docker Hub（需要外网）
```bash
# 本地打标签并推送
docker tag mirage_backend:latest your-dockerhub-username/mirage:v1.0
docker push your-dockerhub-username/mirage:v1.0

# 服务器拉取
docker pull your-dockerhub-username/mirage:v1.0
```

#### 方式二：离线打包（推荐）

**在本地 Windows 机器：**
```powershell
# 1. 构建镜像
docker-compose build

# 将整个backend目录打包（包含Dockerfile和docker-compose.yml）
tar -czf mirage_backend_v1.0.tar.gz .

# 3. 上传到服务器（使用 scp 或 FTP 工具）
scp mirage_backend_v1.0.tar root@your-server-ip:/data/
```

**在服务器上：**
```bash
# 1. 加载镜像
docker load -i /data/mirage_backend_v1.0.tar

# 2. 验证
docker images | grep mirage

# 3. 启动服务
cd /path/to/project
docker-compose up -d
```

### 6.2 生产环境优化

#### 修改 docker-compose.yml

```yaml
# 生产环境配置调整
services:
  api:
    # 使用镜像而非 build
    image: mirage_backend:v1.0
    restart: always
    # 不挂载代码卷（提高安全性）
    # volumes:
    #   - .:/app  # 注释掉

  worker:
    image: mirage_backend:v1.0
    # 根据服务器性能调整并发数
    command: python worker_gevent.py --workers 200

  scheduler:
    image: mirage_backend:v1.0
```

#### Nginx 反向代理

```nginx
# /etc/nginx/sites-available/mirage
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/mirage /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6.3 HTTPS 证书配置

```bash
# 使用 Certbot 自动申请证书
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

---

## 第七步：日常运维

### 7.1 监控和日志

```bash
# 实时查看所有服务日志
docker-compose logs -f --tail=100

# 只看错误日志
docker-compose logs | grep ERROR

# 导出日志到文件
docker-compose logs --since 24h > logs_24h.txt
```

### 7.2 数据备份

```bash
# 备份 MySQL 数据库（会提示输入密码取自 .env 的 MYSQL_ROOT_PASSWORD）
docker-compose exec mysql mysqldump -u root -p sora_platform > backup_$(date +%Y%m%d).sql

# 或者直接指定密码
docker-compose exec mysql mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" sora_platform > backup_$(date +%Y%m%d).sql

# 备份 Redis 数据
docker-compose exec redis redis-cli SAVE
cp data/redis/dump.rdb backup_redis_$(date +%Y%m%d).rdb
```

### 7.3 更新部署流程

```bash
# 1. 本地开发完成后构建新版本
docker build -t mirage_backend:v1.1 .

# 2. 打包上传
docker save -o mirage_v1.1.tar mirage_backend:v1.1
scp mirage_v1.1.tar root@server:/data/

# 3. 服务器加载并重启
docker load -i /data/mirage_v1.1.tar
cd /path/to/project

# 修改 docker-compose.yml 中的镜像版本
# image: mirage_backend:v1.1

docker-compose up -d --no-deps --build api worker scheduler
```

### 7.4 故障排查

#### Worker 不消费任务
```bash
# 检查 Redis 连接
docker-compose exec worker python -c "from app.utils.redis_cli import get_redis; print(get_redis().ping())"

# 查看队列长度
docker-compose exec redis redis-cli LLEN sora:queue:runnable
```

#### API 响应慢
```bash
# 查看容器资源占用
docker stats

# 增加 Gunicorn worker 数量
docker-compose exec api gunicorn -w 8 -b 0.0.0.0:5000 run:app
```

#### 数据库连接失败
```bash
# 检查 MySQL 健康状态
docker-compose exec mysql mysqladmin ping

# 查看连接数（会提示输入密码取自 .env 的 MYSQL_ROOT_PASSWORD）
docker-compose exec mysql mysql -u root -p -e "SHOW PROCESSLIST;"

# 或者直接指定密码
docker-compose exec mysql mysql -u root -p"$MYSQL_ROOT_PASSWORD" -e "SHOW PROCESSLIST;"
```

---

## 常见问题（FAQ）

### Q1: 如何切换开发/生产环境？
修改 `.env` 文件中的 `FLASK_ENV`：
- 开发：`FLASK_ENV=development`
- 生产：`FLASK_ENV=production`

### Q2: 端口冲突怎么办？
修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "8000:5000"  # 宿主机 8000 映射到容器 5000
```

### Q3: 如何查看 Worker 并发数？
```bash
docker-compose logs worker | grep "Max Concurrency"
```

### Q4: 数据库字符集问题
确保 MySQL 启动命令包含：
```yaml
command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
```

### Q5: Redis 持久化配置
```yaml
command: redis-server --appendonly yes --save 60 1000
```
- `--appendonly yes`: 启用 AOF 持久化
- `--save 60 1000`: 60 秒内有 1000 次写入则触发 RDB 快照

### Q6: 为什么弃用 init.sql？
**问题背景：**
```
错误：ERROR 1146 (42S02) at line 7: Table 'sora_platform.membership_configs' doesn't exist
原因：MySQL 启动时立即执行 init.sql，但表结构由 Flask-Migrate 管理，此时还未创建
```

**解决方案：**
- ✅ 使用 `docker-entrypoint.sh` + `init_db.py` 自动初始化
- ✅ 容器启动时检测数据库是否为空，如果为空则自动运行 `init_db.py`
- ✅ `init_db.py` 同时处理表结构创建和数据插入

**如果你有自定义的 init.sql：**
1. 将 SQL 语句转换为 Python 代码，添加到 `init_db.py` 中
2. 或者在 API 容器启动后手动执行：
   ```bash
   docker-compose exec mysql mysql -u sora_user -p"$MYSQL_PASSWORD" sora_platform < your_custom.sql
   ```

### Q7: 如何查看数据库初始化日志？
```bash
# 查看 API 容器的完整启动日志
docker-compose logs api

# 实时跟踪
docker-compose logs -f api
```

### Q8: Worker 报错 "Working outside of application context"
**问题描述：**
```
RuntimeError: Working outside of application context.
Traceback:
  File "/app/worker_gevent.py", line 68, in worker_wrapper
    process_task(payload)
  File "/app/worker.py", line 74, in query_sql
    with db.engine.connect() as conn:
```

**原因分析：**
- Gevent 协程池中的子协程不会自动继承父协程的应用上下文
- Flask 的数据库操作（`db.engine.connect()`）需要在应用上下文中执行

**解决方案：**
本项目已在 `worker_gevent.py` 的 `worker_wrapper` 方法中添加了 `with app.app_context():`，确保每个协程都有独立的应用上下文。

**如何验证修复：**
```bash
# 重启 Worker 容器
docker-compose restart worker

# 查看日志
docker-compose logs -f worker

# 应该看到正常的任务处理日志，不再有 RuntimeError
```

**详细技术说明：** 请参考 `docs/flask-app-context-fix.md`

---

## 总结

### 核心改变
1. ❌ 放弃 Conda 虚拟环境 → ✅ Docker 容器隔离
2. ❌ 本地安装 MySQL/Redis → ✅ Docker Compose 编排
3. ❌ 手动启动 3 个进程 → ✅ 一键启动 5 个容器

### 部署检查清单
- [ ] `requirements.txt` 包含 `gevent`
- [ ] `Dockerfile` 安装了 `curl`（healthcheck 需要）
- [ ] `.env` 文件配置完整（不提交到 Git）
- [ ] `app/config.py` 支持环境变量
- [ ] `docker-compose.yml` 配置 3 个应用服务
- [ ] 生产环境使用 Nginx 反向代理
- [ ] 配置 HTTPS 证书
- [ ] 设置数据库定期备份

### 最佳实践
1. 开发环境保留 `volumes` 挂载，便于热更新
2. 生产环境移除 `volumes`，使用固定版本镜像
3. 敏感信息使用环境变量，不写死在代码中
4. 定期备份 `mysql_data` 和 `redis_data` 卷
5. 使用 `docker-compose logs` 监控运行状态

---

**需要帮助？** 联系运维团队或查看 [Docker 官方文档](https://docs.docker.com/compose/)
