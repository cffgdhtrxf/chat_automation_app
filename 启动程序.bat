@echo off
chcp 65001 >nul
title 聊天自动化监控系统启动器

echo ========================================
echo 欢迎使用聊天自动化监控系统
echo ========================================
echo.

echo 检查 Python...
python --version 2>nul
if errorlevel 1 (
    echo 错误：未找到 Python，请确保已安装 Python 并添加到环境变量
    pause
    exit /b
)

echo.
echo 检查并安装依赖...
pip install -r requirements.txt --user

echo.
echo 检查 Ollama 服务...
curl -s http://localhost:11434/api/version >nul 2>&1
if errorlevel 1 (
    echo ❌ Ollama 服务未运行
    echo.
    echo 重要提示：
    echo 请先启动 Ollama 服务！
    echo.
    echo 方法1：在新命令行窗口执行: ollama serve
    echo 方法2：如果 Ollama 是桌面应用，请启动它
    echo.
    pause
    exit /b
) else (
    echo ✓ Ollama 服务正常运行
)

echo.
echo 启动主程序...
python main.py

pause