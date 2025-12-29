# 测试文档

## 测试概览

本项目使用 pytest 作为测试框架，包含完整的单元测试、集成测试和 API 测试。

### 测试覆盖范围

- **模型层测试** (`tests/test_models/`)
  - 用户模型、会员配置模型
  - 任务模型、模型定价
  - CDK 模型、交易流水模型

- **服务层测试** (`tests/test_services/`)
  - 鉴权服务 (注册、登录、单点登录互斥)
  - 任务服务 (并发控制、任务提交)
  - 支付服务 (CDK 兑换、扣费、退款)

- **API 层测试** (`tests/test_api/`)
  - 鉴权 API (注册、登录、验证码)
  - 用户 API (个人信息、会员等级)
  - 任务 API (提交任务、查询状态)
  - 钱包 API (CDK 兑换、流水查询)
  - 管理员 API (CDK 生成、用户管理)

- **工具类测试** (`tests/test_utils/`)
  - 装饰器 (权限检查、限流)
  - Redis 工具

## 安装测试依赖

```bash
pip install -r requirements-test.txt
```

## 运行测试

### 方式一：使用 pytest 直接运行

```bash
# 运行所有测试
pytest

# 详细输出
pytest -v

# 运行特定测试文件
pytest tests/test_models/test_user.py

# 运行特定测试类
pytest tests/test_models/test_user.py::TestUserModel

# 运行特定测试函数
pytest tests/test_models/test_user.py::TestUserModel::test_create_user
```

### 方式二：使用测试脚本

**Linux/Mac:**
```bash
chmod +x run_tests.sh

# 运行所有测试
./run_tests.sh

# 只运行单元测试
./run_tests.sh unit

# 只运行 API 测试
./run_tests.sh api

# 运行并生成覆盖率报告
./run_tests.sh coverage
```

**Windows:**
```cmd
# 运行所有测试
run_tests.bat

# 只运行单元测试
run_tests.bat unit

# 只运行 API 测试
run_tests.bat api

# 运行并生成覆盖率报告
run_tests.bat coverage
```

## 测试标记

使用 pytest 标记来分类测试：

- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.api` - API 测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.slow` - 慢速测试

运行特定标记的测试：

```bash
# 只运行单元测试
pytest -m unit

# 只运行 API 测试
pytest -m api

# 排除慢速测试
pytest -m "not slow"
```

## 覆盖率报告

生成覆盖率报告：

```bash
# 生成 HTML 报告
pytest --cov=app --cov-report=html

# 生成终端报告
pytest --cov=app --cov-report=term-missing

# 生成 XML 报告 (CI/CD)
pytest --cov=app --cov-report=xml
```

查看报告：
```bash
# Linux/Mac
open htmlcov/index.html

# Windows
start htmlcov/index.html
```

## 测试配置

测试配置位于 `pytest.ini` 文件中：

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --cov=app --cov-report=html
```

## 编写新测试

### 1. 单元测试示例

```python
import pytest
from app.models import User

@pytest.mark.unit
class TestUserModel:
    def test_create_user(self, db_session):
        """测试创建用户"""
        user = User(
            email='test@example.com',
            password_hash='hashed_password',
            balance=100.00
        )

        db_session.session.add(user)
        db_session.session.commit()

        assert user.id is not None
        assert user.email == 'test@example.com'
```

### 2. API 测试示例

```python
import pytest
import json

@pytest.mark.api
class TestAuthAPI:
    def test_login_success(self, client, db_session, test_user):
        """测试登录成功"""
        response = client.post(
            '/api/auth/login',
            data=json.dumps({
                'email': test_user.email,
                'password': 'password123'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'token' in data['data']
```

### 3. 使用 Fixtures

```python
@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(
        email='test@example.com',
        password_hash='hashed_password',
        balance=1000.00
    )
    db_session.session.add(user)
    db_session.session.commit()
    return user
```

## 常见问题

### 1. 测试数据库

测试使用 SQLite 内存数据库，每个测试函数执行后自动清理。

### 2. Redis 测试

测试使用 Redis 数据库 15，每个测试完成后自动清空。

### 3. Mock 外部服务

使用 `pytest-mock` Mock 外部服务：

```python
def test_send_email(self, mocker):
    mock_mail = mocker.patch('app.extensions.mail.send')

    # 测试代码...

    mock_mail.assert_called_once()
```

### 4. 测试认证

使用 `auth_headers` fixture 获取认证 header：

```python
def test_protected_endpoint(self, client, auth_headers):
    response = client.get('/api/protected', headers=auth_headers)
    assert response.status_code == 200
```

## CI/CD 集成

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run tests
      run: pytest --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 最佳实践

1. **测试命名**: 使用描述性名称，如 `test_create_user_success`
2. **单一职责**: 每个测试只测试一个功能点
3. **独立性**: 测试之间不应相互依赖
4. **清理**: 使用 fixtures 自动清理测试数据
5. **Mock**: 对外部依赖使用 Mock，避免依赖外部服务
6. **断言**: 使用清晰的断言消息
7. **覆盖率**: 保持至少 80% 的代码覆盖率

## 测试报告

运行 `./run_tests.sh coverage` 后，可以在 `htmlcov/index.html` 查看详细的覆盖率报告，包括：

- 每个文件的覆盖率百分比
- 未覆盖的代码行
- 分支覆盖情况

## 持续改进

- 定期运行测试确保代码质量
- 新增功能必须编写对应测试
- 修复 bug 时先写测试复现问题
- 保持测试代码的可维护性
