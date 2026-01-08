# 实现总结：Cloudflare R2 对象存储 + 数据库改进

## 概述

本次实现包含以下三个主要功能：

1. **Cloudflare R2 对象存储接入**：支持文件上传、下载、删除
2. **Task 表结构优化**：将 `input_file_url` 改为 JSON 类型以支持多文件
3. **自动清理机制**：定时清理超过 3 天的已完成任务及其文件

---

## 1. 新增文件

### 1.1 存储服务模块
- **文件**: `app/services/storage_service.py`
- **功能**: 
  - 封装 Cloudflare R2 的上传、删除、批量操作
  - 支持预签名 URL 生成
  - 自动按用户和日期组织文件结构

### 1.2 上传 API 路由
- **文件**: `app/api/upload.py`
- **接口**:
  - `POST /api/upload/file` - 上传单个文件
  - `POST /api/upload/files` - 批量上传文件
  - `DELETE /api/upload/delete/{object_key}` - 删除文件
- **特性**:
  - 文件类型白名单验证
  - 用户权限隔离
  - 支持图片、视频、音频

### 1.3 数据库迁移脚本
- **文件**: `migrations/change_input_file_url_to_json.py`
- **功能**: 将 `tasks.input_file_url` 从 `Text` 改为 `JSON`
- **运行方式**:
  ```bash
  python migrations/change_input_file_url_to_json.py
  ```

---

## 2. 修改的文件

### 2.1 Task 模型
- **文件**: `app/models/task.py`
- **变更**: `input_file_url` 字段类型从 `db.Text` 改为 `db.JSON`
- **影响**: 现在可以存储多个输入文件 URL

### 2.2 TaskService
- **文件**: `app/services/task_service.py`
- **新增方法**: `cleanup_old_tasks(days=3)`
  - 清理超过指定天数的已完成任务
  - 同时删除关联的 R2 存储文件
  - 返回清理统计信息

### 2.3 定时任务调度器
- **文件**: `scheduler.py`
- **新增任务**: `cleanup_tasks_job()`
  - 每天凌晨 2:00 自动运行
  - 清理 3 天前的已完成任务

### 2.4 应用初始化
- **文件**: `app/__init__.py`
- **变更**: 注册 `upload_bp` 蓝图

### 2.5 环境变量示例
- **文件**: `.env.example`
- **新增配置**:
  ```env
  R2_ACCOUNT_ID=your_account_id_here
  R2_ACCESS_KEY_ID=your_access_key_id_here
  R2_SECRET_ACCESS_KEY=your_secret_access_key_here
  R2_BUCKET_NAME=mirage-storage
  R2_PUBLIC_URL=https://cdn.yourdomain.com
  ```

---

## 3. 部署步骤

### 3.1 安装依赖
```bash
pip install boto3 botocore
```

### 3.2 配置环境变量
在 `.env` 文件中添加 R2 配置（参考 `.env.example`）

### 3.3 运行数据库迁移
```bash
python migrations/change_input_file_url_to_json.py
```

### 3.4 重启应用
```bash
# 开发环境
python run.py

# 生产环境
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### 3.5 启动定时任务调度器
```bash
python scheduler.py
```

---

## 4. API 使用示例

### 4.1 上传单个文件
```bash
curl -X POST http://localhost:5000/api/upload/file \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@image.jpg" \
  -F "type=image"
```

**响应**:
```json
{
  "code": 200,
  "msg": "File uploaded successfully",
  "data": {
    "url": "https://cdn.yourdomain.com/uploads/user_1/2024/01/08/abc123-image.jpg",
    "key": "uploads/user_1/2024/01/08/abc123-image.jpg"
  }
}
```

### 4.2 批量上传
```bash
curl -X POST http://localhost:5000/api/upload/files \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files[]=@image1.jpg" \
  -F "files[]=@image2.jpg" \
  -F "type=image"
```

### 4.3 创建任务（使用多个输入文件）
```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 1,
    "prompt": "Generate video",
    "input_file_url": [
      "https://cdn.yourdomain.com/uploads/user_1/2024/01/08/abc123-image1.jpg",
      "https://cdn.yourdomain.com/uploads/user_1/2024/01/08/def456-image2.jpg"
    ]
  }'
```

---

## 5. 数据库变更

### 5.1 tasks 表
**变更前**:
```sql
input_file_url TEXT NULL
```

**变更后**:
```sql
input_file_url JSON NULL
```

**数据示例**:
```json
[
  "https://cdn.yourdomain.com/uploads/user_1/2024/01/08/abc123-image1.jpg",
  "https://cdn.yourdomain.com/uploads/user_1/2024/01/08/def456-image2.jpg"
]
```

---

## 6. 自动清理机制

### 6.1 清理规则
- **触发时间**: 每天凌晨 2:00
- **清理条件**: 
  - `finished_at` 不为空
  - `finished_at` 超过 3 天
  - `status` 为 `success`、`failed` 或 `cancelled`
- **清理内容**:
  - 任务记录（从数据库删除）
  - 输入文件（从 R2 删除）
  - 结果文件（从 R2 删除）

### 6.2 手动触发清理
```python
from app import create_app
from app.services.task_service import TaskService

app = create_app()
with app.app_context():
    result = TaskService.cleanup_old_tasks(days=3)
    print(f"Deleted {result['deleted']} tasks and {result['deleted_files']} files")
```

---

## 7. 文件存储结构

```
bucket-name/
├── uploads/
│   ├── user_1/
│   │   ├── 2024/01/08/
│   │   │   ├── abc123-image.jpg
│   │   │   └── def456-video.mp4
│   │   └── 2024/01/09/
│   ├── user_2/
│   └── ...
```

---

## 8. 支持的文件类型

- **图片**: png, jpg, jpeg, gif, webp, bmp
- **视频**: mp4, avi, mov, mkv, webm, flv
- **音频**: mp3, wav, ogg, aac, m4a

---

## 9. 安全特性

1. **用户隔离**: 用户只能访问自己上传的文件
2. **文件类型验证**: 白名单机制，只允许特定类型
3. **权限控制**: JWT 认证 + Redis 会话验证
4. **路径安全**: 使用 `secure_filename` 防止路径遍历

---

## 10. 监控和日志

### 10.1 查看上传日志
```bash
tail -f logs/app.log | grep "upload"
```

### 10.2 查看清理日志
```bash
tail -f logs/scheduler.log | grep "cleanup"
```

### 10.3 查看调度器状态
```bash
ps aux | grep scheduler.py
```

---

## 11. 故障排查

### 11.1 上传失败
- 检查 R2 配置是否正确
- 检查 API 令牌权限
- 检查网络连接

### 11.2 文件无法访问
- 检查自定义域名 DNS 配置
- 检查存储桶公开访问设置
- 检查文件 URL 格式

### 11.3 清理任务未运行
- 检查 scheduler.py 是否运行
- 检查日志中的错误信息
- 手动触发清理测试

---

## 12. 成本估算

**Cloudflare R2 定价**:
- 存储: $0.015/GB/月
- 写入: $4.50/百万次
- 读取: 免费
- 出站流量: 免费

**示例（每月）**:
- 100GB 存储 = $1.5
- 10万次上传 = $0.45
- **总计**: 约 $2/月

---

## 13. 后续优化建议

1. **图片压缩**: 上传前自动压缩图片
2. **缩略图生成**: 为图片生成多种尺寸
3. **CDN 加速**: 配置 Cloudflare CDN
4. **断点续传**: 支持大文件分片上传
5. **水印添加**: 为图片/视频添加水印
6. **病毒扫描**: 集成文件安全扫描

---

## 14. 相关文档

- [Cloudflare R2 官方文档](https://developers.cloudflare.com/r2/)
- [boto3 文档](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Flask 文件上传](https://flask.palletsprojects.com/en/2.3.x/patterns/fileuploads/)

---

## 15. 联系方式

如有问题，请联系开发团队或提交 Issue。
