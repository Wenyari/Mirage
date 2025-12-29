# AIGC 文生视频平台 - 后端项目

基于 Flask + MySQL + Redis 的 AIGC 视频生成平台后端服务。

## 技术栈

- **框架**: Flask 3.0
- **数据库**: MySQL 8.0
- **缓存/队列**: Redis 7.0
- **异步任务**: RQ (Redis Queue)
- **认证**: JWT
- **ORM**: SQLAlchemy

## 项目结构

```
backend/
├── app/                    # 核心代码
│   ├── api/               # API 路由层
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑层
│   ├── tasks/             # 异步任务
│   └── utils/             # 工具类
├── docs/                   # 文档
├── migrations/            # 数据库迁移
├── run.py                 # API 服务入口
├── worker.py              # Worker 入口
└── docker-compose.yml     # Docker 编排
```

## 快速开始

### 1. 环境准备

复制环境变量配置文件:
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置数据库、Redis、OpenAI API Key 等。

### 2. 使用 Docker 启动 (推荐)

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

服务将运行在:
- API: http://localhost:5000
- MySQL: localhost:3306
- Redis: localhost:6379

### 3. 本地开发

#### 安装依赖
```bash
pip install -r requirements.txt
```

#### 初始化数据库
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

#### 启动服务

终端 1 - API 服务:
```bash
python run.py
```

终端 2 - Worker 服务:
```bash
python worker.py
```

## API 文档

### 鉴权相关
- `POST /api/auth/code` - 发送验证码
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 任务相关
- `POST /api/tasks` - 提交生成任务
- `GET /api/tasks/{id}` - 查询任务状态
- `GET /api/tasks` - 获取任务历史

### 钱包相关
- `POST /api/wallet/redeem` - CDK 兑换
- `GET /api/wallet/transactions` - 查看流水
- `GET /api/wallet/balance` - 查看余额

### 管理员相关
- `POST /api/admin/cdk/generate` - 生成 CDK
- `PATCH /api/admin/users/{id}/ban` - 封禁用户
- `GET /api/admin/stats` - 数据统计

## 核心功能

### 1. 单点登录互斥 (顶号机制)
每次登录时，将 JWT Token 存入 Redis。后续请求验证 Token 与 Redis 中的是否一致，实现单设备登录。

### 2. 并发控制 (T1-T5 等级)
根据用户会员等级限制并发任务数，在任务提交时检查运行中的任务数量。

### 3. 优先级队列
- T4-T5 用户: `high_priority` 队列
- T1-T3 用户: `default` 队列

Worker 优先处理高优先级队列。

### 4. 预扣费 + 失败退款
任务提交时预扣费，失败时自动退款，保障资金安全。

### 5. CDK 兑换 (悲观锁)
使用数据库 `FOR UPDATE` 锁防止并发兑换同一个 CDK。

## 测试

本项目包含完整的测试套件，覆盖模型层、服务层、API 层和工具类。

### 安装测试依赖

```bash
pip install -r requirements-test.txt
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行并生成覆盖率报告
pytest --cov=app --cov-report=html

# 使用脚本运行
./run_tests.sh coverage  # Linux/Mac
run_tests.bat coverage   # Windows
```

### 测试分类

- **单元测试**: `pytest -m unit`
- **API 测试**: `pytest -m api`
- **集成测试**: `pytest -m integration`

### 测试覆盖

- 模型层: 用户、任务、钱包相关模型
- 服务层: 鉴权、任务、支付服务
- API 层: 所有 API 端点
- 工具类: 装饰器、Redis 工具

详细测试文档: [TESTING.md](TESTING.md)

## 开发指南

### 添加新的 API 接口

1. 在 `app/api/` 下创建或编辑蓝图文件
2. 在 `app/services/` 下实现业务逻辑
3. 如需数据库操作，使用 `app/models/` 中的模型
4. 为新接口编写测试

### 添加新的异步任务

1. 在 `app/tasks/` 下创建任务函数
2. 在需要的地方使用 RQ 入队:
```python
from rq import Queue
q = Queue('default', connection=redis_client)
q.enqueue(your_task_function, args)
```
3. 为任务编写单元测试

## 部署

### 生产环境建议

1. 使用 Gunicorn 运行 API:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

2. 使用 Nginx 反向代理

3. 配置 SSL 证书

4. 使用 Supervisor 管理进程

## 许可证

MIT License
