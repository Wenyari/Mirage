#!/bin/bash
# R2 存储和任务清理功能测试运行脚本

echo "========================================="
echo "  R2 Storage & Task Cleanup Tests"
echo "========================================="
echo ""

# 检查 pytest 是否安装
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest not found. Installing test dependencies..."
    pip install -r requirements-test.txt
fi

# 运行存储服务测试
echo "1. Running Storage Service Tests..."
echo "-----------------------------------"
pytest tests/test_services/test_storage_service.py -v --tb=short
STORAGE_RESULT=$?

echo ""
echo "2. Running Task Cleanup Tests..."
echo "-----------------------------------"
pytest tests/test_services/test_task_service.py::TestTaskServiceCleanup -v --tb=short
CLEANUP_RESULT=$?

echo ""
echo "========================================="
echo "  Test Results Summary"
echo "========================================="

if [ $STORAGE_RESULT -eq 0 ]; then
    echo "✓ Storage Service Tests: PASSED"
else
    echo "✗ Storage Service Tests: FAILED"
fi

if [ $CLEANUP_RESULT -eq 0 ]; then
    echo "✓ Task Cleanup Tests: PASSED"
else
    echo "✗ Task Cleanup Tests: FAILED"
fi

echo ""
echo "========================================="

# 如果所有测试通过，返回 0；否则返回 1
if [ $STORAGE_RESULT -eq 0 ] && [ $CLEANUP_RESULT -eq 0 ]; then
    echo "All tests passed! ✓"
    exit 0
else
    echo "Some tests failed. Please check the output above."
    exit 1
fi
