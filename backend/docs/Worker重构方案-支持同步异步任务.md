# Worker 重构方案：支持同步和异步任务

## 一、回答你的疑问

### 疑问 1：Worker 如何确认任务结束并发送结果给前端？

**当前流程：**
```
用户提交任务
    ↓
TaskService → 数据库（tasks 表，status='pending'）
    ↓
KeyManager 分配密钥 → Redis 队列（queue:runnable）
    ↓
Worker 取出任务 → 调用上游 API
    ↓
Worker 轮询上游进度 → 更新数据库（status='success', result_url='...'）
    ↓
前端轮询 GET /api/tasks/{task_id} → 查询数据库 → 获取结果
```

**关键点：**
- Worker **不直接发送**结果给前端
- Worker 将结果**写入数据库**（`tasks` 表）
- 前端通过 **API 轮询**查询数据库获取结果
- 数据库是 Worker 和前端之间的**桥梁**

**代码证据：** `worker.py:307-311`
```python
# 任务成功（使用独立连接）
success_sql = text("""
    UPDATE tasks
    SET status = 'success',
        progress = 100,
        result_url = :result_url,  # ← 结果存入数据库
        finished_at = :finished_at
    WHERE id = :task_id
""")
```

**前端查询：** `app/services/task_service.py:215-240`
```python
@classmethod
def get_task_status(cls, user_id: int, task_id: str):
    task = Task.query.get(task_id)
    task_dict = task.to_dict()  # ← 前端从数据库读取结果

    if task.status == 'processing':
        # 读取 Redis 实时进度
        redis_progress = get_redis().get(f"task:progress:{task_id}")
        if redis_progress:
            task_dict['progress'] = int(redis_progress)

    return task_dict
```

---

### 疑问 2：Worker 是否会等待上一个任务结束才取下一个？

**是的**，当前 Worker 是**单进程单循环**的同步执行模式：

**代码证据：** `worker.py:400-412`
```python
with app.app_context():
    while True:
        # 阻塞式取任务（超时 1 秒）
        raw_task = get_redis().blpop(KeyManager.QUEUE_RUNNABLE, timeout=1)

        if raw_task:
            payload = json.loads(task_json)
            logger.info(f"Received task: {payload['task_id']}")

            # 同步处理任务（会阻塞，直到任务完全完成）
            process_task(payload)  # ← 这里会等待轮询完成
```

**执行流程：**
```
┌─────────────────────────────────────────────────────────┐
│ Worker Main Loop (单线程，同步执行)                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [Task 1] ──→ 提交 → 轮询 10 分钟 → 完成 ────┐        │
│                                               │        │
│  [等待 Task 1 完成...]                        │        │
│                                               ↓        │
│  [Task 2] ──→ 只有 Task 1 完全结束后才会开始处理      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**影响：**
- ✅ 对于**长时间异步任务**（视频生成，10 分钟）：合理，因为占用了 API 密钥
- ❌ 对于**快速同步任务**（图片生成，秒级）：效率低下，浪费资源

**如果要并发处理，需要：**
- 多进程 Worker（启动多个 `python worker.py` 实例）
- 多线程 Worker（ThreadPoolExecutor）
- 异步 Worker（asyncio + aiohttp）

**当前设计的优势：**
- 简单可靠
- 每个任务独占一个密钥，不会冲突
- 错误隔离（一个任务失败不影响其他）

---

## 二、问题分析

根据探索结果，当前 Worker 存在以下问题：

### 1. 请求体构造硬编码（视频生成特化）

**当前代码：** `worker.py:206-224`
```python
# 【视频生成特化】硬编码了请求体结构
submit_payload = {
    "model": payload.get('model'),        # 必需
    "prompt": payload.get('prompt', ''),  # 必需
    "images": images,                      # 必需（视频需要参考图）
    **params                               # 展开其他参数
}
```

**不同任务类型的差异：**

| 任务类型 | 请求体结构 | 必需字段 |
|---------|-----------|---------|
| **视频生成** | `{model, prompt, images, duration, ...}` | `model`, `prompt`, `images` |
| **图片生成** | `{model, prompt, size, aspect_ratio, n, ...}` | `model`, `prompt` |
| **图片编辑** | `{model, image, mask, prompt, ...}` | `model`, `image`, `prompt` |

### 2. 轮询逻辑硬编码（假定所有任务都是异步）

**当前代码：** `worker.py:263-323`
```python
# 【视频生成特化】假定所有任务都需要轮询
max_poll_time = 600  # 硬编码 10 分钟
poll_interval = 3    # 硬编码 3 秒间隔

while True:
    time.sleep(poll_interval)
    check = requests.get(status_url, headers=headers, timeout=30)
    # ... 解析状态
```

**问题：**
- 图片生成是**同步的**（提交后直接在响应中返回结果），不需要轮询
- 当前代码会浪费时间去轮询一个已经完成的任务

**澄清"同步"和"异步"的含义：**

| 类型 | 提交流程 | Worker 是否阻塞 | 是否需要轮询 |
|------|---------|---------------|------------|
| **异步任务（视频）** | POST → 返回 task_id → 需要后续轮询进度 | ✅ 是（等待提交 + 轮询） | ✅ 是 |
| **同步任务（图片）** | POST → 等待几秒/几十秒 → 直接返回结果 | ✅ 是（等待上游 API 处理） | ❌ 否 |

**关键区别：**
```
异步任务（视频生成）:
  Worker POST 提交 (1s)
    → 收到 task_id (1s)
    → 每 3 秒轮询一次状态 (3s × 200次 = 10分钟)
    → 总等待时间: ~10 分钟

同步任务（图片生成）:
  Worker POST 提交 (1s)
    → 等待上游 API 处理 (5-30s)
    → 直接收到结果图片 URL
    → 总等待时间: ~5-30 秒
    → 无需轮询，节省了后续的轮询时间
```

**所以两种任务都会让 Worker 阻塞等待**，区别是：
- 同步任务：一次 HTTP 请求，等待完成
- 异步任务：一次提交 + N 次轮询，等待完成

### 3. ApiAdapter 职责不完整

**当前 ApiAdapter 仅负责：**
- ✅ 解析提交响应（提取 task_id）
- ✅ 解析状态响应（标准化状态/进度/结果）

**缺失的职责：**
- ❌ 构造请求体（不同 API 的请求格式不同）
- ❌ 判断是否需要轮询（同步 vs 异步）
- ❌ 提供轮询策略（超时、间隔）

---

## 三、重构方案（推荐）：扩展 ApiAdapter 职责

### 核心思想

**将 ApiAdapter 从"响应解析器"扩展为"完整的任务处理策略"**，包含：
1. 请求体构造
2. 同步/异步判断
3. 响应解析（已有）
4. 轮询配置（如果异步）

### 方案优势

✅ **利用现有系统** - 已有适配器路由机制（`get_adapter()`）
✅ **职责清晰** - 每个适配器封装对应 API 的所有特性
✅ **易于扩展** - 添加新 API 只需创建新适配器
✅ **Worker 保持通用** - Worker 只负责调度和错误处理

---

## 四、详细设计

### 步骤 1：扩展 ApiAdapter 基类

**文件：** `app/adapters/api_adapter.py`

```python
class ApiAdapter:
    """API 适配器基类"""

    def __init__(self, api_base: str):
        self.api_base = api_base

    # ========== 新增方法 ==========

    def build_submit_payload(self, task_payload: dict) -> dict:
        """
        构造提交请求体

        Args:
            task_payload: 从队列取出的任务数据
                {
                    "task_id": "...",
                    "model": "sora-2",
                    "prompt": "...",
                    "params": {...},
                    "input_file_url": "..."
                }

        Returns:
            dict: 上游 API 的请求体
                示例（视频）: {
                    "model": "sora-2",
                    "prompt": "...",
                    "images": [...],
                    "duration": 5
                }
                示例（图片）: {
                    "model": "dall-e-3",
                    "prompt": "...",
                    "size": "1024x1024"
                }
        """
        raise NotImplementedError

    def is_async_task(self) -> bool:
        """
        判断是否是异步任务（需要轮询）

        Returns:
            bool: True=异步任务，需要轮询进度
                  False=同步任务，直接返回结果
        """
        raise NotImplementedError

    def get_polling_config(self) -> dict:
        """
        获取轮询配置（仅异步任务需要）

        Returns:
            dict: {
                "max_timeout": 600,   # 最长轮询时间（秒）
                "interval": 3,        # 轮询间隔（秒）
                "status_url_pattern": "{base}/{task_id}"  # URL 模板
            }
        """
        return {
            "max_timeout": 600,
            "interval": 3,
            "status_url_pattern": "{base}/{task_id}"
        }

    def parse_sync_response(self, response_data: dict) -> dict:
        """
        解析同步响应（仅同步任务需要）

        Args:
            response_data: 提交响应的 JSON 数据

        Returns:
            dict: {
                "result_url": "https://...",  # 结果链接
                "result_urls": ["https://..."],  # 多个结果（图片生成可能返回多张）
                "metadata": {...}  # 其他元数据
            }
        """
        return {
            "result_url": None,
            "result_urls": [],
            "metadata": {}
        }

    # ========== 已有方法保持不变 ==========

    def parse_submit_response(self, response_data: dict) -> Optional[str]:
        """提取上游任务ID（异步任务需要）"""
        raise NotImplementedError

    def parse_status_response(self, response_data: dict) -> dict:
        """解析状态查询响应（异步任务需要）"""
        raise NotImplementedError
```

---

### 步骤 2：实现具体适配器

#### 2.1 视频生成适配器（异步）

```python
class T8StarAdapter(ApiAdapter):
    """T8Star 视频生成适配器（异步）"""

    def build_submit_payload(self, task_payload: dict) -> dict:
        """构造视频生成请求体"""
        params = task_payload.get('params', {})

        # 处理 images 字段
        images = params.get('images', [])
        if not images and task_payload.get('input_file_url'):
            input_url = task_payload['input_file_url']
            images = [input_url] if isinstance(input_url, str) else input_url

        return {
            "model": task_payload.get('model'),
            "prompt": task_payload.get('prompt', ''),
            "images": images,
            **params  # duration, aspect_ratio 等参数
        }

    def is_async_task(self) -> bool:
        return True  # 视频生成是异步的

    def get_polling_config(self) -> dict:
        return {
            "max_timeout": 600,  # 10 分钟
            "interval": 3,       # 3 秒
            "status_url_pattern": "{base}/{task_id}"
        }

    # parse_submit_response 和 parse_status_response 保持不变
```

#### 2.2 图片生成适配器（同步）

```python
class T8StarImageGenerationAdapter(ApiAdapter):
    """T8Star 图片生成适配器（同步）"""

    def build_submit_payload(self, task_payload: dict) -> dict:
        """构造图片生成请求体"""
        params = task_payload.get('params', {})

        # 图片生成可能有参考图
        images = params.get('image', [])

        return {
            "model": task_payload.get('model'),
            "prompt": task_payload.get('prompt', ''),
            "size": params.get('size', '1024x1024'),
            "aspect_ratio": params.get('aspect_ratio', '1:1'),
            "image": images,  # 可选：参考图
            **{k: v for k, v in params.items()
               if k not in ['size', 'aspect_ratio', 'image']}
        }

    def is_async_task(self) -> bool:
        return False  # 图片生成是同步的

    def parse_sync_response(self, response_data: dict) -> dict:
        """解析同步响应"""
        # 假设响应格式：
        # {
        #   "created": 1234567890,
        #   "data": [
        #     {"b64_json": "..." 或 "url": "https://..."}
        #   ]
        # }
        data = response_data.get('data', [])
        result_urls = []

        for item in data:
            if 'url' in item:
                result_urls.append(item['url'])
            elif 'b64_json' in item:
                # 可以将 base64 转换为 URL，或直接存储
                result_urls.append(f"data:image/png;base64,{item['b64_json']}")

        return {
            "result_url": result_urls[0] if result_urls else None,
            "result_urls": result_urls,
            "metadata": {
                "created": response_data.get('created'),
                "count": len(result_urls)
            }
        }
```

#### 2.3 图片编辑适配器（同步）

```python
class T8StarImageEditAdapter(ApiAdapter):
    """T8Star 图片编辑适配器（同步）"""

    def build_submit_payload(self, task_payload: dict) -> dict:
        """构造图片编辑请求体"""
        params = task_payload.get('params', {})

        return {
            "model": task_payload.get('model'),
            "image": params.get('image'),  # 必需：原图
            "mask": params.get('mask'),    # 可选：掩码
            "prompt": task_payload.get('prompt', ''),
            "size": params.get('size', '1024x1024'),
            "n": params.get('n', 1),
            **{k: v for k, v in params.items()
               if k not in ['image', 'mask', 'size', 'n']}
        }

    def is_async_task(self) -> bool:
        return False  # 图片编辑是同步的

    def parse_sync_response(self, response_data: dict) -> dict:
        """解析同步响应（与图片生成相同）"""
        data = response_data.get('data', [])
        result_urls = []

        for item in data:
            if 'url' in item:
                result_urls.append(item['url'])
            elif 'b64_json' in item:
                result_urls.append(f"data:image/png;base64,{item['b64_json']}")

        return {
            "result_url": result_urls[0] if result_urls else None,
            "result_urls": result_urls,
            "metadata": {
                "created": response_data.get('created'),
                "count": len(result_urls)
            }
        }
```

---

### 步骤 3：重构 Worker.process_task()

**文件：** `worker.py`

**修改点 1：使用适配器构造请求体**
```python
# ❌ 旧代码（硬编码）
submit_payload = {
    "model": payload.get('model'),
    "prompt": payload.get('prompt', ''),
    "images": images,
    **params
}

# ✅ 新代码（使用适配器）
submit_payload = adapter.build_submit_payload(payload)
```

**修改点 2：根据任务类型选择处理流程**
```python
# 提交任务到上游 API
resp = requests.post(submit_url, headers=headers, json=submit_payload, timeout=30)
response_data = resp.json()

# 【关键分支】判断是同步还是异步
if adapter.is_async_task():
    # ========== 异步任务流程 ==========
    # 1. 提取 task_id
    task_uuid = adapter.parse_submit_response(response_data)

    # 2. 保存 upstream_task_id
    save_upstream_sql = text(...)
    execute_sql(save_upstream_sql, {"task_id": task_id, "upstream_task_id": task_uuid})

    # 3. 轮询进度
    polling_config = adapter.get_polling_config()
    status_url = polling_config['status_url_pattern'].format(
        base=status_base, task_id=task_uuid
    )
    max_poll_time = polling_config['max_timeout']
    poll_interval = polling_config['interval']

    while True:
        time.sleep(poll_interval)
        check = requests.get(status_url, headers=headers, timeout=30)
        parsed = adapter.parse_status_response(check.json())

        if parsed['status'] == 'SUCCESS':
            # 更新数据库
            success_sql = text(...)
            execute_sql(success_sql, {
                "task_id": task_id,
                "result_url": parsed['result_url'],
                "finished_at": datetime.now()
            })
            break
        elif parsed['status'] == 'FAILED':
            raise Exception(parsed['fail_reason'])

else:
    # ========== 同步任务流程 ==========
    # 1. 直接从提交响应中解析结果
    result = adapter.parse_sync_response(response_data)

    # 2. 立即更新数据库为成功
    success_sql = text("""
        UPDATE tasks
        SET status = 'success',
            progress = 100,
            result_url = :result_url,
            finished_at = :finished_at
        WHERE id = :task_id
    """)
    execute_sql(success_sql, {
        "task_id": task_id,
        "result_url": result['result_url'],
        "finished_at": datetime.now()
    })

    logger.info(f"Task {task_id} completed synchronously, result: {result['result_url']}")
```

---

## 五、实施步骤

### 1. 扩展 ApiAdapter 基类
- [ ] 添加 `build_submit_payload()` 方法
- [ ] 添加 `is_async_task()` 方法
- [ ] 添加 `get_polling_config()` 方法
- [ ] 添加 `parse_sync_response()` 方法

### 2. 实现具体适配器
- [ ] `T8StarAdapter`（视频生成，异步）
- [ ] `T8StarImageGenerationAdapter`（图片生成，同步）
- [ ] `T8StarImageEditAdapter`（图片编辑，同步）

### 3. 重构 Worker
- [ ] 使用 `adapter.build_submit_payload()` 构造请求
- [ ] 添加同步/异步分支逻辑
- [ ] 同步任务：直接解析结果并更新数据库
- [ ] 异步任务：保持现有轮询逻辑

### 4. 更新 get_adapter() 路由
- [ ] 确保正确路由到新适配器
- [ ] 测试路径匹配逻辑

### 5. 测试
- [ ] 测试视频生成（异步）
- [ ] 测试图片生成（同步）
- [ ] 测试图片编辑（同步）
- [ ] 验证数据库更新正确
- [ ] 验证前端能获取结果

---

## 六、关键文件

| 文件 | 修改内容 |
|------|---------|
| `app/adapters/api_adapter.py` | 扩展基类，实现新适配器 |
| `worker.py` | 重构 process_task()，支持同步/异步分支 |
| `app/adapters/__init__.py` | 导出新适配器 |

---

## 七、优势总结

✅ **职责清晰** - 适配器封装所有 API 特性，Worker 只负责流程控制
✅ **易于扩展** - 添加新 API 只需创建新适配器，无需修改 Worker
✅ **向后兼容** - 现有视频生成逻辑保持不变
✅ **性能优化** - 同步任务无需等待轮询，秒级完成
✅ **代码复用** - Worker 核心逻辑复用（数据库、密钥管理、错误处理）

---

## 八、后续优化（可选）

如果未来需要支持**高并发**处理快速任务，可以考虑：

### 选项 1：多进程 Worker
```bash
# 启动 3 个 Worker 实例
python worker.py &
python worker.py &
python worker.py &
```
- 简单易行
- 每个 Worker 独立处理任务
- 适合当前架构

### 选项 2：改造为异步 Worker（复杂）
```python
import asyncio
import aiohttp

async def process_task_async(payload):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as resp:
            result = await resp.json()
    # ...
```
- 需要大量重构
- 适合大规模高并发场景
- 可以后续再考虑
