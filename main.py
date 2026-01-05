# main.py
import sys
import os

# 设置 DPI 感知以避免缩放问题
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # 使程序 DPI 感知
except:
    pass

from PyQt5.QtWidgets import QApplication
import time
import threading
import re
import cv2  # 添加 cv2 导入
import numpy as np  # 添加 numpy 导入

# 导入模块
from config import CONFIG
from modules.screen_monitor import ScreenMonitor
from modules.ocr_processor import OCRProcessor
from modules.ai_handler import AIHandler
from modules.keyboard_sim import KeyboardSimulator
from modules.gui_app import GUIApp

class ChatAutomationSystem:
    def __init__(self):
        self.config = CONFIG
        self.screen_monitor = ScreenMonitor(self.config)
        self.ocr_processor = OCRProcessor(self.config)
        self.ai_handler = AIHandler(self.config)
        self.keyboard_sim = KeyboardSimulator()
        
        self.is_monitoring = False
        self.input_coords = (0, 0)  # 输入框坐标
        self.copy_area_region = (0, 0, 100, 30)   # 复制区域坐标
        self.monitoring_thread = None
        
        # 添加模式控制
        self.ocr_mode_enabled = True
        self.copy_area_mode_enabled = False
        
        # 添加复制区域模式相关属性
        self.last_copy_area_text = ""
        self.last_copy_area_time = 0
        self.copy_area_interval = 3  # 最小间隔时间3秒
        
        # 测试AI连接
        if self.ai_handler.test_connection():
            print("Ollama连接正常")
        else:
            print("警告: 无法连接到Ollama，请确保Ollama服务正在运行")
    
    def set_monitor_region(self, x, y, width, height):
        """设置监控区域"""
        self.screen_monitor.set_monitor_region(x, y, width, height)
    
    def set_input_coords(self, coords):
        """设置输入框坐标"""
        self.input_coords = coords
    
    def set_copy_area_region(self, region):
        """设置复制区域坐标"""
        self.copy_area_region = region
    
    def set_modes(self, ocr_enabled, copy_area_enabled):
        """设置监控模式"""
        self.ocr_mode_enabled = ocr_enabled
        self.copy_area_mode_enabled = copy_area_enabled
    
    def start_monitoring(self):
        """开始监控"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
    
    def is_likely_conversation_text(self, text):
        """判断是否为可能的对话文本 - 黑名单模式 + 对话内容白名单"""
        # 白名单：明确的对话内容
        whitelisted_patterns = [
            # 问候语
            r'你好', r'您好', r'早上好', r'下午好', r'晚上好', r'您好',
            # 祝福语
            r'恭喜发财', r'恭喜', r'生日快乐', r'新年快乐', r'新年好', r'节日快乐',
            r'恭喜你', r'恭喜了', r'发财', r'恭喜恭喜', r'祝你', r'祝福',
            # 情感表达
            r'爱', r'喜欢', r'讨厌', r'高兴', r'开心', r'难过', r'伤心', r'生气',
            # 感谢用语
            r'谢谢', r'感谢', r'感激', r'多谢',
            # 简单回应
            r'好', r'是', r'不', r'要', r'有', r'在', r'了', r'的',
            # 疑问句
            r'吗', r'呢', r'？', r'为什么', r'怎么', r'什么', r'谁', r'哪里', r'哪个',
            # 感叹句
            r'！', r'啊', r'呀', r'哇', r'哦', r'嗯', r'嗯嗯',
            # 互动用语
            r'说', r'讲', r'聊', r'话', r'聊天', r'说话',
            # 自我介绍相关
            r'介绍', r'自己', r'我叫', r'我是', r'介绍一下', r'介绍一下自己',
            # 求助用语
            r'求', r'求你', r'请', r'麻烦', r'帮', r'拜托',
            # 语气词
            r'吧', r'嘛', r'啦', r'呗', r'哈',
            # 意见表达
            r'可以', r'应该', r'会', r'希望', r'想要', r'需要',
            # 指示词
            r'今天', r'现在', r'这个', r'那个', r'这里', r'那里',
            # 单个字或简单词
            r'喵', r'呜', r'嗯', r'哦', r'啊', r'哈', r'哼', r'哦', r'嗯嗯',
        ]
        
        # 黑名单：明确的非对话内容
        blacklisted_patterns = [
            # 时间戳格式
            r'\d{1,2}:\d{2}',  # 12:34 格式
            r'\d{1,2}:\d{2}:\d{2}',  # 12:34:56 格式
            # 数字序列（可能是序号）
            r'\d{3,}',  # 3个以上连续数字
            # 用户标识
            r'@\w+',  # @username
            # 商品信息
            r'价格.*\d+',  # 价格相关
            r'¥\d+',  # 价格符号
            r'元$',  # 价格结尾
            # 界面元素
            r'设置', r'选项', r'菜单', r'文件', r'编辑', r'视图', r'帮助',
            r'新建', r'打开', r'保存', r'退出', r'取消', r'确定', r'是', r'否',
            r'应用', r'关闭', r'返回', r'下一页', r'上一页', r'前进',
            r'首页', r'搜索', r'筛选', r'排序', r'刷新', r'更新',
            r'安装', r'卸载', r'下载', r'上传', r'同步',
            r'登录', r'注销', r'注册', r'账户', r'个人资料',
            # 商品名称
            r'维生素', r'药品', r'商品', r'购买', r'优惠', r'促销',
            r'广告', r'推广', r'产品', r'品牌', r'规格', r'包装', r'成分',
            r'效果', r'功能', r'作用', r'说明', r'介绍', r'详情',
            # 系统信息
            r'系统', r'时间', r'日期', r'天气', r'状态', r'信息', r'关于',
            # 菜单项
            r'设置', r'选项', r'菜单', r'文件', r'编辑', r'查看', r'帮助',
        ]
        
        text_lower = text.lower()
        
        # 首先检查白名单
        for pattern in whitelisted_patterns:
            if re.search(pattern, text):
                return True
            if pattern in text:
                return True
            if pattern in text_lower:
                return True
        
        # 然后检查黑名单
        for pattern in blacklisted_patterns:
            if re.search(pattern, text):
                return False
            if pattern in text:
                return False
            if pattern in text_lower:
                return False
        
        # 检查文本是否过于混乱（字符种类太多但内容少）
        char_types = len(set(text))
        if len(text) > 0 and char_types / len(text) > 0.9 and len(text) < 8:
            # 如果字符种类占比过高且长度较短，可能是乱码
            return False
        
        # 检查是否包含中文字符（单个中文字符也视为对话内容）
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
        if chinese_chars > 0:
            return True
        
        # 除了黑名单内容，其他都视为对话内容
        return True
    
    def process_auto_copy_message(self, message):
        """处理自动复制的消息"""
        if self.is_monitoring:
            print(f"处理自动复制消息: {message}")
            
            # 检查是否是对话内容
            if self.is_likely_conversation_text(message):
                # 获取AI回复
                ai_response = self.ai_handler.get_ai_response(message)
                print(f"AI回复: {ai_response}")
                
                if ai_response and ai_response != "抱歉，暂时无法回复":
                    # 验证AI回复是否有意义
                    meaningful_response = len(ai_response) > 3 and len(re.findall(r'[\u4e00-\u9fa5a-zA-Z]{2,}', ai_response)) > 0
                    print(f"AI回复有意义: {meaningful_response}")
                    
                    if meaningful_response:
                        success = self.keyboard_sim.send_message(
                            ai_response, 
                            self.input_coords
                        )
                        
                        if success:
                            print(f"回复已发送: {ai_response}")
                            # 记录发送的消息，用于过滤
                            self.ocr_processor.record_sent_message(ai_response)
                        else:
                            print("发送失败")
                    else:
                        print(f"AI回复无意义，跳过发送: {ai_response}")
                else:
                    print(f"AI无法生成有效回复")
            else:
                print(f"自动复制内容不是对话内容: {message[:50]}...")
    
    def process_ocr_mode(self):
        """处理OCR模式"""
        print(f"开始检测屏幕变化...")
        
        # 捕获屏幕
        img = self.screen_monitor.capture_screen()
        if img is None:
            print("屏幕捕获失败")
            return
        
        print(f"屏幕捕获成功，图像尺寸: {img.shape}")
        
        # 检测屏幕变化
        has_changed = self.screen_monitor.detect_changes(img)
        print(f"屏幕变化检测: {has_changed}")
        
        if not has_changed:
            print("屏幕无变化，跳过OCR")
            return
        
        # OCR识别
        current_text = self.ocr_processor.extract_text(img)
        print(f"OCR识别结果: '{current_text}'")
        
        if current_text and len(current_text) >= self.config["monitoring"]["min_text_length"]:
            print(f"文本长度: {len(current_text)}, 满足最小长度要求")
            
            # 额外验证文本是否有意义
            if self.ocr_processor.is_meaningful_text(current_text):
                print(f"文本有意义，开始处理")
                
                # 检查是否是刚发送的回复（避免重复）
                if not self.ocr_processor.is_recent_reply(current_text):
                    # 额外检查：确保文本包含实际对话内容
                    if self.is_likely_conversation_text(current_text):
                        print(f"处理消息: {current_text}")
                        
                        # 获取AI回复
                        ai_response = self.ai_handler.get_ai_response(current_text)
                        print(f"AI回复: {ai_response}")
                        
                        if ai_response and ai_response != "抱歉，暂时无法回复":
                            # 验证AI回复是否有意义
                            meaningful_response = len(ai_response) > 3 and len(re.findall(r'[\u4e00-\u9fa5a-zA-Z]{2,}', ai_response)) > 0
                            print(f"AI回复有意义: {meaningful_response}")
                            
                            if meaningful_response:
                                success = self.keyboard_sim.send_message(
                                    ai_response, 
                                    self.input_coords
                                )
                                
                                if success:
                                    print(f"回复已发送: {ai_response}")
                                    # 记录发送的消息，用于过滤
                                    self.ocr_processor.record_sent_message(ai_response)
                                else:
                                    print("发送失败")
                            else:
                                print(f"AI回复无意义，跳过发送: {ai_response}")
                        else:
                            print(f"AI无法生成有效回复")
                    else:
                        print(f"文本不是对话内容，发送提示: {current_text[:50]}...")
                        # 发送提示信息
                        hint_response = "我只回复有意义的对话内容哦"
                        success = self.keyboard_sim.send_message(
                            hint_response, 
                            self.input_coords
                        )
                        if success:
                            print(f"提示已发送: {hint_response}")
                            self.ocr_processor.record_sent_message(hint_response)
                        else:
                            print("发送提示失败")
                else:
                    print(f"过滤掉刚发送的回复内容，跳过处理")
            else:
                print(f"OCR识别出乱码，发送提示: {current_text[:50]}...")
                # 发送乱码提示
                hint_response = "识别到乱码，无法回复"
                success = self.keyboard_sim.send_message(
                    hint_response, 
                    self.input_coords
                )
                if success:
                    print(f"乱码提示已发送: {hint_response}")
                    self.ocr_processor.record_sent_message(hint_response)
                else:
                    print("发送乱码提示失败")

    def process_copy_area_mode(self):
        """处理复制区域模式 - 直接处理所有内容"""
        import pyautogui
        import re
        import time
        import pyperclip
        
        try:
            # 获取复制区域的坐标
            x, y, width, height = self.copy_area_region
            
            # 点击区域中心，确保焦点在该区域
            pyautogui.click(x + width // 2, y + height // 2)
            time.sleep(0.1)  # 等待点击生效
            
            # 模拟三击选择整行文本（适用于聊天应用）
            pyautogui.click(x + width // 2, y + height // 2)
            time.sleep(0.05)
            pyautogui.click(x + width // 2, y + height // 2)
            time.sleep(0.05)
            pyautogui.click(x + width // 2, y + height // 2)
            time.sleep(0.1)  # 等待选择完成
            
            # 复制选中的文本
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.1)  # 等待复制完成
            
            # 获取剪贴板内容
            current_text = pyperclip.paste().strip()
            
            # 检查是否为AI回复内容（避免处理自己的回复）
            ai_response_indicators = [
                '我只回复有意义的对话内容哦',
                '识别到乱码，无法回复',
                '<think>',
                'AI回复',
                '回复已发送',
                '准备发送消息'
            ]
            
            is_ai_response = any(indicator in current_text for indicator in ai_response_indicators)
            if is_ai_response:
                return  # 跳过AI回复内容
            
            # 检查是否内容发生变化且时间间隔足够
            current_time = time.time()
            if (current_text != self.last_copy_area_text and 
                current_text.strip() and 
                current_time - self.last_copy_area_time > self.copy_area_interval):
                
                # 更新最后处理的时间和内容
                self.last_copy_area_text = current_text
                self.last_copy_area_time = current_time
                
                # 检查是否是对话内容（避免复制其他内容）
                if len(current_text.strip()) > 1 and re.search(r'[\u4e00-\u9fa5a-zA-Z]', current_text):
                    print(f"自动区域复制识别到: {current_text[:50]}...")
                    
                    # 直接处理，不再检查是否为对话内容
                    print(f"处理自动区域复制消息: {current_text}")
                    
                    # 获取AI回复
                    ai_response = self.ai_handler.get_ai_response(current_text)
                    print(f"AI回复: {ai_response}")
                    
                    if ai_response and ai_response != "抱歉，暂时无法回复":
                        # 验证AI回复是否有意义
                        meaningful_response = len(ai_response) > 3 and len(re.findall(r'[\u4e00-\u9fa5a-zA-Z]{2,}', ai_response)) > 0
                        print(f"AI回复有意义: {meaningful_response}")
                        
                        if meaningful_response:
                            success = self.keyboard_sim.send_message(
                                ai_response, 
                                self.input_coords
                            )
                            
                            if success:
                                print(f"回复已发送: {ai_response}")
                                # 记录发送的消息，用于过滤
                                self.ocr_processor.record_sent_message(ai_response)
                            else:
                                print("发送失败")
                        else:
                            print(f"AI回复无意义，跳过发送: {ai_response}")
                    else:
                        print(f"AI无法生成有效回复")
        except Exception as e:
            print(f"自动区域复制模式错误: {e}")
    
    def monitor_loop(self):
        """监控循环 - 增强版，支持多模式"""
        while self.is_monitoring:
            try:
                # 根据启用的模式进行不同的处理
                if self.ocr_mode_enabled:
                    self.process_ocr_mode()
                
                if self.copy_area_mode_enabled:
                    self.process_copy_area_mode()
                
                time.sleep(self.config["monitoring"]["interval"])
                
            except Exception as e:
                print(f"监控循环错误: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(2)

def main():
    # 创建截图目录
    os.makedirs('screenshots', exist_ok=True)
    
    # 创建自动化系统
    automation_system = ChatAutomationSystem()
    
    # 创建Qt应用
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = GUIApp(automation_system)
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()