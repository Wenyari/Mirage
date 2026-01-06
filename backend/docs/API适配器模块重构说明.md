# API 适配器模块重构说明

## 📁 新的模块结构

```
app/adapters/
├── __init__.py                    # 模块导出
├── base_adapter.py                # ApiAdapter 基类
├── adapter_factory.py             # get_adapter() 工厂函数
├── t8star_video_adapter.py        # T8StarVideoGenerationAdapter (视频生成)
├── t8star_image_adapter.py        # T8StarImageGenerationAdapter (图片生成)
├── t8star_image_edit_adapter.py   # T8StarImageEditAdapter (图片编辑)
├── default_adapter.py             # DefaultAdapter (通用适配器)
└── api_adapter.py.backup          # 旧文件备份（可删除）
```

## 🔄 重命名说明

| 旧名称 | 新名称 | 说明 |
|-------|-------|------|
| `T8StarAdapter` | `T8StarVideoGenerationAdapter` | 避免混淆，明确表示视频生成 |

**向后兼容性**: `__init__.py` 中保留了 `T8StarAdapter` 作为别名：
```python
T8StarAdapter = T8StarVideoGenerationAdapter
```

## 📝 各文件说明

### 1. base_adapter.py
**职责**: 定义 ApiAdapter 基类，所有适配器的抽象接口

**关键方法**:
- `build_submit_payload()` - 构造请求体
- `is_async_task()` - 判断同步/异步
- `get_polling_config()` - 轮询配置
- `parse_sync_response()` - 解析同步响应
- `parse_submit_response()` - 解析提交响应
- `parse_status_response()` - 解析状态响应

### 2. t8star_video_adapter.py
**职责**: T8Star 视频生成适配器（异步）

**API**: `https://ai.t8star.cn/v2/videos/generations`

**特点**:
- 异步任务，需要轮询
- 10分钟超时，3秒轮询间隔
- 包含 `_parse_progress()` 静态方法（被其他适配器复用）

### 3. t8star_image_adapter.py
**职责**: T8Star 图片生成适配器（同步）

**API**: `https://ai.t8star.cn/v1/images/generations`

**特点**:
- 同步任务，直接返回结果
- 继承自 `T8StarVideoGenerationAdapter` 以复用状态解析逻辑
- 支持 `url` 和 `b64_json` 两种响应格式

### 4. t8star_image_edit_adapter.py
**职责**: T8Star 图片编辑适配器（同步）

**API**: `https://ai.t8star.cn/v1/images/edits`

**特点**:
- 同步任务，直接返回结果
- 继承自 `T8StarVideoGenerationAdapter`
- 支持 image, mask, size, n 等参数

### 5. default_adapter.py
**职责**: 默认通用适配器

**适用**: OpenAI 风格的标准 API

**特点**:
- 默认为异步任务
- 尝试多种可能的字段名（task_id, id, taskId, request_id）
- 兼容多种响应格式

### 6. adapter_factory.py
**职责**: 适配器工厂，根据 API URL 返回对应适配器

**路由规则**:
```python
https://ai.t8star.cn/v1/images/generations → T8StarImageGenerationAdapter
https://ai.t8star.cn/v1/images/edits       → T8StarImageEditAdapter
https://ai.t8star.cn/v2/videos/generations → T8StarVideoGenerationAdapter
其他 URL                                    → DefaultAdapter
```

## 🔧 使用方法

### 导入适配器
```python
from app.adapters import (
    get_adapter,
    T8StarVideoGenerationAdapter,
    T8StarImageGenerationAdapter,
    T8StarImageEditAdapter,
    DefaultAdapter
)
```

### 使用工厂函数（推荐）
```python
# Worker 中使用
adapter = get_adapter('https://ai.t8star.cn/v2/videos/generations')
# 返回: T8StarVideoGenerationAdapter 实例

adapter = get_adapter('https://ai.t8star.cn/v1/images/generations')
# 返回: T8StarImageGenerationAdapter 实例
```

### 直接实例化
```python
# 如果需要直接使用特定适配器
video_adapter = T8StarVideoGenerationAdapter('https://ai.t8star.cn/v2/videos/generations')
image_adapter = T8StarImageGenerationAdapter('https://ai.t8star.cn/v1/images/generations')
```

## ✅ 优势

1. **职责清晰**: 每个适配器一个文件，易于维护
2. **易于扩展**: 添加新适配器只需创建新文件
3. **代码复用**: 通过继承复用通用逻辑
4. **向后兼容**: 保留 `T8StarAdapter` 别名
5. **类型安全**: 明确的类名避免混淆

## 🧪 测试验证

所有文件已通过语法检查：
```bash
python -m py_compile app/adapters/base_adapter.py ✅
python -m py_compile app/adapters/t8star_video_adapter.py ✅
python -m py_compile app/adapters/t8star_image_adapter.py ✅
python -m py_compile app/adapters/t8star_image_edit_adapter.py ✅
python -m py_compile app/adapters/default_adapter.py ✅
python -m py_compile app/adapters/adapter_factory.py ✅
```

适配器工厂路由测试：
```python
>>> from app.adapters import get_adapter
>>> adapter = get_adapter('https://ai.t8star.cn/v2/videos/generations')
>>> print(adapter.__class__.__name__)
T8StarVideoGenerationAdapter

>>> adapter2 = get_adapter('https://ai.t8star.cn/v1/images/generations')
>>> print(adapter2.__class__.__name__)
T8StarImageGenerationAdapter
```

## 🗑️ 清理工作

旧文件 `app/adapters/api_adapter.py` 已备份为 `api_adapter.py.backup`，可安全删除。

## 📌 下一步

模块重构已完成，可以进行以下测试：
1. 启动 Worker: `python worker.py`
2. 提交视频生成任务（测试异步流程）
3. 提交图片生成任务（测试同步流程）
4. 提交图片编辑任务（测试同步流程）
