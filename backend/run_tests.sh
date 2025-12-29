#!/bin/bash
# 测试运行脚本

set -e

echo "======================================"
echo "    Running Test Suite"
echo "======================================"
echo ""

# 检查是否安装了测试依赖
if ! pip show pytest > /dev/null 2>&1; then
    echo "Installing test dependencies..."
    pip install -r requirements-test.txt
fi

# 运行测试
echo "Running tests..."
echo ""

# 选项说明
# -v: 详细输出
# --cov: 生成覆盖率报告
# --cov-report: 覆盖率报告格式
# -m: 标记选择

case "$1" in
    unit)
        echo "Running unit tests only..."
        pytest -v -m unit
        ;;
    api)
        echo "Running API tests only..."
        pytest -v -m api
        ;;
    integration)
        echo "Running integration tests only..."
        pytest -v -m integration
        ;;
    quick)
        echo "Running quick tests (excluding slow tests)..."
        pytest -v -m "not slow"
        ;;
    coverage)
        echo "Running all tests with coverage report..."
        pytest -v --cov=app --cov-report=html --cov-report=term-missing
        echo ""
        echo "Coverage report generated in htmlcov/index.html"
        ;;
    *)
        echo "Running all tests..."
        pytest -v
        ;;
esac

echo ""
echo "======================================"
echo "    Test Suite Completed"
echo "======================================"
