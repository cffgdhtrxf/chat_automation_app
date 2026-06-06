import sys
import os
from webui.api import app, init_app

# 导入主应用
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import ChatAutomationApp

def main():
    print("🚀 启动聊天自动化Web UI...")
    
    # 创建主应用实例
    automation_app = ChatAutomationApp("user_config.json")
    
    # 初始化Web UI
    init_app(automation_app)
    
    print("🌐 Web UI 已启动")
    print("🌐 访问地址: http://localhost:5000")
    
    # 启动Flask服务器
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()
