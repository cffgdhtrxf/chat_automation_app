# modules/screen_monitor.py
import cv2
import numpy as np
import pyautogui
from PIL import Image
import time
import threading

class ScreenMonitor:
    def __init__(self, callback=None, confidence_threshold=0.7, check_interval=0.5):
        self.callback = callback
        self.confidence_threshold = confidence_threshold
        self.check_interval = check_interval
        self.previous_screenshot = None
        self.last_change_time = time.time()
        self.running = False
        self.monitor_thread = None
        
        # 获取屏幕区域参数（从配置文件中获取，需要从外部获取）
        self.detection_region = None  # 初始化时不确定区域
        print(f"🎯 屏幕监控初始化完成，检测阈值: {confidence_threshold}，检查间隔: {check_interval}s")
    
    def update_detection_region(self, x, y, width, height):
        """更新屏幕检测区域"""
        self.detection_region = (x, y, width, height)
        print(f"🔄 屏幕检测区域已更新: ({x}, {y}, {width}, {height})")
        self.reset_change_detection()
    
    def get_current_region(self):
        """获取当前屏幕检测区域"""
        return self.detection_region

    def capture_screen(self):
        """捕获屏幕截图"""
        try:
            # 全屏截图
            screenshot = pyautogui.screenshot()
            
            # 如果设置了检测区域，则截取指定区域
            if self.detection_region:
                x, y, width, height = self.detection_region
                
                # 边界检查
                screen_width, screen_height = screenshot.size
                if x < 0:
                    x = 0
                if y < 0:
                    y = 0
                if x + width > screen_width:
                    width = screen_width - x
                if y + height > screen_height:
                    height = screen_height - y
                
                # 检查宽高是否有效
                if width <= 0 or height <= 0:
                    print(f"⚠️ 检测区域尺寸无效: ({x}, {y}, {width}, {height})，使用全屏截图")
                    self.detection_region = None
                else:
                    # 裁剪指定区域
                    screenshot = screenshot.crop((x, y, x + width, y + height))
                    print(f"📸 已截取检测区域: ({x}, {y}, {width}, {height})")
            
            # 转换为numpy数组
            img = np.array(screenshot)
            # RGB转BGR
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            return img
        except Exception as e:
            print(f"❌ 屏幕捕获失败: {e}")
            # 返回空图像
            return None

    def detect_changes(self, current_img):
        """检测屏幕变化"""
        if self.previous_screenshot is None:
            # 第一次捕获，直接保存
            self.previous_screenshot = current_img.copy() if current_img is not None else None
            return True
        
        if current_img is None:
            return False
        
        # 计算差异
        diff = cv2.absdiff(self.previous_screenshot, current_img)
        # 转换为灰度图
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        # 计算非零像素数量
        non_zero_count = cv2.countNonZero(gray_diff)
        
        # 计算变化百分比
        total_pixels = current_img.shape[0] * current_img.shape[1]
        change_percentage = (non_zero_count / total_pixels) * 100
        
        print(f"🔍 屏幕变化检测: {change_percentage:.2f}% (像素变化: {non_zero_count}/{total_pixels})")
        
        # 更新上一次的截图
        self.previous_screenshot = current_img.copy()
        
        # 如果变化超过阈值，则认为有变化
        threshold = self.confidence_threshold * 100  # 转换为百分比进行比较
        return change_percentage > threshold

    def reset_change_detection(self):
        """重置变化检测"""
        self.previous_screenshot = None

    def start_monitoring(self):
        """启动屏幕监控"""
        if self.running:
            print("⚠️ 屏幕监控已在运行中")
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("✅ 屏幕监控已启动")

    def stop_monitoring(self):
        """停止屏幕监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("✅ 屏幕监控已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 捕获屏幕
                current_img = self.capture_screen()
                
                # 检测变化
                if self.detect_changes(current_img):
                    print("✨ 检测到屏幕变化")
                    # 这里可以触发回调，但现在我们只是打印
                    if self.callback:
                        # 注意：这里需要实际的文本内容作为参数调用回调
                        # 由于我们移除了OCR功能，暂时使用占位符
                        pass
                        
                # 等待下一个检查周期
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"❌ 监控循环中出现错误: {e}")
                time.sleep(self.check_interval)

    def cleanup(self):
        """清理资源"""
        self.stop_monitoring()
        if self.previous_screenshot is not None:
            del self.previous_screenshot
            self.previous_screenshot = None