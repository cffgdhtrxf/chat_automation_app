import importlib.util
import sys
import os
import traceback

def main():
    print("🚀 启动聊天自动化系统...")
    
    try:
        # 检查依赖
        required_modules = ['PyQt5', 'cv2', 'numpy', 'keyboard', 'pyperclip', 'PIL', 'requests']
        missing_modules = []
        
        for module in required_modules:
            if not importlib.util.find_spec(module):
                missing_modules.append(module)
        
        if missing_modules:
            print(f"❌ 缺少以下模块: {', '.join(missing_modules)}")
            print("请运行: pip install -r requirements.txt")
            return
        
        # 确保在正确的项目目录下
        project_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本所在目录
        os.chdir(project_dir)  # 切换到项目目录
        
        # 动态导入主模块 - 使用绝对路径
        main_module_path = os.path.join(project_dir, "main.py")
        if not os.path.exists(main_module_path):
            print(f"❌ 找不到主模块文件: {main_module_path}")
            return
        
        spec = importlib.util.spec_from_file_location("main_module", main_module_path)
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        
        # 创建聊天自动化系统实例
        try:
            automation_system = main_module.ChatAutomationApp("user_config.json")
        except Exception as exc:
            print(f"⚠️ 初始化失败: {exc}")
            print(f"详细错误信息: {traceback.format_exc()}")
            print("❌ 无法初始化应用，请检查您的环境配置")
            input("按回车键退出...")
            return
        
        # 启动GUI
        gui_app_path = os.path.join(project_dir, "gui", "gui_app.py")
        if not os.path.exists(gui_app_path):
            print(f"❌ 找不到GUI应用文件: {gui_app_path}")
            return
        
        gui_spec = importlib.util.spec_from_file_location("gui_app", gui_app_path)
        gui_app_module = importlib.util.module_from_spec(gui_spec)
        gui_spec.loader.exec_module(gui_app_module)
        
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        
        # 创建GUI应用实例 - 现在传递自动化系统实例
        gui_app = gui_app_module.GUIApp(automation_system)
        gui_app.show()
        
        print("✅ 系统启动完成，GUI已显示")
        
        # 启动Qt事件循环
        sys.exit(app.exec_())
    
    except Exception as exc:
        print(f"❌ 程序运行时发生未处理的错误: {exc}")
        print(f"详细错误信息: {traceback.format_exc()}")
        input("按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as exc:
        print(f"❌ 程序启动时发生致命错误: {exc}")
        print(f"详细错误信息: {traceback.format_exc()}")
        input("按回车键退出...")
        sys.exit(1)