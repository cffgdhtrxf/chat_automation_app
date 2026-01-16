# main.py
import cv2
import time
import threading
import json
from modules.screen_monitor import ScreenMonitor
from modules.ai_handler import AIHandler
from modules.keyboard_sim import KeyboardSimulator
from modules.config_loader import ConfigLoader
from modules.auto_copy_handler import AutoCopyHandler

class ChatAutomationApp:
    def __init__(self, config_file="config.json"):
        # 加载配置
        self.config = ConfigLoader(config_file)
        print(f"⚙️ 配置加载完成: {self.config.config}")  # 调试信息
        
        # 初始化键盘模拟器
        self.keyboard_sim = KeyboardSimulator()
        
        # 初始化AI处理器 - 确保传递的是完整的配置字典
        print(f"🤖 配置对象类型: {type(self.config)}")  # 调试信息
        print(f"🤖 配置内容: {self.config.config}")  # 调试信息
        self.ai_handler = AIHandler(self.config.config)  # 关键修复：传递config.config而不是config对象
        
        # 初始化屏幕监控器，传递配置
        self.screen_monitor = ScreenMonitor(
            callback=self.on_new_content,
            confidence_threshold=self.config.config.get('confidence_threshold', 0.7),
            check_interval=self.config.config.get('check_interval', 0.5)
        )
        
        # 从配置加载屏幕区域设置
        screen_region = self.config.config.get('screen_region', {
            'offset_x': 0,
            'offset_y': 0,
            'width': 800,
            'height': 600
        })
        self.screen_monitor.update_detection_region(
            screen_region['offset_x'],
            screen_region['offset_y'],
            screen_region['width'],
            screen_region['height']
        )
        
        # 初始化自动复制处理器
        self.auto_copy_handler = AutoCopyHandler(self.config)
        
        # 启动屏幕监控线程
        self.monitor_thread = None
        self.auto_copy_thread = None
        
        print("✅ 应用初始化完成")

    def update_model(self, new_model_name):
        """更新AI模型"""
        print(f"🔄 更新AI模型为: {new_model_name}")
        # 更新配置
        self.config.config['ollama_model'] = new_model_name
        # 重新创建AI处理器以使用新模型
        self.ai_handler = AIHandler(self.config.config)
        print(f"✅ AI模型已更新为: {new_model_name}")

    def start_monitoring(self):
        """启动监控 - 根据配置的模式决定启动哪种功能"""
        active_mode = self.config.config.get('active_mode', 'auto_copy')
        print(f"🔄 当前激活模式: {active_mode}")
        print(f"📋 启用自动复制: {self.config.config.get('enable_auto_copy', False)}")
        
        if active_mode == 'screen_monitor':
            # 启动屏幕监控模式
            if self.monitor_thread is None or not self.monitor_thread.is_alive():
                self.monitor_thread = threading.Thread(target=self.screen_monitor.start_monitoring, daemon=True)
                self.monitor_thread.start()
                print("✅ 屏幕监控已启动")
            else:
                print("⚠️ 屏幕监控已在运行")
        elif active_mode == 'auto_copy':
            # 启动自动复制模式
            self.start_auto_copy()
        else:
            print(f"❌ 未知模式: {active_mode}")

    def stop_monitoring(self):
        """停止监控 - 根据配置的模式决定停止哪种功能"""
        active_mode = self.config.config.get('active_mode', 'auto_copy')
        print(f"🔄 停止模式: {active_mode}")
        
        if active_mode == 'screen_monitor':
            # 停止屏幕监控模式
            self.screen_monitor.stop_monitoring()
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2)  # 最多等待2秒
            print("✅ 屏幕监控已停止")
        elif active_mode == 'auto_copy':
            # 停止自动复制模式
            self.stop_auto_copy()
        else:
            print(f"❌ 未知模式: {active_mode}")

    def start_auto_copy(self):
        """启动自动复制功能"""
        try:
            # 检查坐标是否已设置
            capture_point = self.config.config.get('capture_point', {'x': 0, 'y': 0})
            input_point = self.config.config.get('input_point', {'x': 0, 'y': 0})
            print(f"📋 捕获点坐标: ({capture_point.get('x', 0)}, {capture_point.get('y', 0)})")
            print(f"⌨️ 输入框坐标: ({input_point.get('x', 0)}, {input_point.get('y', 0)})")
            
            if capture_point.get('x', 0) == 0 and capture_point.get('y', 0) == 0:
                print("❌ 捕获点坐标未设置，请先设置坐标")
                return False
            if input_point.get('x', 0) == 0 and input_point.get('y', 0) == 0:
                print("❌ 输入框坐标未设置，请先设置坐标")
                return False
                
            self.auto_copy_handler.start_listening()
            print("✅ 自动复制功能已启动")
            return True
        except Exception as e:
            print(f"❌ 启动自动复制功能失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def stop_auto_copy(self):
        """停止自动复制功能"""
        try:
            self.auto_copy_handler.stop_listening()
            print("✅ 自动复制功能已停止")
            return True
        except Exception as e:
            print(f"❌ 停止自动复制功能失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def on_new_content(self, detected_text):
        """当检测到新内容时的回调函数"""
        print(f"💬 检测到新内容: {detected_text}")
        print(f"🤖 当前使用的模型: {self.config.config.get('ollama_model', 'default')}")
        print(f"🤖 AI处理器的配置类型: {type(self.ai_handler.config)}")
        print(f"🤖 AI处理器的配置内容: {self.ai_handler.config}")  # 新增调试信息
        
        # 使用AI处理检测到的内容
        response = self.ai_handler.get_ai_response(detected_text)
        
        if response:
            print(f"🤖 AI响应: {response}")
            
            # 发送响应
            self.send_response(response)

    def send_response(self, response):
        """发送响应"""
        # 使用键盘模拟器发送响应
        self.keyboard_sim.type_text(response)
        time.sleep(0.1)  # 短暂延迟
        self.keyboard_sim.press_enter()

    def update_screen_region(self, x, y, width, height):
        """更新屏幕监控区域"""
        self.screen_monitor.update_detection_region(x, y, width, height)
        print(f"🔄 屏幕监控区域已更新: ({x}, {y}, {width}, {h})")

    def get_current_region(self):
        """获取当前屏幕监控区域"""
        return self.screen_monitor.get_current_region()

def main():
    """主函数"""
    automation_system = ChatAutomationApp("user_config.json")
    
    try:
        # 启动监控
        automation_system.start_monitoring()
        
        # 保持主线程运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 程序即将退出...")
        automation_system.stop_monitoring()

if __name__ == "__main__":
    main()