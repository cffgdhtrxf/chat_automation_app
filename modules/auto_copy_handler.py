import pyautogui
import time
import keyboard
import requests
import json
import threading
import random
from .config_loader import ConfigLoader
import datetime
import platform
import getpass

class SystemInfoProvider:
    def __init__(self):
        pass
    
    def get_basic_info(self):
        """获取基本系统信息"""
        return {
            'current_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'weekday': datetime.datetime.now().strftime("%A"),
            'timezone': str(datetime.datetime.now().astimezone().tzinfo),
            'system_name': platform.system(),
            'machine_type': platform.machine(),
            'user_name': getpass.getuser(),
            'platform_details': platform.platform()
        }
    
    def get_formatted_info(self):
        """获取格式化的系统信息字符串"""
        info = self.get_basic_info()
        return f"""系统信息:
- 当前时间: {info['current_time']}
- 星期: {info['weekday']}
- 时区: {info['timezone']}
- 用户: {info['user_name']}
- 操作系统: {info['system_name']} ({info['platform_details']})"""

class AutoCopyHandler:
    def __init__(self, config: ConfigLoader):
        self.config = config
        self.system_info_provider = SystemInfoProvider()  # 添加系统信息提供器
        self.is_running = False
        self.auto_copy_thread = None
        self.last_processed_text = ""  # 记录上次处理的文本，避免重复处理
        self.last_processed_time = 0   # 记录处理时间，避免短时间内重复处理
        self.is_processing = False     # 标记是否正在处理中，避免并发处理
        self.processing_lock = threading.Lock()  # 线程锁

        # 程序启动时清理一次剪贴板
        self._clear_clipboard()

    def _clear_clipboard(self):
        """清理剪贴板"""
        try:
            import pyperclip
            pyperclip.copy("")  # 清空剪贴板
            print("🧹 启动时剪贴板已清理")
        except Exception as e:
            print(f"⚠️ 启动时清理剪贴板失败: {e}")

    def perform_auto_copy_cycle(self):
        """
        执行一次自动复制周期:
        1. 点击文本捕获点选中文本
        2. 复制文本
        3. 发送给Ollama模型
        4. 获取模型回复
        5. 点击输入框
        6. 粘贴回复
        7. 回车发送
        8. 清理剪贴板
        """
        with self.processing_lock:  # 使用锁确保线程安全
            # 检查是否还在运行（在开始执行前检查，避免停止时继续执行）
            if not self.is_running:
                print("🛑 自动复制已停止，跳过本次周期")
                return

            # 防止并发执行
            if self.is_processing:
                print("🔄 上一个处理周期仍在进行，跳过本次周期")
                return

            self.is_processing = True  # 设置处理标志

        try:
            # 获取坐标配置 - 优先使用新的monitoring配置格式
            monitoring_config = self.config.get('monitoring', {})
            capture_point = monitoring_config.get('copy_area_coords', {})
            input_point = monitoring_config.get('input_coords', {})
            
            # 如果新格式没有找到，尝试旧格式
            if not capture_point:
                capture_point = self.config.get('capture_point', {'x': 0, 'y': 0})
            if not input_point:
                input_point = self.config.get('input_point', {'x': 0, 'y': 0})

            capture_x = capture_point.get('x', 0)
            capture_y = capture_point.get('y', 0)
            input_x = input_point.get('x', 0)
            input_y = input_point.get('y', 0)

            if capture_x == 0 and capture_y == 0:
                print("⚠️ 文本捕获点坐标未设置")
                return

            if input_x == 0 and input_y == 0:
                print("⚠️ 输入框坐标未设置")
                return

            print(f"🖱️ 准备点击坐标 - 捕获点: ({capture_x}, {capture_y}), 输入框: ({input_x}, {input_y})")

            # 添加随机的人类行为模拟
            # 1. 鼠标移动模拟人类轨迹
            self._human_like_mouse_move(capture_x, capture_y)
            time.sleep(random.uniform(0.2, 0.5))  # 随机停顿

            # 2. 点击文本捕获点并选中文本
            print(f"🖱️ 移动到文本捕获点 ({capture_x}, {capture_y}) 并选中文本")
            pyautogui.click(capture_x, capture_y)
            time.sleep(random.uniform(0.1, 0.3))  # 随机停顿
            pyautogui.tripleClick(capture_x, capture_y)  # 三击选中文本
            time.sleep(random.uniform(0.2, 0.4))  # 随机停顿

            # 3. 复制文本 (Ctrl+C) - 添加随机停顿
            print("📋 执行复制操作")
            time.sleep(random.uniform(0.1, 0.2))
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(random.uniform(0.3, 0.7))  # 等待复制完成

            # 4. 从剪贴板获取文本
            import pyperclip
            captured_text = pyperclip.paste()
            print(f"📄 捕获到的文本: {captured_text[:50]}...")  # 只显示前50个字符

            if not captured_text.strip():
                print("⚠️ 捕获的文本为空，跳过处理")
                return

            # 检查是否为重复文本（避免重复处理AI的回复或用户消息）
            current_time = time.time()
            if (captured_text.strip() == self.last_processed_text.strip() and 
                current_time - self.last_processed_time < 10):  # 10秒内不重复处理
                print("🔄 检测到重复文本，跳过处理")
                return

            # 5. 发送给Ollama模型 - 使用增强的系统信息注入
            response_text = self.send_to_ollama_with_system_info(captured_text)
            if not response_text:
                print("⚠️ Ollama未返回响应，跳过处理")
                return

            print(f"🤖 Ollama响应: {response_text[:50]}...")  # 只显示前50个字符

            # 添加AI思考时间模拟
            thinking_time = len(response_text) * random.uniform(0.05, 0.15)  # 根据回复长度计算思考时间
            thinking_time = max(1.0, min(thinking_time, 8.0))  # 限制在1-8秒之间
            print(f"⏳ 模拟AI思考时间: {thinking_time:.2f}秒")
            time.sleep(thinking_time)

            # 6. 鼠标移动到输入框（模拟人类轨迹）
            self._human_like_mouse_move(input_x, input_y)
            time.sleep(random.uniform(0.1, 0.3))

            # 7. 点击输入框
            print(f"🖱️ 点击输入框 ({input_x}, {input_y})")
            pyautogui.click(input_x, input_y)
            time.sleep(random.uniform(0.1, 0.3))

            # 8. 粘贴AI回复 (Ctrl+V) - 添加随机停顿
            print("📋 准备粘贴AI回复到输入框")
            pyperclip.copy(response_text)  # 确保AI回复在剪贴板中
            time.sleep(random.uniform(0.1, 0.2))
            pyautogui.hotkey('ctrl', 'v')  # 粘贴AI回复
            time.sleep(random.uniform(0.2, 0.5))

            # 9. 添加打字延迟模拟，让粘贴看起来更自然
            typing_delay = len(response_text) * random.uniform(0.01, 0.03)  # 模拟打字时间
            print(f"⌨️ 模拟打字时间: {typing_delay:.2f}秒")
            time.sleep(typing_delay)

            # 10. 回车发送 - 添加随机停顿
            print("📨 发送AI回复消息")
            time.sleep(random.uniform(0.2, 0.8))  # 发送前随机停顿
            pyautogui.press('enter')

            # 更新记录
            self.last_processed_text = captured_text.strip()
            self.last_processed_time = time.time()

            print("✅ 自动复制周期完成 - 用户消息已处理，AI回复已发送")

        except Exception as e:
            print(f"❌ 自动复制周期执行失败: {e}")
        finally:
            # 11. 清理剪贴板 - 这是关键改进！
            try:
                import pyperclip
                pyperclip.copy("")  # 清空剪贴板
                print("🧹 循环结束后剪贴板已清理")
            except Exception as e:
                print(f"⚠️ 循环结束后清理剪贴板失败: {e}")
            
            with self.processing_lock:  # 使用锁确保线程安全
                self.is_processing = False  # 无论成功与否，都要清除处理标志

    def _human_like_mouse_move(self, target_x, target_y):
        """模拟人类鼠标移动轨迹"""
        current_x, current_y = pyautogui.position()
        steps = random.randint(10, 25)  # 随机步数
        duration = random.uniform(0.3, 0.8)  # 总移动时间
        
        for i in range(steps):
            progress = i / steps
            # 使用缓动函数让移动更自然
            ease_progress = pow(progress, 2)  # 二次缓动
            
            # 添加轻微的随机偏移
            offset_x = random.uniform(-2, 2)
            offset_y = random.uniform(-2, 2)
            
            x = current_x + (target_x - current_x) * ease_progress + offset_x
            y = current_y + (target_y - current_y) * ease_progress + offset_y
            
            pyautogui.moveTo(x, y)
            time.sleep(duration / steps * random.uniform(0.8, 1.2))  # 随机速度变化

    def send_to_ollama_with_system_info(self, text):
        """发送文本到Ollama并获取响应 - 强制注入系统信息"""
        try:
            # 获取Ollama配置
            ollama_config = self.config.get('ollama', {})
            ollama_host = ollama_config.get('url', 'http://localhost:11434/api/generate')
            
            if not ollama_host or ollama_host == 'http://localhost:11434/api/generate':
                ollama_base_host = self.config.get('ollama_host', 'http://localhost:11434')
                if not ollama_host or '/api/' not in ollama_host:
                    ollama_host = f"{ollama_base_host}/api/generate"
            
            ollama_model = self.config.get('ollama_model', ollama_config.get('model', 'llama2'))
            
            # 获取系统信息
            system_info_text = self.system_info_provider.get_formatted_info()
            
            # 强制使用包含系统信息的提示模板，而不是配置中的模板
            enhanced_prompt = f"""你是一个智能对话助手。请根据以下信息进行回复：

{system_info_text}

用户消息: {text}

请根据上述系统信息和用户消息进行智能回复:"""

            # 构造请求
            payload = {
                "model": ollama_model,
                "prompt": enhanced_prompt,  # 强制使用增强提示，忽略配置中的模板
                "stream": False
            }

            print(f"📤 发送请求到Ollama: {ollama_host}")
            print(f"📝 使用增强提示（包含系统信息）")
            response = requests.post(ollama_host, json=payload, timeout=60)

            if response.status_code != 200:
                print(f"❌ Ollama请求失败，状态码: {response.status_code}")
                print(f"Response: {response.text}")
                return None

            result = response.json()
            response_text = result.get('response', '')

            return response_text

        except Exception as e:
            print(f"❌ 发送到Ollama时出现错误: {e}")
            return None

    def send_to_ollama(self, text):
        """原始的发送方法（保留，以防需要）"""
        try:
            # 获取Ollama配置 - 优先使用config中的ollama配置块
            ollama_config = self.config.get('ollama', {})
            ollama_host = ollama_config.get('url', 'http://localhost:11434/api/generate')
            
            # 如果上面的配置没有URL，则使用备用方法获取
            if not ollama_host or ollama_host == 'http://localhost:11434/api/generate':
                ollama_base_host = self.config.get('ollama_host', 'http://localhost:11434')
                if not ollama_host or '/api/' not in ollama_host:
                    ollama_host = f"{ollama_base_host}/api/generate"
            
            ollama_model = self.config.get('ollama_model', ollama_config.get('model', 'llama2'))
            prompt_template = self.config.get('prompt_template', '请对以下消息进行简洁回复：{message}')

            # 替换模板中的消息占位符
            prompt = prompt_template.format(message=text)

            # 构造请求
            payload = {
                "model": ollama_model,
                "prompt": prompt,
                "stream": False
            }

            print(f"📤 发送请求到Ollama: {ollama_host}")
            response = requests.post(ollama_host, json=payload, timeout=60)

            if response.status_code != 200:
                print(f"❌ Ollama请求失败，状态码: {response.status_code}")
                print(f"Response: {response.text}")
                return None

            result = response.json()
            response_text = result.get('response', '')

            return response_text

        except Exception as e:
            print(f"❌ 发送到Ollama时出现错误: {e}")
            return None

    def start_listening(self):
        """开始自动复制功能（连续运行模式）"""
        if self.is_running:
            print("⚠️ 自动复制已在运行")
            return

        print("🔄 开始自动复制功能（连续运行模式）")
        print(f"📋 捕获点坐标: ({self.config.get('capture_point', {'x': 0, 'y': 0}).get('x', 0)}, {self.config.get('capture_point', {'x': 0, 'y': 0}).get('y', 0)})")
        print(f"⌨️ 输入框坐标: ({self.config.get('input_point', {'x': 0, 'y': 0}).get('x', 0)}, {self.config.get('input_point', {'x': 0, 'y': 0}).get('y', 0)})")
        
        # 启动时再次清理剪贴板，确保干净状态
        self._clear_clipboard()
        print("🧹 启动时再次清理剪贴板，确保干净状态")
        
        # 重置记录的状态
        self.last_processed_text = ""
        self.last_processed_time = 0
        self.is_processing = False
        
        # 确保配置已更新到最新状态
        import time
        time.sleep(0.1)  # 短暂延迟，确保配置更新
        
        # 启动自动复制线程
        self.is_running = True  # 在启动线程前设置标志
        self.auto_copy_thread = threading.Thread(target=self._continuous_auto_copy, daemon=True)
        self.auto_copy_thread.start()

    def stop_listening(self):
        """停止自动复制功能"""
        if not self.is_running:
            return

        print("⏹️ 停止自动复制功能")
        self.is_running = False  # 设置停止标志
        
        # 停止时也清理剪贴板
        try:
            import pyperclip
            pyperclip.copy("")  # 清空剪贴板
            print("🧹 停止时剪贴板已清理")
        except Exception as e:
            print(f"⚠️ 停止时清理剪贴板失败: {e}")
        
        # 等待线程结束
        if self.auto_copy_thread and self.auto_copy_thread.is_alive():
            self.auto_copy_thread.join(timeout=2)  # 最多等待2秒
        print("✅ 自动复制功能已完全停止")

    def _continuous_auto_copy(self):
        """连续执行自动复制周期"""
        # 获取自动复制的时间间隔（秒）
        interval = self.config.get('auto_copy_interval', 2)  # 减少间隔到2秒，更快响应
        print(f"⏱️ 自动复制间隔: {interval}秒")
        
        while self.is_running:
            try:
                # 在开始新的周期前再次检查是否还在运行
                if not self.is_running:
                    break
                    
                self.perform_auto_copy_cycle()
                # 等待指定的时间间隔（加入随机性避免过于规律）
                base_wait = interval
                random_jitter = random.uniform(-0.5, 0.5)  # ±0.5秒随机抖动
                wait_time = max(0.5, base_wait + random_jitter)  # 确保至少等待0.5秒
                
                remaining_time = wait_time
                while remaining_time > 0 and self.is_running:
                    sleep_time = min(0.1, remaining_time)  # 每0.1秒检查一次
                    time.sleep(sleep_time)
                    remaining_time -= sleep_time
            except Exception as e:
                print(f"❌ 连续自动复制过程中出现错误: {e}")
                time.sleep(1)  # 出错后稍作延时再继续