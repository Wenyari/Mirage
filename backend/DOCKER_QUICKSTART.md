# Docker 部署快速启动

本项目已配置完整的 Docker 容器化部署方案，支持一键启动。

## 快速开始

```bash
# 1. 确保配置文件存在
cp .env.example .env

# 2. 启动所有服务（包括自动初始化数据库）
docker-compose up -d --build

# 3. 查看服务状态
docker-compose ps

# 4. 查看初始化日志
docker-compose logs api
```

## 服务清单

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| MySQL | `sora_mysql` | 3306 | 数据库 |
| Redis | `sora_redis` | 6379 | 缓存/队列 |
| API | `mirage_api` | 5000 | REST API 接口 |
| Worker | `mirage_worker` | - | 异步任务处理（100 并发） |
| Scheduler | `mirage_scheduler` | - | 定时任务调度 |

## 默认账号

**管理员账号：**
- 邮箱：`admin@example.com`
- 密码：`***REMOVED***`

**测试用户：**
- 邮箱：`demo@example.com`
- 密码：`***REMOVED***`

## 重要提示

### ✅ 自动初始化
首次启动时，数据库会**自动初始化**，无需手动操作！

初始化包含：
- 创建所有数据表
- 插入会员等级配置（T1-T5）
- 插入模型配置（sora-2, nano-banana）
- 创建管理员和测试用户
- 插入示例 API 密钥

### ⚠️ init.sql 已弃用
本项目已弃用 `init.sql`，改为使用 `docker-entrypoint.sh` + `init_db.py` 自动初始化。

**原因：** MySQL 容器启动时立即执行 init.sql，但此时表结构还未创建，导致 `Table doesn't exist` 错误。

**新方案：** API 容器启动时自动检测数据库是否为空，如果为空则运行 `init_db.py` 创建表并插入数据。

## 常用命令

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f api
docker-compose logs -f worker

# 重启服务
docker-compose restart api

# 停止所有服务
docker-compose down

# 完全重置（删除数据库）
docker-compose down -v
docker-compose up -d --build

# 进入容器调试
docker-compose exec api bash
docker-compose exec mysql mysql -u sora_user -psora_password sora_platform
```

## 测试 API

```bash
# 健康检查
curl http://localhost:5000/health

# 登录测试
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"***REMOVED***"}'
```

## 详细文档

完整的部署方案请参考：[DOCKER部署方案.md](./DOCKER部署方案.md)

包含以下内容：
- 从 Conda 迁移到 Docker 的完整指南
- 环境变量配置详解
- 生产环境部署流程
- 日常运维和故障排查
- 常见问题解答

## 文件说明

| 文件 | 说明 |
|------|------|
| `docker-compose.yml` | 服务编排配置（5 个服务） |
| `Dockerfile` | Python 应用镜像构建 |
| `docker-entrypoint.sh` | 容器启动脚本（自动初始化） |
| `init_db.py` | 数据库初始化脚本 |
| `.dockerignore` | 忽略不必要的文件 |
| `.env.example` | 环境变量模板 |
| ~~`init.sql`~~ | **已弃用** |

---

**需要帮助？** 请查看 [DOCKER部署方案.md](./DOCKER部署方案.md) 或提交 Issue。
