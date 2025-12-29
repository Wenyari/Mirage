@echo off
REM Windows 测试运行脚本

echo ======================================
echo     Running Test Suite
echo ======================================
echo.

REM 检查是否安装了测试依赖
pip show pytest >nul 2>&1
if errorlevel 1 (
    echo Installing test dependencies...
    pip install -r requirements-test.txt
)

REM 运行测试
echo Running tests...
echo.

if "%1"=="unit" (
    echo Running unit tests only...
    pytest -v -m unit
) else if "%1"=="api" (
    echo Running API tests only...
    pytest -v -m api
) else if "%1"=="integration" (
    echo Running integration tests only...
    pytest -v -m integration
) else if "%1"=="quick" (
    echo Running quick tests excluding slow tests...
    pytest -v -m "not slow"
) else if "%1"=="coverage" (
    echo Running all tests with coverage report...
    pytest -v --cov=app --cov-report=html --cov-report=term-missing
    echo.
    echo Coverage report generated in htmlcov/index.html
) else (
    echo Running all tests...
    pytest -v
)

echo.
echo ======================================
echo     Test Suite Completed
echo ======================================
