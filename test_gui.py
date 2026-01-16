#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最基础的GUI测试脚本，用于验证GUI是否可以启动
"""

import sys
import os
import traceback

def test_basic_gui():
    """测试基础GUI是否可以启动"""
    print("🔍 测试基础GUI启动...")
    
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout
        from PyQt5.QtCore import Qt
        
        # 创建简单应用
        app = QApplication(sys.argv)
        
        # 创建简单窗口
        window = QMainWindow()
        window.setWindowTitle("GUI测试窗口")
        window.setGeometry(100, 100, 400, 300)
        
        # 添加简单标签
        central_widget = QWidget()
        layout = QVBoxLayout()
        label = QLabel("基础GUI测试成功！\n如果能看到这个窗口，说明PyQt5工作正常。")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        central_widget.setLayout(layout)
        window.setCentralWidget(central_widget)
        
        window.show()
        print("✅ 基础GUI测试成功！")
        
        # 退出应用
        print("窗口将在3秒后关闭...")
        from PyQt5.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(lambda: app.quit())
        timer.start(3000)  # 3秒后退出
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ 基础GUI测试失败: {e}")
        print(f"详细错误: {traceback.format_exc()}")
        input("按回车键退出...")

def test_ocr_engines():
    """测试OCR引擎是否可以导入"""
    print("\n🔍 测试OCR引擎导入...")
    
    # 测试Tesseract
    try:
        import pytesseract
        print("✅ Tesseract 可以导入")
    except ImportError as e:
        print(f"❌ Tesseract 导入失败: {e}")
    
    # 测试PaddleOCR
    try:
        import paddleocr
        print("✅ PaddleOCR 可以导入")
    except ImportError as e:
        print(f"❌ PaddleOCR 导入失败: {e}")
    except Exception as e:
        print(f"❌ PaddleOCR 导入异常: {e}")

def test_basic_imports():
    """测试基本依赖是否可以导入"""
    print("\n🔍 测试基本依赖导入...")
    
    imports_to_test = [
        ('PyQt5', 'PyQt5'),
        ('cv2', 'OpenCV'),
        ('numpy', 'NumPy'),
        ('keyboard', 'Keyboard'),
        ('pyperclip', 'Pyperclip'),
        ('PIL', 'Pillow'),
        ('pyautogui', 'PyAutoGUI')
    ]
    
    for module, name in imports_to_test:
        try:
            __import__(module)
            print(f"✅ {name} 可以导入")
        except ImportError as e:
            print(f"❌ {name} 导入失败: {e}")
        except Exception as e:
            print(f"⚠️ {name} 导入异常: {e}")

if __name__ == "__main__":
    print("🚀 启动GUI和依赖测试...")
    
    # 确保在正确的项目目录下
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    print(f"📁 当前工作目录: {project_dir}")
    
    try:
        # 测试基本依赖
        test_basic_imports()
        
        # 测试OCR引擎
        test_ocr_engines()
        
        # 测试基础GUI
        test_basic_gui()
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        print(f"详细错误: {traceback.format_exc()}")
        input("按回车键退出...")