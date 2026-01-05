# run.py
import os
import sys
import subprocess
import time

def check_and_install_dependencies():
    """检查并安装依赖包"""
    print("聊天自动化监控系统启动器")
    print("=" * 50)
    
    # 检查 Python 版本
    print(f"Python 版本: {sys.version}")
    
    # 检查并安装依赖
    print("\n检查依赖包...")
    
    # 读取 requirements.txt
    requirements_file = 'requirements.txt'
    if os.path.exists(requirements_file):
        with open(requirements_file, 'r', encoding='utf-8') as f:
            required_packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    else:
        # 默认依赖列表
        required_packages = [
            'opencv-python==4.8.1.78',
            'pyautogui==0.9.53',
            'pytesseract==0.3.10',
            'pillow==12.1.0',
            'requests==2.31.0',
            'pyqt5==5.15.9',
            'keyboard==0.13.5',
            'pyperclip==1.8.2'
        ]
    
    missing_packages = []
    for package in required_packages:
        package_name = package.split('==')[0].split('>=')[0].split('<=')[0]
        try:
            __import__(package_name.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} (待安装)")
    
    if missing_packages:
        print(f"\n正在安装 {len(missing_packages)} 个缺失的包...")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', package])
                print(f"✓ {package} 安装成功")
            except:
                print(f"✗ {package} 安装失败")
    
    print("\n依赖检查完成！")

def check_ollama():
    """检查 Ollama 服务"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            print("✓ Ollama 服务正常运行")
            return True
        else:
            print("✗ Ollama 服务响应异常")
            return False
    except:
        print("✗ Ollama 服务未运行")
        print("  请先启动 Ollama 服务: ollama serve")
        print("  或在新窗口中运行: ollama serve")
        return False

def main():
    print("聊天自动化监控系统启动器")
    print("=" * 50)
    
    # 检查依赖
    check_and_install_dependencies()
    
    # 检查 Ollama
    if not check_ollama():
        print("\n⚠️  重要提示：")
        print("   请确保 Ollama 服务正在运行！")
        print("   在新命令行窗口执行: ollama serve")
        print("   然后再启动本程序")
        input("\n按回车键退出...")
        return
    
    print("\n启动主程序...")
    print("-" * 50)
    
    try:
        # 运行主程序
        subprocess.run([sys.executable, 'main.py'])
    except KeyboardInterrupt:
        print("\n程序已停止")
    except Exception as e:
        print(f"启动失败: {e}")
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()