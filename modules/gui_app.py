# modules/gui_app.py
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                            QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTextEdit, QLabel, QLineEdit, QSpinBox,
                            QGroupBox, QFormLayout, QCheckBox)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QThread, Qt
import time
import threading
import cv2
import numpy as np
import tempfile
import os

class KeyboardMonitorThread(QThread):
    """键盘监控线程"""
    key_pressed_signal = pyqtSignal(str)  # 'enter' only
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.monitoring = False
    
    def run(self):
        import keyboard
        while self.running:
            if self.monitoring:
                if keyboard.is_pressed('enter'):
                    self.key_pressed_signal.emit('enter')
                    time.sleep(0.3)  # 防止重复触发
            time.sleep(0.01)
    
    def start_monitoring(self):
        self.monitoring = True
    
    def stop_monitoring(self):
        self.monitoring = False
    
    def stop_thread(self):
        self.running = False

class CoordinateCaptureThread(QThread):
    """坐标捕获线程"""
    coordinate_signal = pyqtSignal(int, int)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.capturing = False
    
    def run(self):
        import pyautogui
        while self.running:
            if self.capturing:
                try:
                    x, y = pyautogui.position()
                    self.coordinate_signal.emit(x, y)
                    time.sleep(0.1)  # 每0.1秒更新一次
                except:
                    pass
            time.sleep(0.01)
    
    def start_capture(self):
        self.capturing = True
    
    def stop_capture(self):
        self.capturing = False
    
    def stop_thread(self):
        self.running = False

class GUIApp(QMainWindow):
    log_signal = pyqtSignal(str)
    
    def __init__(self, automation_system):
        super().__init__()
        self.automation_system = automation_system
        
        # 添加模式控制相关属性
        self.ocr_mode_enabled = True  # OCR模式是否启用
        self.copy_area_mode_enabled = False  # 复制区域模式是否启用
        
        # 初始化线程
        self.coordinate_thread = CoordinateCaptureThread()
        self.keyboard_thread = KeyboardMonitorThread()
        
        # 连接信号
        self.coordinate_thread.coordinate_signal.connect(self.update_coordinates)
        self.keyboard_thread.key_pressed_signal.connect(self.handle_key_press)
        self.log_signal.connect(self._update_log)
        
        # 启动线程
        self.coordinate_thread.running = True
        self.coordinate_thread.start()
        self.keyboard_thread.running = True
        self.keyboard_thread.start()
        
        # 添加坐标捕获相关属性
        self.waiting_for_monitor_corner = False
        self.waiting_for_first_corner = False
        self.waiting_for_input_coord = False
        self.waiting_for_copy_area = False  # 添加复制区域捕获状态
        self.temp_x1 = 0
        self.temp_y1 = 0
        
        self.init_ui()  # 先初始化UI组件
        
        # 然后加载保存的坐标（此时UI组件已存在）
        self.load_saved_coordinates()
        
        self.setup_connections()
    
    def load_saved_coordinates(self):
        """加载上次保存的坐标"""
        import json
        import os
        
        config_file = 'user_config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 加载监控区域坐标
                region = config.get('monitoring', {}).get('region', {})
                if region:
                    self.x_spin.setValue(region.get('x', 496))
                    self.y_spin.setValue(region.get('y', 1012))
                    self.w_spin.setValue(region.get('width', 1010))
                    self.h_spin.setValue(region.get('height', 88))
                
                # 加载输入框坐标
                input_coords = config.get('monitoring', {}).get('input_coords', {})
                if input_coords:
                    self.input_x.setValue(input_coords.get('x', 200))
                    self.input_y.setValue(input_coords.get('y', 750))
                
                # 加载复制区域坐标
                copy_area_coords = config.get('monitoring', {}).get('copy_area_coords', {})
                if copy_area_coords:
                    self.copy_area_x.setValue(copy_area_coords.get('x', 500))
                    self.copy_area_y.setValue(copy_area_coords.get('y', 1000))
                    self.copy_area_w.setValue(copy_area_coords.get('width', 200))
                    self.copy_area_h.setValue(copy_area_coords.get('height', 50))
                    
            except Exception as e:
                print(f"加载坐标失败: {e}")
    
    def save_coordinates(self):
        """保存当前坐标到配置文件"""
        import json
        import os
        
        # 读取现有配置
        config_file = 'user_config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                config = {}
        else:
            config = {}
        
        # 更新监控区域配置
        if 'monitoring' not in config:
            config['monitoring'] = {}
        
        config['monitoring']['region'] = {
            'x': self.x_spin.value(),
            'y': self.y_spin.value(),
            'width': self.w_spin.value(),
            'height': self.h_spin.value()
        }
        
        config['monitoring']['input_coords'] = {
            'x': self.input_x.value(),
            'y': self.input_y.value()
        }
        
        config['monitoring']['copy_area_coords'] = {
            'x': self.copy_area_x.value(),
            'y': self.copy_area_y.value(),
            'width': self.copy_area_w.value(),
            'height': self.copy_area_h.value()
        }
        
        # 保存配置
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            print("坐标已保存到 user_config.json")
        except Exception as e:
            print(f"保存坐标失败: {e}")
    
    def init_ui(self):
        self.setWindowTitle("聊天自动化监控系统")
        self.setGeometry(100, 100, 900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 监控区域设置
        control_group = QGroupBox("监控设置")
        control_layout = QFormLayout()
        
        # 屏幕区域设置
        region_layout = QHBoxLayout()
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 3840)
        self.x_spin.setValue(496)
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 2160)
        self.y_spin.setValue(1012)
        self.w_spin = QSpinBox()
        self.w_spin.setRange(100, 1920)
        self.w_spin.setValue(1010)
        self.h_spin = QSpinBox()
        self.h_spin.setRange(100, 1080)
        self.h_spin.setValue(88)
        
        region_layout.addWidget(QLabel("X:"))
        region_layout.addWidget(self.x_spin)
        region_layout.addWidget(QLabel("Y:"))
        region_layout.addWidget(self.y_spin)
        region_layout.addWidget(QLabel("W:"))
        region_layout.addWidget(self.w_spin)
        region_layout.addWidget(QLabel("H:"))
        region_layout.addWidget(self.h_spin)
        
        control_layout.addRow("监控区域:", region_layout)
        
        # 添加坐标捕获功能
        coord_capture_layout = QHBoxLayout()
        self.capture_monitor_btn = QPushButton("点击获取监控区域坐标")
        self.capture_monitor_btn.setToolTip("点击后移动鼠标到监控区域左上角，然后右下角")
        coord_capture_layout.addWidget(self.capture_monitor_btn)
        
        # 添加提示标签
        self.coord_hint_label = QLabel("提示: 点击按钮后，移动鼠标到目标位置，然后按回车键确认")
        self.coord_hint_label.setStyleSheet("color: blue;")
        coord_capture_layout.addWidget(self.coord_hint_label)
        
        control_layout.addRow("坐标获取:", coord_capture_layout)
        
        # 输入框坐标设置
        input_layout = QHBoxLayout()
        self.input_x = QSpinBox()
        self.input_x.setRange(0, 3840)
        self.input_x.setValue(200)
        self.input_y = QSpinBox()
        self.input_y.setRange(0, 2160)
        self.input_y.setValue(750)
        input_layout.addWidget(QLabel("X:"))
        input_layout.addWidget(self.input_x)
        input_layout.addWidget(QLabel("Y:"))
        input_layout.addWidget(self.input_y)
        
        input_coord_layout = QHBoxLayout()
        input_coord_layout.addLayout(input_layout)
        self.capture_input_btn = QPushButton("点击获取输入框坐标")
        self.capture_input_btn.setToolTip("点击后移动鼠标到输入框位置")
        input_coord_layout.addWidget(self.capture_input_btn)
        
        control_layout.addRow("输入框坐标:", input_coord_layout)
        
        # 复制区域设置
        copy_area_layout = QHBoxLayout()
        self.copy_area_x = QSpinBox()
        self.copy_area_x.setRange(0, 3840)
        self.copy_area_x.setValue(500)
        self.copy_area_y = QSpinBox()
        self.copy_area_y.setRange(0, 2160)
        self.copy_area_y.setValue(1000)
        self.copy_area_w = QSpinBox()
        self.copy_area_w.setRange(50, 1920)
        self.copy_area_w.setValue(200)
        self.copy_area_h = QSpinBox()
        self.copy_area_h.setRange(20, 1080)
        self.copy_area_h.setValue(50)
        
        copy_area_layout.addWidget(QLabel("X:"))
        copy_area_layout.addWidget(self.copy_area_x)
        copy_area_layout.addWidget(QLabel("Y:"))
        copy_area_layout.addWidget(self.copy_area_y)
        copy_area_layout.addWidget(QLabel("W:"))
        copy_area_layout.addWidget(self.copy_area_w)
        copy_area_layout.addWidget(QLabel("H:"))
        copy_area_layout.addWidget(self.copy_area_h)
        
        copy_area_coord_layout = QHBoxLayout()
        copy_area_coord_layout.addLayout(copy_area_layout)
        self.capture_copy_area_btn = QPushButton("点击获取复制区域坐标")
        self.capture_copy_area_btn.setToolTip("点击后移动鼠标到复制区域左上角，然后右下角")
        copy_area_coord_layout.addWidget(self.capture_copy_area_btn)
        
        control_layout.addRow("复制区域坐标:", copy_area_coord_layout)
        
        # 模式选择
        mode_layout = QHBoxLayout()
        self.ocr_mode_checkbox = QCheckBox("启用OCR模式")
        self.ocr_mode_checkbox.setToolTip("启用屏幕监控和OCR识别")
        self.ocr_mode_checkbox.setChecked(True)  # 默认启用
        self.ocr_mode_checkbox.stateChanged.connect(self.toggle_ocr_mode)
        mode_layout.addWidget(self.ocr_mode_checkbox)
        
        self.copy_area_mode_checkbox = QCheckBox("启用复制区域模式")
        self.copy_area_mode_checkbox.setToolTip("启用自动区域复制识别")
        self.copy_area_mode_checkbox.setChecked(False)  # 默认不启用
        self.copy_area_mode_checkbox.stateChanged.connect(self.toggle_copy_area_mode)
        mode_layout.addWidget(self.copy_area_mode_checkbox)
        
        control_layout.addRow("监控模式:", mode_layout)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始监控")
        self.stop_btn = QPushButton("停止监控")
        self.test_btn = QPushButton("测试OCR")
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.test_btn)
        control_layout.addRow("控制:", button_layout)
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # 日志显示区域
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(300)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def setup_connections(self):
        self.start_btn.clicked.connect(self.start_monitoring)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.test_btn.clicked.connect(self.test_ocr)
        self.capture_monitor_btn.clicked.connect(self.start_capture_monitor)
        self.capture_input_btn.clicked.connect(self.start_capture_input)
        self.capture_copy_area_btn.clicked.connect(self.start_capture_copy_area)  # 添加复制区域坐标捕获
    
    def handle_key_press(self, key_type):
        """处理键盘按键 - 只处理回车键"""
        if self.waiting_for_monitor_corner or self.waiting_for_input_coord or self.waiting_for_copy_area:
            # 都使用回车键确认
            if self.waiting_for_monitor_corner:
                self.confirm_monitor_coordinate()
            elif self.waiting_for_input_coord:
                self.confirm_input_coordinate()
            elif self.waiting_for_copy_area:  # 添加复制区域确认处理
                self.confirm_copy_area_coordinate()
    
    def start_capture_monitor(self):
        """开始捕获监控区域坐标"""
        self.statusBar().showMessage("移动鼠标到监控区域左上角，按回车键确认...")
        self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 请移动鼠标到监控区域左上角，按回车键确认")
        
        # 开始坐标捕获
        self.coordinate_thread.start_capture()
        self.keyboard_thread.start_monitoring()
        self.waiting_for_monitor_corner = True
        self.waiting_for_first_corner = True  # 标记是左上角还是右下角
        self.temp_x1 = 0
        self.temp_y1 = 0
    
    def start_capture_input(self):
        """开始捕获输入框坐标"""
        self.statusBar().showMessage("移动鼠标到输入框位置，按回车键确认...")
        self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 请移动鼠标到输入框位置，按回车键确认")
        
        # 开始坐标捕获
        self.coordinate_thread.start_capture()
        self.keyboard_thread.start_monitoring()
        self.waiting_for_input_coord = True
    
    def start_capture_copy_area(self):
        """开始捕获复制区域坐标"""
        self.statusBar().showMessage("移动鼠标到复制区域左上角，按回车键确认...")
        self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 请移动鼠标到复制区域左上角，按回车键确认")
        
        # 开始坐标捕获
        self.coordinate_thread.start_capture()
        self.keyboard_thread.start_monitoring()
        self.waiting_for_copy_area = True
        self.waiting_for_first_corner = True  # 标记是左上角还是右下角
        self.temp_x1 = 0
        self.temp_y1 = 0
    
    def confirm_monitor_coordinate(self):
        """确认监控区域坐标"""
        import pyautogui
        x, y = pyautogui.position()
        
        # 不进行任何缩放转换，直接使用实际鼠标位置
        if self.waiting_for_first_corner:  # 左上角
            self.temp_x1, self.temp_y1 = x, y
            self.waiting_for_first_corner = False
            self.statusBar().showMessage("移动鼠标到监控区域右下角，按回车键确认...")
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 左上角坐标: ({x}, {y})")
        else:  # 右下角
            x2, y2 = x, y
            width = x2 - self.temp_x1
            height = y2 - self.temp_y1
            
            # 设置坐标
            self.x_spin.setValue(self.temp_x1)
            self.y_spin.setValue(self.temp_y1)
            self.w_spin.setValue(width)
            self.h_spin.setValue(height)
            
            self.statusBar().showMessage(f"监控区域已设置: ({self.temp_x1}, {self.temp_y1}, {width}, {height})")
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 右下角坐标: ({x2}, {y2})")
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 监控区域已设置: ({self.temp_x1}, {self.temp_y1}, {width}, {height})")
            
            self.waiting_for_monitor_corner = False
            self.coordinate_thread.stop_capture()
            self.keyboard_thread.stop_monitoring()
    
    def confirm_input_coordinate(self):
        """确认输入框坐标"""
        import pyautogui
        x, y = pyautogui.position()
        
        # 不进行任何缩放转换，直接使用实际鼠标位置
        # 设置输入框坐标
        self.input_x.setValue(x)
        self.input_y.setValue(y)
        
        self.statusBar().showMessage(f"输入框坐标已设置: ({x}, {y})")
        self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 输入框坐标已设置: ({x}, {y})")
        
        self.waiting_for_input_coord = False
        self.coordinate_thread.stop_capture()
        self.keyboard_thread.stop_monitoring()
    
    def confirm_copy_area_coordinate(self):
        """确认复制区域坐标"""
        import pyautogui
        x, y = pyautogui.position()
        
        # 不进行任何缩放转换，直接使用实际鼠标位置
        if self.waiting_for_first_corner:  # 左上角
            self.temp_x1, self.temp_y1 = x, y
            self.waiting_for_first_corner = False
            self.statusBar().showMessage("移动鼠标到复制区域右下角，按回车键确认...")
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 左上角坐标: ({x}, {y})")
        else:  # 右下角
            x2, y2 = x, y
            width = x2 - self.temp_x1
            height = y2 - self.temp_y1
            
            # 设置坐标
            self.copy_area_x.setValue(self.temp_x1)
            self.copy_area_y.setValue(self.temp_y1)
            self.copy_area_w.setValue(width)
            self.copy_area_h.setValue(height)
            
            self.statusBar().showMessage(f"复制区域已设置: ({self.temp_x1}, {self.temp_y1}, {width}, {height})")
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 右下角坐标: ({x2}, {y2})")
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 复制区域已设置: ({self.temp_x1}, {self.temp_y1}, {width}, {height})")
            
            self.waiting_for_copy_area = False
            self.coordinate_thread.stop_capture()
            self.keyboard_thread.stop_monitoring()
    
    def toggle_ocr_mode(self, state):
        """切换OCR模式"""
        self.ocr_mode_enabled = state == Qt.Checked
        if self.ocr_mode_enabled:
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] OCR模式已启用")
        else:
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] OCR模式已禁用")
    
    def toggle_copy_area_mode(self, state):
        """切换复制区域模式"""
        self.copy_area_mode_enabled = state == Qt.Checked
        if self.copy_area_mode_enabled:
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 复制区域模式已启用")
        else:
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 复制区域模式已禁用")
    
    def update_coordinates(self, x, y):
        """更新坐标显示（实时显示当前鼠标位置）"""
        if self.waiting_for_monitor_corner or self.waiting_for_input_coord or self.waiting_for_copy_area:
            # 显示实际坐标（不进行缩放转换）
            self.statusBar().showMessage(f"当前鼠标位置: X={x}, Y={y} (按回车键确认)")
    
    def start_monitoring(self):
        """开始监控"""
        # 设置监控区域
        region = (
            self.x_spin.value(),
            self.y_spin.value(),
            self.w_spin.value(),
            self.h_spin.value()
        )
        self.automation_system.set_monitor_region(*region)
        
        # 设置输入框坐标
        input_coords = (self.input_x.value(), self.input_y.value())
        self.automation_system.set_input_coords(input_coords)
        
        # 设置复制区域坐标
        copy_area_region = (
            self.copy_area_x.value(),
            self.copy_area_y.value(),
            self.copy_area_w.value(),
            self.copy_area_h.value()
        )
        self.automation_system.set_copy_area_region(copy_area_region)
        
        # 设置模式状态
        self.automation_system.set_modes(
            ocr_enabled=self.ocr_mode_enabled,
            copy_area_enabled=self.copy_area_mode_enabled
        )
        
        # 保存当前坐标
        self.save_coordinates()
        
        # 开始监控
        self.automation_system.start_monitoring()
        self.statusBar().showMessage("监控中...")
        self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 开始监控区域: {region}")
        
        # 显示启用的模式
        modes = []
        if self.ocr_mode_enabled:
            modes.append("OCR模式")
        if self.copy_area_mode_enabled:
            modes.append("复制区域模式")
        self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 启用模式: {', '.join(modes)}")
    
    def stop_monitoring(self):
        """停止监控"""
        self.automation_system.stop_monitoring()
        self.statusBar().showMessage("已停止")
        self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 监控已停止")
    
    def test_ocr(self):
        """测试OCR功能 - 全屏截图预览"""
        import cv2
        import numpy as np
        import tempfile
        import os
        
        # 获取屏幕尺寸
        import pyautogui
        screen_width, screen_height = pyautogui.size()
        region = (0, 0, screen_width, screen_height)  # 全屏
        
        self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 开始全屏OCR测试，区域: {region}")
        
        try:
            # 捕获全屏
            screenshot = pyautogui.screenshot()
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            if img is not None:
                # OCR识别（全屏可能很慢，我们只在监控区域测试）
                # 先截取当前监控区域进行OCR测试
                monitor_region = (
                    self.x_spin.value(),
                    self.y_spin.value(),
                    self.w_spin.value(),
                    self.h_spin.value()
                )
                
                # 在全屏截图上标记监控区域
                x, y, w, h = monitor_region
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 3)  # 绿色矩形框
                
                # 添加文字说明
                cv2.putText(img, 'OCR Test - Full Screen', (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(img, f'Monitor Region: ({x}, {y}, {w}, {h})', (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                # 对监控区域进行OCR测试
                monitor_screenshot = pyautogui.screenshot(region=monitor_region)
                monitor_img = cv2.cvtColor(np.array(monitor_screenshot), cv2.COLOR_RGB2BGR)
                text = self.automation_system.ocr_processor.extract_text(monitor_img)
                
                # 在全屏上显示OCR结果
                result_text = f'OCR Result: {text[:100]}...' if text else 'OCR Result: None'
                cv2.putText(img, result_text, (50, screen_height-50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
                
                # 保存临时文件并显示
                temp_file = os.path.join(tempfile.gettempdir(), f'full_ocr_test_{int(time.time())}.png')
                cv2.imwrite(temp_file, img)
                
                # 使用系统默认图片查看器打开
                os.startfile(temp_file)
                
                self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 监控区域OCR测试结果: {text}")
                print(f"监控区域OCR测试结果: {text}")
                self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 全屏OCR测试截图已保存并打开: {temp_file}")
                
            else:
                self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] OCR测试失败: 无法捕获屏幕")
                
        except Exception as e:
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] OCR测试出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_log(self, message):
        """更新日志 - 从其他线程调用时使用信号"""
        self.log_signal.emit(message)
    
    def _update_log(self, message):
        """实际的日志更新方法 - 在主线程中执行"""
        self.log_text.append(message)
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 保存当前坐标
        self.save_coordinates()
        self.coordinate_thread.stop_thread()
        self.keyboard_thread.stop_thread()
        self.coordinate_thread.wait()
        self.keyboard_thread.wait()
        event.accept()