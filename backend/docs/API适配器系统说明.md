# API 适配器系统说明

## 概述

由于不同上游 API 的响应格式不一致，我们实现了一个适配器系统来标准化各种 API 响应。

## 问题背景

**T8Star API (https://ai.t8star.cn) 响应格式：**

```json
{
    "task_id": "veo3:1756693796-YQVHH4A3Lg",
    "status": "SUCCESS",
    "progress": "100%",  // ❌ 字符串而不是整数
    "fail_reason": "",
    "data": {
        "output": "https://filesystem.site/cdn/..."  // ❌ 直接是字符串，不是 {url: "..."}
    }
}
```

**标准 API 响应格式：**

```json
{
    "task_id": "abc-123",
    "status": "SUCCEEDED",
    "progress": 100,  // ✓ 整数
    "output": {
        "url": "https://..."  // ✓ 对象
    }
}
```

## 架构设计

### 1. 适配器基类 (`ApiAdapter`)

定义了所有适配器必须实现的接口：

```python
class ApiAdapter:
    def parse_submit_response(self, response_data: dict) -> Optional[str]:
        """解析提交响应，提取上游任务ID"""
        raise NotImplementedError

    def parse_status_response(self, response_data: dict) -> dict:
        """
        解析状态查询响应，标准化为统一格式

        返回格式：
        {
            "status": str,  # RUNNING | SUCCESS | FAILED
            "progress": int,  # 0-100
            "result_url": str | None,
            "fail_reason": str | None
        }
        """
        raise NotImplementedError
```

### 2. T8Star 适配器 (`T8StarAdapter`)

专门处理 T8Star API 的响应格式：

**特点：**
- 进度是字符串 `"100%"` → 解析为整数 `100`
- 结果链接在 `data.output` 中，且是字符串而不是对象
- 状态值 `SUCCESS` 而不是 `SUCCEEDED`

**实现：**
```python
class T8StarAdapter(ApiAdapter):
    def parse_status_response(self, response_data: dict) -> dict:
        # 1. 状态映射
        status_map = {
            'SUCCESS': 'SUCCESS',
            'RUNNING': 'RUNNING',
            'FAILED': 'FAILED',
            ...
        }

        # 2. 进度解析（"100%" -> 100）
        progress = self._parse_progress(response_data.get('progress', '0'))

        # 3. 结果 URL 提取（data.output 直接是字符串）
        result_url = response_data.get('data', {}).get('output')

        return {
            'status': normalized_status,
            'progress': progress,
            'result_url': result_url,
            'fail_reason': response_data.get('fail_reason')
        }
```

### 3. 默认适配器 (`DefaultAdapter`)

处理标准格式的 API 响应（OpenAI 风格）。

### 4. 适配器工厂 (`get_adapter`)

根据 API Base URL 自动选择对应的适配器：

```python
def get_adapter(api_base: str) -> ApiAdapter:
    if 't8star.cn' in api_base.lower():
        return T8StarAdapter(api_base)
    # elif 'api.openai.com' in api_base:
    #     return OpenAIAdapter(api_base)
    else:
        return DefaultAdapter(api_base)
```

## Worker 集成

在 `worker.py` 中的使用：

```python
from app.adapters import get_adapter

def process_task(payload):
    # 1. 根据 API Base 创建适配器
    adapter = get_adapter(payload['api_base'])

    # 2. 提交任务，解析响应
    response_data = requests.post(...).json()
    task_uuid = adapter.parse_submit_response(response_data)

    # 3. 轮询状态，解析响应
    raw_data = requests.get(status_url).json()
    parsed = adapter.parse_status_response(raw_data)

    state = parsed['status']  # SUCCESS | FAILED | RUNNING
    progress = parsed['progress']  # 0-100 整数
    result_url = parsed['result_url']
    fail_reason = parsed['fail_reason']

    # 4. 统一处理（无需关心原始格式差异）
    if state == 'SUCCESS':
        task.result_url = result_url
        ...
```

## 如何添加新的适配器

### 步骤 1: 创建适配器类

在 `app/adapters/api_adapter.py` 中添加新的适配器类：

```python
class NewProviderAdapter(ApiAdapter):
    """
    新提供商的适配器

    响应格式示例：
    {
        "id": "task-123",
        "state": "done",  # done | processing | error
        "percent": 80,
        "result": {"video": "https://..."}
    }
    """

    def parse_submit_response(self, response_data: dict) -> Optional[str]:
        # 提取任务ID（根据实际响应字段调整）
        return response_data.get('id')

    def parse_status_response(self, response_data: dict) -> dict:
        # 状态映射
        status_map = {
            'done': 'SUCCESS',
            'processing': 'RUNNING',
            'error': 'FAILED',
        }

        raw_status = response_data.get('state', '')
        normalized_status = status_map.get(raw_status, 'RUNNING')

        # 进度
        progress = response_data.get('percent', 0)

        # 结果 URL
        result_url = None
        if normalized_status == 'SUCCESS':
            result_url = response_data.get('result', {}).get('video')

        # 失败原因
        fail_reason = response_data.get('error_message')

        return {
            'status': normalized_status,
            'progress': progress,
            'result_url': result_url,
            'fail_reason': fail_reason
        }
```

### 步骤 2: 注册适配器

在 `get_adapter()` 函数中添加域名匹配：

```python
def get_adapter(api_base: str) -> ApiAdapter:
    api_base_lower = api_base.lower()

    if 't8star.cn' in api_base_lower:
        return T8StarAdapter(api_base)

    # 新增适配器
    elif 'newprovider.com' in api_base_lower:
        logger.info(f"Using NewProviderAdapter for API base: {api_base}")
        return NewProviderAdapter(api_base)

    else:
        return DefaultAdapter(api_base)
```

### 步骤 3: 测试

提交一个使用新 API 的任务，观察 worker 日志：

```
[INFO] Using NewProviderAdapter for API base: https://api.newprovider.com/...
[INFO] Task xxx submitted successfully, upstream ID: task-123
[INFO] Task xxx status: RUNNING, progress: 35%
[INFO] Task xxx status: SUCCESS, progress: 100%
[INFO] Task xxx completed successfully, result: https://...
```

## 支持的适配器

| 适配器 | 匹配规则 | 状态 |
|--------|----------|------|
| `T8StarAdapter` | `t8star.cn` | ✅ 已实现 |
| `DefaultAdapter` | 其他所有 | ✅ 默认 |

## 常见问题

### Q1: 如何调试适配器？

在适配器中添加详细日志：

```python
def parse_status_response(self, response_data: dict) -> dict:
    logger.debug(f"Raw response: {response_data}")

    parsed = {
        'status': normalized_status,
        ...
    }

    logger.debug(f"Parsed result: {parsed}")
    return parsed
```

### Q2: 如果适配器解析失败怎么办？

适配器会抛出异常，worker 会捕获并标记任务失败：

```python
try:
    parsed = adapter.parse_status_response(raw_data)
except Exception as e:
    logger.error(f"Adapter parsing failed: {e}")
    # 任务会被标记为 failed
```

### Q3: 可以为同一个域名创建多个适配器吗？

可以，通过更精确的路径匹配：

```python
def get_adapter(api_base: str) -> ApiAdapter:
    if 'api.provider.com/v1' in api_base:
        return ProviderV1Adapter(api_base)
    elif 'api.provider.com/v2' in api_base:
        return ProviderV2Adapter(api_base)
    ...
```

## 测试清单

添加新适配器后，请测试以下场景：

- [ ] 任务提交成功，task_id 正确提取
- [ ] 轮询中状态为 RUNNING，进度正确显示
- [ ] 任务成功完成，result_url 正确提取
- [ ] 任务失败，fail_reason 正确提取
- [ ] 进度字符串（如 "50%"）正确解析为整数
- [ ] 各种状态值（SUCCESS/SUCCEEDED/COMPLETED）正确映射

## 文件位置

```
backend/
├── app/
│   ├── adapters/
│   │   ├── __init__.py          # 导出适配器
│   │   └── api_adapter.py       # 适配器实现
│   └── ...
├── worker.py                     # 使用适配器
└── docs/
    └── API适配器系统说明.md      # 本文档
```

## 相关文档

- [任务ID映射修复说明.md](./任务ID映射修复说明.md)
- [统一任务查询接口说明.md](./统一任务查询接口说明.md)
- [数据库表设计.md](./数据库表设计.md)
