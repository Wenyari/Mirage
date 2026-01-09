# 业务逻辑测试指南

## 概述

本目录包含活动积分系统的完整业务逻辑单元测试。所有测试使用 pytest 框架，测试数据库使用 SQLite 内存数据库。

## 测试文件结构

```
tests/
├── conftest.py                              # pytest 全局配置和 fixtures
├── test_services/
│   ├── test_pay_service_enhanced.py         # 支付服务测试（优先扣除逻辑）
│   ├── test_activity_service.py             # 活动服务测试
│   └── test_activity_admin_service.py       # 活动管理服务测试
```

## 测试覆盖的功能

### 1. test_pay_service_enhanced.py

测试支付相关核心业务逻辑：

- **优先扣除逻辑**
  - 只扣除活动积分
  - 同时扣除两种积分
  - 只扣除充值积分
  - 余额不足检测

- **CDK 兑换**
  - 成功兑换
  - 无效代码
  - 已使用
  - 已过期
  - 通用 CDK（可重复使用）
  - 等级授予

- **退款功能**
  - 成功退款
  - 用户不存在处理

- **并发安全**
  - 悲观锁测试

### 2. test_activity_service.py

测试活动相关核心业务逻辑：

- **活动领取**
  - 成功领取
  - 活动不存在
  - 达到领取上限
  - 等级要求
  - 活动状态检查（暂停/未开始/已结束）

- **每日签到**
  - 首次签到
  - 连续签到
  - 签到循环（1-7天）
  - 断签重置
  - 重复签到检测

- **签到状态查询**
  - 从未签到
  - 今天已签到
  - 连续签到状态

- **活动积分过期**
  - 单个积分过期
  - 部分扣除（余额不足）
  - 无过期积分
  - 永久积分不过期

- **活动列表和记录**
  - 获取可用活动
  - 时间范围过滤
  - 用户领取记录
  - 分页功能

### 3. test_activity_admin_service.py

测试活动管理相关业务逻辑：

- **创建活动**
  - 成功创建
  - 必填字段验证
  - 代码重复检测
  - 日期格式验证

- **更新活动**
  - 成功更新
  - 活动不存在
  - 更新日期字段
  - 清除日期字段

- **删除活动**
  - 成功删除
  - 有领取记录时无法删除
  - 活动不存在

- **活动列表**
  - 获取所有活动
  - 状态筛选
  - 分页功能

- **活动统计**
  - 无领取记录
  - 有领取记录
  - 多用户统计

- **签到配置**
  - 获取默认配置
  - 更新配置
  - 验证规则
  - 禁用配置

- **集成测试**
  - 完整生命周期测试

## 安装依赖

```bash
pip install pytest pytest-cov pytest-mock
```

## 运行测试

### 运行所有测试

```bash
# 在项目根目录下执行
pytest tests/

# 或者带详细输出
pytest tests/ -v

# 带覆盖率报告
pytest tests/ --cov=app/services --cov-report=html
```

### 运行特定测试文件

```bash
# 只测试支付服务
pytest tests/test_services/test_pay_service_enhanced.py -v

# 只测试活动服务
pytest tests/test_services/test_activity_service.py -v

# 只测试活动管理服务
pytest tests/test_services/test_activity_admin_service.py -v
```

### 运行特定测试类

```bash
# 只测试优先扣除逻辑
pytest tests/test_services/test_pay_service_enhanced.py::TestCheckAndDeductBalance -v

# 只测试签到功能
pytest tests/test_services/test_activity_service.py::TestDailyCheckin -v
```

### 运行特定测试用例

```bash
# 只测试从两种积分同时扣除的情况
pytest tests/test_services/test_pay_service_enhanced.py::TestCheckAndDeductBalance::test_deduct_from_both_balances -v
```

## 测试输出示例

```
tests/test_services/test_pay_service_enhanced.py::TestCheckAndDeductBalance::test_deduct_from_activity_only PASSED [ 10%]
tests/test_services/test_pay_service_enhanced.py::TestCheckAndDeductBalance::test_deduct_from_both_balances PASSED [ 20%]
tests/test_services/test_pay_service_enhanced.py::TestCheckAndDeductBalance::test_insufficient_balance PASSED [ 30%]
...

========================== 45 passed in 2.35s ==========================
```

## 覆盖率报告

运行带覆盖率的测试后，可以查看 HTML 报告：

```bash
# 生成覆盖率报告
pytest tests/ --cov=app/services --cov-report=html

# 打开报告（在浏览器中）
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

## 测试数据说明

所有测试使用 `conftest.py` 中定义的 fixtures：

### 基础 Fixtures

- `app` - Flask 应用实例（会话级别）
- `db_session` - 数据库会话（函数级别，每个测试独立）
- `redis_db` - Redis 客户端（函数级别）

### 用户 Fixtures

- `test_user` - 普通测试用户（T3等级，recharge_balance=10000）
- `admin_user` - 管理员用户（T5等级）
- `test_user_with_activity_balance` - 有活动积分的用户（recharge=100, activity=50）

### 数据 Fixtures

- `test_cdk` - 测试 CDK（500积分，一次性码）
- `test_activity` - 测试活动（100积分，30天有效期）
- `test_task` - 测试任务

### Mock Fixtures

- `mock_redis` - 模拟 Redis（用于不依赖 Redis 的测试）
- `mock_mail` - 模拟邮件发送

## 注意事项

1. **数据库隔离**：每个测试函数都有独立的数据库会话，测试完成后自动回滚
2. **Redis 清理**：每个测试完成后会清空 Redis 测试数据库（db=15）
3. **并发测试**：实际并发测试需要多线程，当前只验证悲观锁不会报错
4. **时间相关测试**：使用固定的过去/未来时间，避免时区问题

## 常见问题

### Q1: 测试失败提示 Redis 连接错误

**解决方案：** 测试使用 `redis://localhost:6379/15`，确保 Redis 运行。如果没有 Redis，某些测试会被跳过。

### Q2: SQLite 不支持某些特性

**解决方案：** 测试使用内存 SQLite，某些 MySQL 特性（如外键约束）可能表现不同。关键业务逻辑不依赖数据库特定特性。

### Q3: 如何调试失败的测试

```bash
# 使用 -s 显示 print 输出
pytest tests/test_services/test_activity_service.py -v -s

# 使用 --pdb 在失败时进入调试器
pytest tests/test_services/test_activity_service.py --pdb

# 只运行失败的测试
pytest tests/test_services/test_activity_service.py --lf
```

## 测试最佳实践

1. **每个测试独立**：不依赖其他测试的执行结果
2. **明确的测试名称**：一看就知道测试什么场景
3. **完整的断言**：验证所有相关状态，不只是一个字段
4. **边界条件**：测试正常情况和异常情况
5. **使用 fixtures**：复用测试数据，保持测试简洁

## 持续集成

建议在 CI/CD 管道中添加测试步骤：

```yaml
# .github/workflows/test.yml
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
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-mock
      - name: Run tests
        run: pytest tests/ --cov=app/services --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 测试统计

当前测试覆盖情况：

- **test_pay_service_enhanced.py**: 18个测试用例
- **test_activity_service.py**: 27个测试用例
- **test_activity_admin_service.py**: 25个测试用例
- **总计**: 70+ 个测试用例

覆盖的核心业务场景：

- ✅ 优先扣除逻辑（4个场景）
- ✅ CDK 兑换（6个场景）
- ✅ 活动领取（7个场景）
- ✅ 每日签到（6个场景）
- ✅ 积分过期（4个场景）
- ✅ 活动管理（15个场景）
- ✅ 签到配置（7个场景）

---

## 反馈与贡献

如果发现测试问题或需要添加新的测试场景，欢迎提交 Issue 或 Pull Request。
