# modules/keyboard_sim.py
import pyautogui
import time
import pyperclip

class KeyboardSimulator:
    def __init__(self):
        # 配置pyautogui参数
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
    def safe_click(self, x, y):
        """安全点击，避免触发安全机制"""
        try:
            # 检查目标坐标是否在屏幕范围内
            screen_width, screen_height = pyautogui.size()
            
            # 确保坐标在屏幕范围内，但不靠近边缘
            safe_x = max(10, min(x, screen_width - 10))
            safe_y = max(10, min(y, screen_height - 10))
            
            pyautogui.click(safe_x, safe_y)
            time.sleep(0.2)
            return True
        except pyautogui.FailSafeException:
            print("安全机制触发：鼠标在屏幕角落")
            return False
        except Exception as e:
            print(f"点击失败: {e}")
            return False
    
    def send_message(self, text, input_coords, send_coords=None):
        """使用剪贴板发送消息（推荐，避免乱码）"""
        try:
            print(f"准备发送消息: {text[:50]}...")
            
            # 点击输入框
            if not self.safe_click(input_coords[0], input_coords[1]):
                return False
            
            # 清空输入框
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            
            # 使用剪贴板粘贴文本（避免乱码）
            pyperclip.copy(text)  # 复制到剪贴板
            time.sleep(0.1)  # 等待剪贴板准备
            pyautogui.hotkey('ctrl', 'v')  # 粘贴
            time.sleep(0.1)  # 等待粘贴完成
            
            # 发送消息
            if send_coords:
                if not self.safe_click(send_coords[0], send_coords[1]):
                    return False
            else:
                pyautogui.press('enter')
            
            print(f"消息发送成功: {text}")
            return True
            
        except Exception as e:
            print(f"发送消息失败: {e}")
            # 如果剪贴板方式失败，尝试备用方式
            return self.send_message_typing(text, input_coords, send_coords)
    
    def send_message_typing(self, text, input_coords, send_coords=None):
        """备用：原来的打字方式"""
        try:
            print(f"备用方式发送消息: {text[:50]}...")
            
            # 点击输入框
            if not self.safe_click(input_coords[0], input_coords[1]):
                return False
            
            # 清空输入框
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            
            # 输入文本
            pyautogui.typewrite(text, interval=0.02)
            
            # 发送消息
            if send_coords:
                if not self.safe_click(send_coords[0], send_coords[1]):
                    return False
            else:
                pyautogui.press('enter')
            
            print(f"备用方式发送成功: {text}")
            return True
            
        except Exception as e:
            print(f"备用方式发送失败: {e}")
            return False