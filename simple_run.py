#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版启动脚本，用于解决闪退问题
"""

import sys
import os
import traceback

def safe_import(module_name, package_name=None):
    """安全导入模块，如果失败则返回None"""
    try:
        if package_name:
            __import__(package_name)
        return __import__(module_name)
    except ImportError as e:
        print(f"⚠️ 无法导入 {module_name}: {e}")
        return None
    except Exception as e:
        print(f"⚠️ 导入 {module_name} 时发生错误: {e}")
        return None

def main():
    print("🚀 启动聊天自动化系统 (简化版)...")
    
    # 确保在正确的项目目录下
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    print(f"📁 当前工作目录: {project_dir}")
    
    # 检查必需的文件
    required_files = ["main.py", "user_config.json"]  # 更正配置文件名
    missing_files = []
    
    for f in required_files:
        if not os.path.exists(f):
            missing_files.append(f)
    
    if missing_files:
        print(f"❌ 找不到必需文件: {missing_files}")
        input("按回车键退出...")
        return
    
    print("✅ 必需文件检查通过")
    
    # 尝试导入必要模块
    print("🔍 检查依赖模块...")
    
    # 检查PyQt5
    pyqt5_ok = safe_import('PyQt5')
    if not pyqt5_ok:
        print("❌ PyQt5 未安装或不可用")
        input("按回车键退出...")
        return
    
    # 检查其他依赖
    dependencies = {
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'keyboard': 'Keyboard',
        'pyperclip': 'Pyperclip',
        'PIL': 'Pillow',
    }
    
    missing_deps = []
    for module, name in dependencies.items():
        if not safe_import(module):
            missing_deps.append(name)
    
    if missing_deps:
        print(f"⚠️ 以下依赖缺失: {missing_deps}")
        print("请运行: pip install -r requirements.txt")
    
    # 尝试导入项目模块
    try:
        import main
        print("✅ 成功导入 main 模块")
    except Exception as e:
        print(f"❌ 导入 main 模块失败: {e}")
        print(f"详细错误: {traceback.format_exc()}")
        input("按回车键退出...")
        return
    
    try:
        # 尝试初始化系统，使用Tesseract OCR避免PyTorch问题
        automation_system = main.ChatAutomationSystem(ocr_engine='tesseract')
        print("✅ 聊天自动化系统初始化成功")
    except Exception as e:
        print(f"❌ 初始化聊天自动化系统失败: {e}")
        print(f"详细错误: {traceback.format_exc()}")
        
        # 尝试使用PaddleOCR
        try:
            print("🔄 尝试使用PaddleOCR...")
            automation_system = main.ChatAutomationSystem(ocr_engine='paddle')
            print("✅ 聊天自动化系统初始化成功 (PaddleOCR)")
        except Exception as e2:
            print(f"❌ 两种OCR引擎初始化都失败: {e2}")
            print(f"详细错误: {traceback.format_exc()}")
            input("按回车键退出...")
            return
    
    # 尝试导入GUI模块
    try:
        import gui.gui_app
        print("✅ 成功导入GUI模块")
    except Exception as e:
        print(f"❌ 导入GUI模块失败: {e}")
        print(f"详细错误: {traceback.format_exc()}")
        input("按回车键退出...")
        return
    
    # 启动GUI
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        
        # 创建GUI应用实例
        gui_app = gui.gui_app.GUIApp(automation_system)
        gui_app.show()
        
        print("✅ 系统启动完成，GUI已显示")
        
        # 启动Qt事件循环
        sys.exit(app.exec_())
    
    except Exception as e:
        print(f"❌ 启动GUI失败: {e}")
        print(f"详细错误: {traceback.format_exc()}")
        input("按回车键退出...")
        return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序启动时发生致命错误: {e}")
        print(f"详细错误信息: {traceback.format_exc()}")
        input("按回车键退出...")