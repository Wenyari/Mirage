# 快速启动指南

## 方式一：使用 Docker (推荐)

### 1. 准备环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置必要参数
# 最少需要配置:
# - SECRET_KEY
# - JWT_SECRET_KEY
# - OPENAI_API_KEY
# - MAIL_USERNAME 和 MAIL_PASSWORD (用于发送验证码)
```

### 2. 启动服务

```bash
# 启动所有服务 (MySQL, Redis, API, Worker)
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
docker-compose logs -f worker
```

### 3. 初始化数据库

```bash
# 进入 API 容器
docker-compose exec api bash

# 运行初始化脚本
python init_db.py

# 退出容器
exit
```

### 4. 测试服务

```bash
# 健康检查
curl http://localhost:5000/health

# 查看会员等级配置
curl http://localhost:5000/api/users/membership/plans
```

管理员账号:
- 邮箱: 取自 `.env` 的 `ADMIN_EMAIL`
- 密码: 取自 `.env` 的 `ADMIN_PASSWORD`

⚠️ **项目不含硬编码默认口令。未设置 `ADMIN_PASSWORD` 时 `init_db.py` 会直接中止初始化。**

---

## 方式二：本地开发

### 1. 安装依赖

```bash
# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 准备数据库

确保本地已安装并启动:
- MySQL 8.0+
- Redis 7.0+

创建数据库:
```sql
CREATE DATABASE sora_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，修改数据库连接信息
```

### 4. 初始化数据库

```bash
# 方式 1: 使用 Flask-Migrate
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 方式 2: 直接运行初始化脚本
python init_db.py
```

### 5. 启动服务

**终端 1 - API 服务:**
```bash
python run.py
```

**终端 2 - Worker 服务:**
```bash
python worker.py
```

---

## 常见问题

### 1. 数据库连接失败

检查 `.env` 中的 `DATABASE_URI` 配置是否正确:
```
DATABASE_URI=mysql+pymysql://用户名:密码@localhost:3306/sora_platform?charset=utf8mb4
```

### 2. Redis 连接失败

检查 Redis 是否启动:
```bash
# Linux/Mac
redis-cli ping

# Windows
redis-cli.exe ping
```

### 3. 邮件发送失败

确保配置了正确的 SMTP 信息:
- Gmail: 需要开启"允许不够安全的应用"或使用应用专用密码
- QQ 邮箱: 需要开启 SMTP 服务并获取授权码

### 4. Worker 无法处理任务

检查:
1. Worker 是否正常运行
2. Redis 队列中是否有任务: `redis-cli LLEN queue:tasks:default`
3. 查看 Worker 日志是否有报错

---

## API 测试示例

### 1. 注册用户

```bash
# 发送验证码
curl -X POST http://localhost:5000/api/auth/code \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# 注册
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "code": "123456",
    "password": "password123"
  }'
```

### 2. 登录

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

保存返回的 `token` 用于后续请求。

### 3. 提交任务

```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "model": "sora-v2",
    "prompt": "A beautiful sunset over the ocean",
    "params": {"duration": 5}
  }'
```

### 4. 查询任务状态

```bash
curl http://localhost:5000/api/tasks/TASK_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 下一步

- 查看完整 API 文档: 参考 `docs/后端技术方案.md`
- 了解数据库设计: 参考 `docs/数据库表设计.md`
- 了解项目架构: 参考 `docs/后端项目结构.md`

---

## 技术支持

如遇问题，请检查:
1. 所有环境变量是否正确配置
2. MySQL 和 Redis 是否正常运行
3. 查看服务日志获取详细错误信息

Docker 日志:
```bash
docker-compose logs -f
```

本地开发日志: 查看终端输出
