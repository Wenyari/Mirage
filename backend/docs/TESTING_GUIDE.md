# R2 存储和任务清理功能测试指南

## 测试概述

本文档介绍如何运行 Cloudflare R2 存储服务和任务清理功能的单元测试。

## 测试文件

### 1. 存储服务测试
**文件**: `tests/test_services/test_storage_service.py`

**测试内容**:
- 存储服务初始化
- 文件上传（单个/批量）
- 文件删除（单个/批量）
- 预签名 URL 生成
- 文件存在性检查
- 错误处理

**测试用例数**: 30+

### 2. 任务清理测试
**文件**: `tests/test_services/test_task_service.py`

**测试内容**:
- 清理超过3天的已完成任务
- 清理关联的存储文件
- 不清理未完成或最近的任务
- 批量清理
- 错误处理

**测试用例数**: 12+

### 3. 上传 API 测试
**文件**: `tests/test_api/test_upload.py`

**测试内容**:
- 单文件上传接口
- 批量上传接口
- 文件删除接口
- 文件类型验证
- 权限控制
- 错误处理

**测试用例数**: 25+

## 运行测试

### 前置条件

1. 安装测试依赖:
```bash
pip install -r requirements-test.txt
```

2. 确保 Redis 服务运行（用于测试环境）:
```bash
redis-server
```

### 运行所有 R2 相关测试

```bash
# 运行所有存储服务测试
pytest tests/test_services/test_storage_service.py -v

# 运行任务清理测试
pytest tests/test_services/test_task_service.py::TestTaskServiceCleanup -v

# 运行上传 API 测试
pytest tests/test_api/test_upload.py -v

# 运行所有 R2 相关测试
pytest tests/test_services/test_storage_service.py tests/test_api/test_upload.py tests/test_services/test_task_service.py::TestTaskServiceCleanup -v
```

### 运行特定测试

```bash
# 运行单个测试用例
pytest tests/test_services/test_storage_service.py::TestStorageService::test_upload_file_success -v

# 运行特定测试类
pytest tests/test_services/test_storage_service.py::TestStorageService -v
```

### 生成测试覆盖率报告

```bash
# 生成覆盖率报告
pytest tests/test_services/test_storage_service.py tests/test_api/test_upload.py --cov=app.services.storage_service --cov=app.api.upload --cov-report=html

# 查看报告
# 打开 htmlcov/index.html
```

### 运行测试并显示详细输出

```bash
# 显示打印输出
pytest tests/test_services/test_storage_service.py -v -s

# 显示失败的详细信息
pytest tests/test_services/test_storage_service.py -v --tb=long
```

## 测试结构

### 存储服务测试结构

```
TestStorageService
├── 初始化测试
│   ├── test_storage_service_init_success
│   └── test_storage_service_init_without_credentials
├── 对象键生成测试
│   ├── test_generate_object_key
│   └── test_generate_object_key_without_prefix
├── 文件上传测试
│   ├── test_upload_file_success
│   ├── test_upload_file_without_content_type
│   ├── test_upload_file_client_error
│   ├── test_upload_file_generic_exception
│   └── test_upload_file_without_client
├── 批量上传测试
│   ├── test_upload_multiple_files_success
│   └── test_upload_multiple_files_partial_failure
├── 文件删除测试
│   ├── test_delete_file_success
│   ├── test_delete_file_client_error
│   └── test_delete_file_without_client
├── 批量删除测试
│   ├── test_delete_multiple_files_success
│   └── test_delete_multiple_files_partial_failure
├── 预签名 URL 测试
│   ├── test_generate_presigned_url_success
│   ├── test_generate_presigned_url_default_expiration
│   ├── test_generate_presigned_url_error
│   └── test_generate_presigned_url_without_client
└── 文件存在性测试
    ├── test_file_exists_true
    ├── test_file_exists_false
    └── test_file_exists_without_client
```

### 任务清理测试结构

```
TestTaskServiceCleanup
├── test_cleanup_old_tasks_success
├── test_cleanup_old_tasks_with_multiple_input_files
├── test_cleanup_old_tasks_not_delete_recent
├── test_cleanup_old_tasks_not_delete_pending
├── test_cleanup_old_tasks_not_delete_without_finished_at
├── test_cleanup_old_tasks_multiple_statuses
├── test_cleanup_old_tasks_with_file_deletion_error
├── test_cleanup_old_tasks_custom_days
├── test_cleanup_old_tasks_without_files
├── test_cleanup_old_tasks_with_empty_input_file_list
└── test_cleanup_old_tasks_batch_cleanup
```

### 上传 API 测试结构

```
TestUploadHelpers
├── 文件类型验证
│   ├── test_allowed_file_image
│   ├── test_allowed_file_video
│   ├── test_allowed_file_audio
│   ├── test_allowed_file_any_type
│   ├── test_allowed_file_invalid
│   └── test_allowed_file_case_insensitive
└── MIME 类型获取
    ├── test_get_content_type_image
    ├── test_get_content_type_video
    └── test_get_content_type_audio

TestUploadAPI
├── 单文件上传
│   ├── test_upload_file_success
│   ├── test_upload_file_without_auth
│   ├── test_upload_file_no_file_provided
│   ├── test_upload_file_empty_filename
│   ├── test_upload_file_invalid_type
│   └── test_upload_file_storage_error
├── 批量上传
│   ├── test_upload_files_success
│   ├── test_upload_files_partial_failure
│   ├── test_upload_files_invalid_type
│   └── test_upload_files_no_files
└── 文件删除
    ├── test_delete_file_success
    ├── test_delete_file_permission_denied
    ├── test_delete_file_storage_error
    └── test_delete_file_without_auth
```

## Mock 说明

所有测试都使用 Mock 来模拟外部依赖，不会实际连接到 Cloudflare R2：

1. **boto3 客户端**: 使用 `mocker.patch('boto3.client')` 模拟
2. **环境变量**: 使用 `monkeypatch` 设置测试环境变量
3. **存储服务**: 在 API 测试中使用 `mocker.patch('app.api.upload.storage_service')` 模拟

## 测试数据

测试使用以下模拟数据：

- **Account ID**: `test-account-id`
- **Access Key**: `test-access-key`
- **Secret Key**: `test-secret-key`
- **Bucket Name**: `test-bucket`
- **Public URL**: `https://cdn.test.com`

## 常见问题

### 1. Redis 连接错误

**问题**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**解决方案**:
```bash
# 启动 Redis
redis-server

# 或者跳过需要 Redis 的测试
pytest tests/test_services/test_storage_service.py -v
```

### 2. 导入错误

**问题**: `ModuleNotFoundError: No module named 'pytest'`

**解决方案**:
```bash
pip install -r requirements-test.txt
```

### 3. 测试失败

**问题**: 某些测试失败

**解决方案**:
```bash
# 查看详细错误信息
pytest tests/test_services/test_storage_service.py -v --tb=long

# 运行单个失败的测试
pytest tests/test_services/test_storage_service.py::TestStorageService::test_name -v -s
```

## 持续集成

### GitHub Actions 配置示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run R2 storage tests
        run: |
          pytest tests/test_services/test_storage_service.py -v
          pytest tests/test_api/test_upload.py -v
          pytest tests/test_services/test_task_service.py::TestTaskServiceCleanup -v

      - name: Generate coverage report
        run: |
          pytest --cov=app.services.storage_service --cov=app.api.upload --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 测试最佳实践

1. **隔离性**: 每个测试独立运行，不依赖其他测试
2. **可重复性**: 测试结果一致，不受外部环境影响
3. **Mock 外部依赖**: 不实际连接 R2，使用 Mock 模拟
4. **清晰的断言**: 每个测试有明确的验证点
5. **错误场景覆盖**: 测试正常和异常情况

## 测试覆盖率目标

- **存储服务**: > 95%
- **上传 API**: > 90%
- **任务清理**: > 95%

## 下一步

1. 运行所有测试确保通过
2. 查看覆盖率报告
3. 补充缺失的测试用例
4. 集成到 CI/CD 流程

## 相关文档

- [pytest 文档](https://docs.pytest.org/)
- [pytest-mock 文档](https://pytest-mock.readthedocs.io/)
- [Flask 测试文档](https://flask.palletsprojects.com/en/2.3.x/testing/)
