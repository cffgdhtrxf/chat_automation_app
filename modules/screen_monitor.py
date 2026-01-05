# modules/screen_monitor.py
import cv2
import numpy as np
import pyautogui
from PIL import Image
import time

class ScreenMonitor:
    def __init__(self, config):
        self.config = config
        self.last_screenshot = None
        self.region = (0, 0, 800, 600)  # 默认监控区域 (x, y, width, height)
        
        # 获取屏幕缩放信息
        self.scale_factor = self.get_scale_factor()
        print(f"屏幕缩放因子: {self.scale_factor}")
    
    def get_scale_factor(self):
        """获取屏幕缩放因子 - 针对 150% 缩放优化"""
        try:
            import ctypes
            # 设置进程 DPI 感知，避免自动缩放
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            user32 = ctypes.windll.user32
            dpi = user32.GetDpiForSystem()
            scale_factor = dpi / 96.0
            print(f"系统 DPI: {dpi}, 缩放因子: {scale_factor}")
            return scale_factor
        except:
            print("无法获取 DPI 信息，使用默认缩放因子 1.0")
            return 1.0
    
    def set_monitor_region(self, x, y, width, height):
        """设置监控区域 - 不进行坐标转换，直接使用原始坐标"""
        # 不进行任何缩放转换，直接使用用户输入的坐标
        self.region = (x, y, width, height)
        print(f"监控区域设置为: {self.region}")
    
    def capture_screen(self):
        """捕获屏幕指定区域 - 增强版"""
        try:
            screenshot = pyautogui.screenshot(
                region=self.region
            )
            # 转换为OpenCV格式
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            return img
        except Exception as e:
            print(f"屏幕捕获失败: {e}")
            # 尝试捕获全屏然后裁剪
            try:
                full_screenshot = pyautogui.screenshot()
                img = cv2.cvtColor(np.array(full_screenshot), cv2.COLOR_RGB2BGR)
                x, y, w, h = self.region
                cropped_img = img[y:y+h, x:x+w]
                return cropped_img
            except Exception as e2:
                print(f"备用捕获方法也失败: {e2}")
                return None
    
    def detect_changes(self, current_img):
        """检测屏幕变化 - 安全版本"""
        if self.last_screenshot is None:
            self.last_screenshot = current_img
            return True
        
        try:
            # 确保两张图片尺寸相同
            if self.last_screenshot.shape != current_img.shape:
                # 如果尺寸不同，调整到相同尺寸
                current_img_resized = cv2.resize(current_img, 
                                               (self.last_screenshot.shape[1], 
                                                self.last_screenshot.shape[0]))
                diff = cv2.absdiff(self.last_screenshot, current_img_resized)
            else:
                diff = cv2.absdiff(self.last_screenshot, current_img)
            
            non_zero_count = np.count_nonzero(diff)
            
            # 更新上一次截图
            self.last_screenshot = current_img
            
            # 如果差异像素超过阈值，认为有变化
            return non_zero_count > 100  # 阈值可调整
            
        except Exception as e:
            print(f"检测变化时出错: {e}")
            # 出错时也认为有变化，避免程序停止
            self.last_screenshot = current_img
            return True
    
    def save_screenshot(self, img, filename):
        """保存截图用于调试"""
        cv2.imwrite(f"screenshots/{filename}", img)