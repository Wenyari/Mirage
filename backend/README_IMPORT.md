# AI媒体资产数据导入指南

## 方法1: 在Docker容器内运行(推荐)

这是最简单且最可靠的方法,因为脚本会在Flask应用上下文中运行。

### 步骤:

1. **确保Docker容器正在运行**
```bash
cd backend
docker-compose ps
```

2. **运行导入脚本**
```bash
docker-compose exec api python scripts/import_ai_media_assets.py
```

## 方法2: 使用Flask CLI命令

也可以创建一个Flask命令来导入数据:

```bash
docker-compose exec api flask import-assets
```

## 脚本说明

### 文件位置
- 导入脚本: `backend/scripts/import_ai_media_assets.py`
- 数据文件: `backend/scripts/final_data_to_sync.json`

### 功能特性
- ✅ 自动创建数据库表(如果不存在)
- ✅ 智能去重(基于`source_id`)
- ✅ 批量提交(每100条提交一次,提高性能)
- ✅ 详细的进度提示和统计信息
- ✅ 错误处理和回滚机制

### 预期输出示例
```
📖 正在读取 scripts/final_data_to_sync.json ...
✅ JSON文件读取成功,共 5241 条数据
🔧 检查数据库表...
✅ 表结构检查完成
🔍 检查现有数据...
📊 数据库中已有 0 条记录
🚀 开始导入数据...
  ⏳ 已导入 100 条新数据...
  ⏳ 已导入 200 条新数据...
  ...

==================================================
✅ 数据导入完成!
==================================================
📊 统计信息:
  - 新导入: 5241 条
  - 已跳过: 0 条 (重复)
  - 失败: 0 条
  - 总计: 5241 条
==================================================
```

## 验证导入结果

### 1. 使用phpMyAdmin (推荐)
访问 http://localhost:8080 查看 `ai_media_assets` 表

### 2. 使用API查询
```bash
curl http://localhost:5000/api/admin/ai-media-assets?page=1&page_size=10
```

### 3. 使用MySQL命令
```bash
docker-compose exec mysql mysql -u sora_user -p"$MYSQL_PASSWORD" -e "SELECT COUNT(*) FROM sora_platform.ai_media_assets;"
```

## 常见问题

### Q: 导入脚本报错 "Working outside of application context"
**A:** 请在Docker容器内运行脚本,或确保脚本使用了 `app.app_context()`

### Q: 如何重新导入所有数据?
**A:** 先清空表,再重新导入:
```bash
docker-compose exec mysql mysql -u sora_user -p"$MYSQL_PASSWORD" -e "TRUNCATE TABLE sora_platform.ai_media_assets;"
docker-compose exec api python scripts/import_ai_media_assets.py
```

### Q: 导入速度很慢怎么办?
**A:** 脚本已经使用批量提交优化。如果仍然慢,可以调整批量大小(修改脚本中的 `100` 为更大的值如 `500`)

## 注意事项

- 导入前请确保 `final_data_to_sync.json` 文件存在于 `backend/scripts/` 目录下
- 首次导入会自动创建表结构
- 重复导入会自动跳过已存在的记录(基于`source_id`去重)
- 如果中途失败,已导入的数据会保留,可以直接重新运行脚本
