# modules/ocr_processor.py
import pytesseract
import cv2
import numpy as np
from PIL import Image
import re
import time

class OCRProcessor:
    def __init__(self, config):
        self.config = config
        # 设置Tesseract路径
        if config['paths']['tesseract_path']:
            pytesseract.pytesseract.tesseract_cmd = config['paths']['tesseract_path']
        
        # 添加回复过滤机制
        self.last_sent_message = ""
        self.last_sent_time = 0
        self.reply_filter_duration = 5  # 5秒内过滤回复内容
    
    def preprocess_image(self, img):
        """优化的图像预处理 - 针对字符识别优化"""
        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 增强对比度
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # 高斯模糊去噪（轻微）
        blurred = cv2.GaussianBlur(enhanced, (1, 1), 0)
        
        # 二值化 - 使用更精确的阈值
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 调整对比度和亮度
        final = cv2.convertScaleAbs(thresh, alpha=1.3, beta=10)
        
        return final
    
    def correct_common_ocr_errors(self, text):
        """纠正常见的OCR识别错误"""
        # 创建一个副本用于修改
        corrected_text = text
        
        # 常见的OCR错误映射
        corrections = {
            # 字符错误
            '0': '口',  # 0 -> 口
            'l': '1',   # l -> 1
            'I': '1',   # I -> 1
            'S': '5',   # S -> 5
            'Z': '2',   # Z -> 2
            'B': '8',   # B -> 8
            'O': '口',  # O -> 口
        }
        
        # 应用字符纠正
        for wrong, correct in corrections.items():
            corrected_text = corrected_text.replace(wrong, correct)
        
        # 常见词汇纠正
        word_corrections = {
            'l口': '口',  # "1口" -> "口"
            '0口': '口',  # "0口" -> "口"
            'O口': '口',  # "O口" -> "口"
            'l了': '了',  # "1了" -> "了"
            '0了': '了',  # "0了" -> "了"
            'O了': '了',  # "O了" -> "了"
            'l的': '的',  # "1的" -> "的"
            '0的': '的',  # "0的" -> "的"
            'O的': '的',  # "O的" -> "的"
        }
        
        for wrong, correct in word_corrections.items():
            corrected_text = corrected_text.replace(wrong, correct)
        
        return corrected_text
    
    def calculate_text_quality(self, text):
        """计算文本质量分数 - 字符级优化"""
        if not text.strip():
            return 0
        
        # 中文字符数量
        chinese_count = len(re.findall(r'[\u4e00-\u9fa5]', text))
        # 英文单词数量（2个字母以上）
        english_count = len(re.findall(r'[a-zA-Z]{2,}', text))
        # 数字组数量
        number_count = len(re.findall(r'[0-9]{2,}', text))
        # 标点符号数量
        punct_count = len(re.findall(r'[，。！？；：、\.,!?;:]', text))
        
        # 重复字符检测
        unique_chars = len(set(text))
        repeat_ratio = 1 - (unique_chars / len(text)) if len(text) > 0 else 0
        
        # OCR乱码检测
        ocr_noise_score = 0
        text_upper = text.upper()
        ocr_noise_patterns = [
            r'[A-Z]{3,}\s*[A-Z]{2,}',  # 大写字母组合，如 RAIN OO
            r'[A-Z]{2,}\s*[0-9]{2,}',  # 字母+数字，如 ABC123
            r'[0-9]{2,}\s*[A-Z]{2,}',  # 数字+字母，如 123ABC
            r'[A-Z]{1,2}\s*[A-Z]{1,2}',  # 短字母组合，如 A B
        ]
        
        for pattern in ocr_noise_patterns:
            if re.search(pattern, text_upper):
                meaningful_parts = [
                    'HELLO', 'THANK', 'PLEASE', 'HELP', 'YES', 'NO', 'OK', 'GOOD', 'BAD', 'WELL', 'TIME'
                ]
                has_meaningful = any(part in text_upper for part in meaningful_parts)
                if not has_meaningful:
                    ocr_noise_score = 10  # OCR乱码惩罚
        
        # 字符清晰度评分（基于字符的可读性）
        clarity_score = 0
        for char in text:
            # 检查字符是否是常见OCR错误
            if char in ['O', 'l', 'I', 'S', 'Z', 'B']:
                clarity_score += 0.5  # 稍微降低分数
            elif char in ['0', '1', '2', '5', '8']:
                clarity_score += 0.3  # 稍微降低分数
            else:
                clarity_score += 1  # 正常字符
        
        clarity_score = clarity_score / len(text) if len(text) > 0 else 0
        
        # 质量分数计算
        quality_score = (
            chinese_count * 3 +      # 中文字符权重较高
            english_count * 2 +      # 英文单词
            number_count * 1 +       # 数字
            punct_count * 1 +        # 标点
            clarity_score * 10 -     # 字符清晰度
            repeat_ratio * 20 -      # 重复字符惩罚
            ocr_noise_score * 5      # OCR乱码惩罚
        )
        
        return quality_score
    
    def extract_text_multiple_methods(self, img):
        """使用多种方法和多次识别提取文本 - 字符级优化"""
        # 预处理图像
        processed_img = self.preprocess_image(img)
        
        # 多种配置尝试
        configs = [
            '--psm 6 -l chi_sim+eng',  # 默认配置
            '--psm 7 -l chi_sim+eng',  # 单行文本
            '--psm 8 -l chi_sim+eng',  # 单词
            '--psm 13 -l chi_sim+eng', # 纯文字行
            '--psm 10 -l chi_sim+eng', # 单个字符
        ]
        
        all_results = []
        
        # 对每种配置进行多次识别
        for config in configs:
            for attempt in range(5):  # 增加到5次识别
                try:
                    text = pytesseract.image_to_string(processed_img, config=config)
                    if text.strip():
                        all_results.append(text.strip())
                except:
                    continue
        
        # 过滤和排序结果
        meaningful_results = []
        for result in all_results:
            if self.is_meaningful_text(result):
                # 计算质量分数
                quality_score = self.calculate_text_quality(result)
                meaningful_results.append((result, quality_score))
        
        if meaningful_results:
            # 返回质量分数最高的结果
            best_result = max(meaningful_results, key=lambda x: x[1])
            return best_result[0]
        
        return ""
    
    def extract_text(self, img):
        """从图像中提取文字 - 多次识别版"""
        try:
            # 使用多种方法和多次识别提取
            text = self.extract_text_multiple_methods(img)
            
            # 纠正常见OCR错误
            corrected_text = self.correct_common_ocr_errors(text)
            
            # 清理文本 - 保持简单
            cleaned_text = self.clean_text(corrected_text)
            
            if cleaned_text and self.is_meaningful_text(cleaned_text):
                # 检查是否是刚发送的回复（避免重复识别）
                if self.is_recent_reply(cleaned_text):
                    print(f"过滤掉刚发送的回复内容: {cleaned_text[:30]}...")
                    return ""
                return cleaned_text.strip()
            else:
                return ""
                
        except Exception as e:
            print(f"OCR处理失败: {e}")
            return ""
    
    def clean_text(self, text):
        """简单清理OCR结果"""
        if not text.strip():
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除过多的重复字符
        text = re.sub(r'(.)\1{4,}', r'\1\1', text)  # 将连续5个以上相同字符变为2个
        
        # 只保留有意义的字符
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\.,!?;:，。！？；：\-_@#&\(\)]', '', text)
        
        # 移除过多的空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def is_meaningful_text(self, text):
        """判断文本是否有意义 - 增强乱码检测"""
        if not text or len(text.strip()) < 1:
            return False
        
        # 检查中文字符数量
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
        # 检查英文单词数量（至少2个字母）
        english_words = len(re.findall(r'[a-zA-Z]{2,}', text))
        # 检查数字组数量（至少2个数字）
        numbers = len(re.findall(r'[0-9]{2,}', text))
        
        # 检查是否包含对话特征
        conversation_indicators = ['：', ':', '？', '?', '！', '!', '。', '.', '，', ',']
        has_indicators = any(indicator in text for indicator in conversation_indicators)
        
        # 检查重复字符比例（避免乱码）
        if len(text) > 0:
            unique_chars = len(set(text))
            repeat_ratio = 1 - (unique_chars / len(text))
            if repeat_ratio > 0.8:  # 如果80%以上是重复字符，认为是乱码
                return False
        
        # 检查是否包含常见乱码特征
        garbage_patterns = [
            r'[^\u4e00-\u9fa5a-zA-Z0-9\s\.,!?;:，。！？；：\-_@#&\(\)\[\]{}]',  # 乱码字符
            r'(\w)\1{8,}',  # 连续重复字符
        ]
        
        for pattern in garbage_patterns:
            if len(re.findall(pattern, text)) > 1:  # 如果有多个乱码模式
                return False
        
        # 专门检测OCR乱码模式：字母和数字的奇怪组合
        # 例如：RAIN OO, ABC123, XYZ999 等
        ocr_noise_patterns = [
            r'[A-Z]{3,}\s*[A-Z]{2,}',  # 大写字母组合，如 RAIN OO
            r'[A-Z]{2,}\s*[0-9]{2,}',  # 字母+数字，如 ABC123
            r'[0-9]{2,}\s*[A-Z]{2,}',  # 数字+字母，如 123ABC
            r'[A-Z]{1,2}\s*[A-Z]{1,2}',  # 短字母组合，如 A B
        ]
        
        text_upper = text.upper()
        for pattern in ocr_noise_patterns:
            if re.search(pattern, text_upper):
                # 检查这些模式是否包含有意义的词汇
                meaningful_parts = [
                    'HELLO', 'THANK', 'PLEASE', 'HELP', 'YES', 'NO', 'OK', 'GOOD', 'BAD', 'WELL', 'TIME'
                ]
                has_meaningful = any(part in text_upper for part in meaningful_parts)
                if not has_meaningful:
                    return False  # 确认是OCR乱码
        
        # 检查是否是常见的界面元素（如按钮、菜单等）
        interface_elements = [
            'settings', 'options', 'menu', 'file', 'edit', 'view', 'help',
            'new', 'open', 'save', 'exit', 'cancel', 'ok', 'yes', 'no',
            'apply', 'close', 'back', 'next', 'previous', 'forward',
            'home', 'search', 'filter', 'sort', 'refresh', 'update',
            'install', 'uninstall', 'download', 'upload', 'sync',
            'login', 'logout', 'register', 'account', 'profile',
            'message', 'chat', 'contact', 'group', 'room',
            'time', 'date', 'weather', 'status', 'info', 'about'
        ]
        text_lower = text.lower()
        is_interface = any(element in text_lower for element in interface_elements)
        if is_interface:
            return False
        
        # 判断标准：有中文字符，或者有意义的英文单词，或者包含对话特征
        return (chinese_chars >= 1 or english_words >= 1 or has_indicators) and len(text) >= 1
    
    def record_sent_message(self, message):
        """记录发送的消息，用于过滤"""
        self.last_sent_message = message
        self.last_sent_time = time.time()
    
    def is_recent_reply(self, text):
        """检查文本是否是最近发送的回复"""
        if not self.last_sent_message:
            return False
        
        # 检查时间是否在过滤时间内
        if time.time() - self.last_sent_time > self.reply_filter_duration:
            return False
        
        # 检查文本是否包含最近发送的消息内容
        # 使用模糊匹配，避免完全相等的严格要求
        text_lower = text.lower()
        sent_lower = self.last_sent_message.lower()
        
        # 检查发送的消息是否在识别到的文本中
        if sent_lower in text_lower:
            return True
        
        # 检查识别到的文本是否在发送的消息中（可能只是部分识别）
        if text_lower in sent_lower:
            return True
        
        return False