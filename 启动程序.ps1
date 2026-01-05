Write-Host "========================================" -ForegroundColor Green
Write-Host "欢迎使用聊天自动化监控系统" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host "`n检查 Python..."
try {
    $python_version = python --version
    Write-Host "✓ Python: $python_version" -ForegroundColor Green
} catch {
    Write-Host "❌ 未找到 Python，请确保已安装并添加到环境变量" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit
}

Write-Host "`n安装依赖包..."
try {
    pip install -r requirements.txt --user
    Write-Host "✓ 依赖安装完成" -ForegroundColor Green
} catch {
    Write-Host "⚠️  安装依赖时出现问题，继续启动..." -ForegroundColor Yellow
}

Write-Host "`n检查 Ollama 服务..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/version" -TimeoutSec 5
    Write-Host "✓ Ollama 服务正常运行" -ForegroundColor Green
} catch {
    Write-Host "❌ Ollama 服务未运行" -ForegroundColor Red
    Write-Host "`n重要提示：" -ForegroundColor Yellow
    Write-Host "请先启动 Ollama 服务！" -ForegroundColor Yellow
    Write-Host "" 
    Write-Host "方法1：在新命令行窗口执行: ollama serve" -ForegroundColor Yellow
    Write-Host "方法2：如果 Ollama 是桌面应用，请启动它" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "按回车键退出"
    exit
}

Write-Host "`n启动主程序..."
python main.py

Read-Host "`n按回车键退出"