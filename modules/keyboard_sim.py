# modules/keyboard_sim.py
import pyautogui
import time
import random

class KeyboardSimulator:
    def __init__(self):
        # 设置pyautogui的通用延迟
        pyautogui.PAUSE = 0.1  # 操作之间的小延迟
    
    def send_message(self, message, input_coords):
        """发送消息 - 使用更可靠的方法输入文字"""
        try:
            # 检查输入参数
            if not message or not input_coords:
                print("❌ 输入参数无效: 消息或坐标为空")
                return False
                
            if len(input_coords) != 2:
                print("❌ 坐标参数格式错误，应为 (x, y)")
                return False
                
            # 点击输入框
            x, y = input_coords
            pyautogui.click(x, y)
            time.sleep(0.3)  # 等待焦点设置
            
            # 清空输入框（可选）
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            time.sleep(0.1)
            
            # 计算打字速度 - 基于消息长度
            message_length = len(message)
            
            # 根据消息长度调整打字速度
            if message_length < 10:  # 短消息
                delay = random.uniform(0.05, 0.1)  # 0.05-0.1秒/字符
            elif message_length < 50:  # 中等消息
                delay = random.uniform(0.08, 0.15)  # 0.08-0.15秒/字符
            else:  # 长消息
                delay = random.uniform(0.1, 0.25)  # 0.1-0.25秒/字符
            
            # 使用pyperclip复制粘贴的方式（更可靠）
            import pyperclip
            pyperclip.copy(message)  # 复制消息到剪贴板
            
            # 粘贴消息（使用Ctrl+V）
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)  # 等待粘贴完成
            
            # 检查是否成功粘贴（可选：添加延时以模拟打字）
            if message_length > 0:
                # 根据消息长度添加相应的延时
                total_delay = message_length * delay
                time.sleep(total_delay)
                
                # 发送消息（回车键）
                pyautogui.press('enter')
                print(f"消息已发送，长度: {message_length} 字符")
                return True
            else:
                print("消息为空")
                return False
                
        except pyautogui.FailSafeException:
            print("❌ 鼠标移动到屏幕角落触发了PyAutoGUI的安全机制")
            return False
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False