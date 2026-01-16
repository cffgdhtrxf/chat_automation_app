# gui/gui_app.py
import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox, QSlider, QComboBox,
    QMessageBox, QTabWidget, QCheckBox, QStatusBar, QRadioButton
)
from PyQt5.QtCore import Qt, QThread, QMutex, QTimer
from PyQt5.QtGui import QIntValidator

import requests

class ModelListWorker(QThread):
    def __init__(self, host_url):
        super().__init__()
        self.host_url = host_url
        self.models = []

    def run(self):
        try:
            response = requests.get(f"{self.host_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                self.models = [model['name'] for model in data.get('models', [])]
        except Exception as e:
            print(f"获取模型列表失败: {e}")

from modules.config_loader import ConfigLoader

class GUIApp(QMainWindow):
    def __init__(self, automation_app=None):
        super().__init__()
        self.automation_app = automation_app
        # ConfigLoader在初始化时已经加载了配置文件
        self.config = ConfigLoader('user_config.json')
        self.init_ui()
        self.setup_auto_save()
        self.setup_logging()
        self.load_last_used_model()
        
        # 使用定时器在UI初始化完成后自动刷新模型列表
        QTimer.singleShot(100, self.auto_refresh_models)

    def load_last_used_model(self):
        """加载上次使用的模型"""
        try:
            # 从配置文件加载上次使用的模型
            last_model = self.config.config.get('ollama_model', 'qwen3:8b')
            if last_model:
                # 检查模型是否在下拉列表中，如果不在则添加
                model_index = self.model_selector.findText(last_model)
                if model_index == -1:
                    # 如果模型不在列表中，添加到列表开头
                    self.model_selector.insertItem(0, last_model)
                
                # 设置当前选中项
                self.model_selector.setCurrentText(last_model)
                self.log_message(f"已加载上次使用的模型: {last_model}")
                # 确保配置中也有这个值
                self.config.update_config('ollama_model', last_model)
        except Exception as e:
            self.log_message(f"加载上次模型失败: {e}", "ERROR")

    def setup_logging(self):
        """设置日志功能"""
        # 在自动化应用中添加日志回调
        if self.automation_app:
            self.automation_app.log_callback = self.log_message

    def log_message(self, message, level="INFO"):
        """记录日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        # 添加到日志文本框
        self.log_text.append(formatted_message)
        # 滚动到底部
        self.log_text.moveCursor(self.log_text.textCursor().End)

    def setup_auto_save(self):
        """设置自动保存功能"""
        # 当文本发生变化时自动保存
        # 使用 editTextChanged 代替 currentTextChanged，这样手动输入也会触发
        self.model_selector.editTextChanged.connect(self.auto_save_config_and_update_model)
        self.template_input.textChanged.connect(self.auto_save_config)
        self.capture_x_input.textChanged.connect(self.auto_save_config)
        self.capture_y_input.textChanged.connect(self.auto_save_config)
        self.input_x_input.textChanged.connect(self.auto_save_config)
        self.input_y_input.textChanged.connect(self.auto_save_config)
        self.confidence_slider.valueChanged.connect(self.auto_save_config)
        self.interval_input.textChanged.connect(self.auto_save_config)
        self.offset_x_input.textChanged.connect(self.auto_save_config)
        self.offset_y_input.textChanged.connect(self.auto_save_config)
        self.width_input.textChanged.connect(self.auto_save_config)
        self.height_input.textChanged.connect(self.auto_save_config)
        self.screen_monitor_radio.toggled.connect(self.auto_save_config)
        self.auto_copy_radio.toggled.connect(self.auto_save_config)

    def auto_save_config_and_update_model(self):
        """自动保存配置并更新模型"""
        self.auto_save_config()
        # 如果自动化应用存在，更新模型
        if self.automation_app:
            new_model = self.model_selector.currentText().strip()
            if new_model:
                self.automation_app.update_model(new_model)

    def auto_save_config(self):
        """自动保存配置"""
        try:
            # 更新工作模式
            if self.screen_monitor_radio.isChecked():
                active_mode = 'screen_monitor'
            else:
                active_mode = 'auto_copy'
            self.config.update_config('active_mode', active_mode)
            
            # 更新Ollama设置 - 使用当前文本而不是当前索引的文本
            current_model = self.model_selector.currentText().strip()
            if current_model:  # 确保不为空
                self.config.update_config('ollama_model', current_model)
            
            # 更新基本设置
            self.config.update_config('prompt_template', self.template_input.toPlainText())
            
            # 更新捕获点和输入点坐标到monitoring配置中
            monitoring_config = self.config.config.get('monitoring', {})
            
            # 更新input_coords（输入框坐标）
            input_coords = {
                'x': int(self.input_x_input.text()),
                'y': int(self.input_y_input.text())
            }
            monitoring_config['input_coords'] = input_coords
            
            # 更新copy_area_coords（文本捕获点坐标）
            copy_area_coords = {
                'x': int(self.capture_x_input.text()),
                'y': int(self.capture_y_input.text())
            }
            monitoring_config['copy_area_coords'] = copy_area_coords
            
            self.config.update_config('monitoring', monitoring_config)
            
            # 同时更新旧格式以保证兼容性
            capture_point = {
                'x': int(self.capture_x_input.text()),
                'y': int(self.capture_y_input.text())
            }
            self.config.update_config('capture_point', capture_point)
            
            input_point = {
                'x': int(self.input_x_input.text()),
                'y': int(self.input_y_input.text())
            }
            self.config.update_config('input_point', input_point)

            # 更新高级设置
            confidence = self.confidence_slider.value() / 100.0
            self.config.update_config('confidence_threshold', confidence)

            check_interval = float(self.interval_input.text())
            if check_interval >= 0.1:  # 只有在有效值时才更新
                self.config.update_config('check_interval', check_interval)

            # 更新区域设置
            screen_region = {
                'offset_x': int(self.offset_x_input.text()),
                'offset_y': int(self.offset_y_input.text()),
                'width': int(self.width_input.text()),
                'height': int(self.height_input.text())
            }
            self.config.update_config('screen_region', screen_region)

            # 如果自动化应用存在，只更新其配置而不改变运行状态
            if self.automation_app:
                # 更新检测区域
                self.automation_app.update_screen_region(
                    screen_region['offset_x'],
                    screen_region['offset_y'],
                    screen_region['width'],
                    screen_region['height']
                )
                # 更新监控参数
                if hasattr(self.automation_app.screen_monitor, 'confidence_threshold'):
                    self.automation_app.screen_monitor.confidence_threshold = confidence
                if hasattr(self.automation_app.screen_monitor, 'check_interval'):
                    self.automation_app.screen_monitor.check_interval = check_interval

        except ValueError:
            pass  # 忽略无效数值
        except Exception as e:
            print(f"自动保存配置时出错: {e}")

    def init_ui(self):
        # 设置窗口始终置顶
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowTitle('聊天自动化应用')
        self.setGeometry(300, 300, 1000, 950)  # 增加宽度以容纳日志区域

        # 创建中心窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局 - 水平分割左右两部分
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧配置区域
        left_layout = QVBoxLayout()
        
        # LLM API设置组
        api_group = QGroupBox("LLM API设置")
        api_layout = QFormLayout(api_group)

        # 创建模型选择下拉框
        self.model_selector = QComboBox()
        self.model_selector.setEditable(True)  # 允许编辑，以支持自定义模型名称
        # 初始加载时使用配置中的模型
        current_model = self.config.config.get('ollama_model', 'qwen3:8b')
        self.model_selector.addItem(current_model)
        self.model_selector.setCurrentText(current_model)
        
        # 刷新模型按钮
        refresh_models_btn = QPushButton("刷新模型列表")
        refresh_models_btn.clicked.connect(self.refresh_models)
        
        model_hbox = QHBoxLayout()
        model_hbox.addWidget(self.model_selector)
        model_hbox.addWidget(refresh_models_btn)
        
        api_layout.addRow("Ollama模型选择:", model_hbox)

        left_layout.addWidget(api_group)

        # 提示模板设置组
        template_group = QGroupBox("提示模板设置")
        template_layout = QVBoxLayout(template_group)

        self.template_input = QTextEdit()
        self.template_input.setPlainText(
            self.config.config.get('prompt_template', '你是我的聊天助手，负责帮我回复消息。请认真阅读下面的消息内容，理解其含义和语境，然后给出恰当、友好且简洁的回复。注意保持自然的对话风格，避免过于正式或生硬。\n\n消息内容：{message}')
        )
        template_layout.addWidget(self.template_input)

        left_layout.addWidget(template_group)

        # 工作模式选择组
        mode_group = QGroupBox("工作模式选择")
        mode_layout = QVBoxLayout(mode_group)
        
        # 创建互斥的单选按钮
        self.screen_monitor_radio = QRadioButton("屏幕监控模式")
        self.auto_copy_radio = QRadioButton("自动复制模式")
        
        # 根据配置设置默认选中项
        current_mode = self.config.config.get('active_mode', 'auto_copy')
        if current_mode == 'screen_monitor':
            self.screen_monitor_radio.setChecked(True)
        else:
            self.auto_copy_radio.setChecked(True)
        
        # 连接单选按钮变化事件
        self.screen_monitor_radio.toggled.connect(self.on_mode_changed)
        self.auto_copy_radio.toggled.connect(self.on_mode_changed)
        
        mode_layout.addWidget(self.screen_monitor_radio)
        mode_layout.addWidget(self.auto_copy_radio)
        
        left_layout.addWidget(mode_group)
        
        # 自动复制设置组
        copy_group = QGroupBox("自动复制设置")
        copy_layout = QFormLayout(copy_group)
        
        # 文本捕获点坐标设置
        self.capture_x_input = QLineEdit()
        self.capture_x_input.setValidator(QIntValidator())
        # 优先从monitoring.copy_area_coords读取，然后是旧的capture_point格式
        capture_x = self.config.config.get('monitoring', {}).get('copy_area_coords', {}).get('x', 
                    self.config.config.get('capture_point', {}).get('x', 0))
        self.capture_x_input.setText(str(capture_x))
        copy_layout.addRow("文本捕获X坐标:", self.capture_x_input)

        self.capture_y_input = QLineEdit()
        self.capture_y_input.setValidator(QIntValidator())
        # 优先从monitoring.copy_area_coords读取，然后是旧的capture_point格式
        capture_y = self.config.config.get('monitoring', {}).get('copy_area_coords', {}).get('y', 
                    self.config.config.get('capture_point', {}).get('y', 0))
        self.capture_y_input.setText(str(capture_y))
        copy_layout.addRow("文本捕获Y坐标:", self.capture_y_input)

        capture_select_btn = QPushButton("选择捕获点")
        capture_select_btn.clicked.connect(self.select_capture_point)
        copy_layout.addRow("", capture_select_btn)

        # 输入框坐标设置
        self.input_x_input = QLineEdit()
        self.input_x_input.setValidator(QIntValidator())
        # 优先从monitoring.input_coords读取，然后是旧的input_point格式
        input_x = self.config.config.get('monitoring', {}).get('input_coords', {}).get('x', 
                    self.config.config.get('input_point', {}).get('x', 0))
        self.input_x_input.setText(str(input_x))
        copy_layout.addRow("输入框X坐标:", self.input_x_input)

        self.input_y_input = QLineEdit()
        self.input_y_input.setValidator(QIntValidator())
        # 优先从monitoring.input_coords读取，然后是旧的input_point格式
        input_y = self.config.config.get('monitoring', {}).get('input_coords', {}).get('y', 
                    self.config.config.get('input_point', {}).get('y', 0))
        self.input_y_input.setText(str(input_y))
        copy_layout.addRow("输入框Y坐标:", self.input_y_input)

        input_select_btn = QPushButton("选择输入框")
        input_select_btn.clicked.connect(self.select_input_point)
        copy_layout.addRow("", input_select_btn)

        left_layout.addWidget(copy_group)

        # 高级设置组
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QFormLayout(advanced_group)

        # 置信度设置
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setMinimum(0)
        self.confidence_slider.setMaximum(100)
        confidence_value = self.config.config.get('confidence_threshold', 0.7)
        self.confidence_slider.setValue(int(confidence_value * 100))
        self.confidence_label = QLabel(f"{confidence_value:.2f}")
        self.confidence_slider.valueChanged.connect(
            lambda v: self.confidence_label.setText(f"{v/100:.2f}")
        )
        h_layout1 = QHBoxLayout()
        h_layout1.addWidget(self.confidence_slider)
        h_layout1.addWidget(self.confidence_label)
        advanced_layout.addRow("匹配置信度:", h_layout1)

        # 检查间隔设置
        self.interval_input = QLineEdit()
        interval_value = self.config.config.get('check_interval', 0.5)
        self.interval_input.setText(str(interval_value))
        advanced_layout.addRow("检查间隔(秒):", self.interval_input)

        left_layout.addWidget(advanced_group)

        # 屏幕区域设置组
        region_group = QGroupBox("屏幕检测区域设置")
        region_layout = QFormLayout(region_group)

        self.offset_x_input = QLineEdit()
        self.offset_x_input.setText(str(self.config.config.get('screen_region', {}).get('offset_x', 0)))
        region_layout.addRow("X偏移:", self.offset_x_input)

        self.offset_y_input = QLineEdit()
        self.offset_y_input.setText(str(self.config.config.get('screen_region', {}).get('offset_y', 0)))
        region_layout.addRow("Y偏移:", self.offset_y_input)

        self.width_input = QLineEdit()
        self.width_input.setText(str(self.config.config.get('screen_region', {}).get('width', 800)))
        region_layout.addRow("宽度:", self.width_input)

        self.height_input = QLineEdit()
        self.height_input.setText(str(self.config.config.get('screen_region', {}).get('height', 600)))
        region_layout.addRow("高度:", self.height_input)

        # 按钮布局
        btn_layout = QHBoxLayout()
        self.set_region_btn = QPushButton("设置监控区域")
        self.set_region_btn.clicked.connect(self.set_region)
        btn_layout.addWidget(self.set_region_btn)

        self.select_region_btn = QPushButton("手动选择区域")
        self.select_region_btn.clicked.connect(self.select_region)
        btn_layout.addWidget(self.select_region_btn)

        region_layout.addRow(btn_layout)

        left_layout.addWidget(region_group)

        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("启动监控")
        self.start_btn.clicked.connect(self.start_monitoring)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止监控")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)  # 初始状态禁用
        control_layout.addWidget(self.stop_btn)
        
        left_layout.addLayout(control_layout)

        # 右侧日志区域
        right_layout = QVBoxLayout()
        log_group = QGroupBox("系统日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumWidth(350)  # 设置日志区域的最大宽度
        log_layout.addWidget(self.log_text)
        
        # 添加清空日志按钮
        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)
        
        right_layout.addWidget(log_group)

        # 将左右布局添加到主布局
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()

    def on_mode_changed(self):
        """工作模式改变时的处理"""
        if self.screen_monitor_radio.isChecked():
            mode = 'screen_monitor'
        else:
            mode = 'auto_copy'
        self.log_message(f"工作模式已切换到: {mode}")

    def set_region(self):
        """设置监控区域"""
        try:
            x = int(self.offset_x_input.text())
            y = int(self.offset_y_input.text())
            w = int(self.width_input.text())
            h = int(self.height_input.text())

            if w <= 0 or h <= 0:
                QMessageBox.warning(self, "警告", "宽度和高度必须大于0")
                self.log_message("设置监控区域失败: 宽度和高度必须大于0", "ERROR")
                return

            # 如果自动化应用存在，更新其区域设置
            if self.automation_app:
                self.automation_app.update_screen_region(x, y, w, h)
            
            # 更新配置
            screen_region = {
                'offset_x': x,
                'offset_y': y,
                'width': w,
                'height': h
            }
            self.config.update_config('screen_region', screen_region)
            
            self.log_message(f"监控区域已设置为: ({x}, {y}, {w}, {h})")
            QMessageBox.information(self, "成功", f"监控区域已设置为: ({x}, {y}, {w}, {h})")
        except ValueError:
            QMessageBox.warning(self, "警告", "请输入有效的数字")
            self.log_message("设置监控区域失败: 请输入有效的数字", "ERROR")

    def select_capture_point(self):
        """选择文本捕获点"""
        try:
            from modules.coordinate_selector import select_coordinates
            select_coordinates(self.set_capture_coordinates)
        except ImportError:
            QMessageBox.warning(self, "错误", "无法导入坐标选择工具")
            self.log_message("无法导入坐标选择工具", "ERROR")

    def select_input_point(self):
        """选择输入框位置"""
        try:
            from modules.coordinate_selector import select_coordinates
            select_coordinates(self.set_input_coordinates)
        except ImportError:
            QMessageBox.warning(self, "错误", "无法导入坐标选择工具")
            self.log_message("无法导入坐标选择工具", "ERROR")

    def set_capture_coordinates(self, x, y):
        """设置捕获坐标"""
        self.capture_x_input.setText(str(x))
        self.capture_y_input.setText(str(y))
        self.log_message(f"捕获点坐标已设置: ({x}, {y})")

    def set_input_coordinates(self, x, y):
        """设置输入坐标"""
        self.input_x_input.setText(str(x))
        self.input_y_input.setText(str(y))
        self.log_message(f"输入框坐标已设置: ({x}, {y})")

    def select_region(self):
        """手动选择区域"""
        # 实现手动选择区域的功能
        QMessageBox.information(self, "提示", "此功能将在后续版本中实现")
        self.log_message("手动选择区域功能尚未实现")
        
    def auto_refresh_models(self):
        """自动刷新模型列表 - 在程序启动时调用"""
        # 使用默认的Ollama服务地址
        host = 'http://localhost:11434'
        self.log_message("正在自动获取模型列表...")
            
        # 使用线程获取模型列表，防止UI冻结
        self.model_worker = ModelListWorker(host)
        self.model_worker.finished.connect(self.on_models_loaded)
        self.status_bar.showMessage("正在自动获取模型列表...")
        self.model_worker.start()
        
    def refresh_models(self):
        """刷新模型列表 - 修复错误：使用固定的host地址"""
        # 使用固定的默认地址，因为我们没有对应的输入框
        host = 'http://localhost:11434'
        self.log_message("正在获取模型列表...")
        # 如果需要自定义地址，可以考虑添加一个输入框或从配置读取
        custom_host = self.config.config.get('ollama', {}).get('url', 'http://localhost:11434')
        # 提取主机地址部分
        if custom_host.startswith('http://'):
            host = custom_host.replace('/api/generate', '').replace('/api/tags', '') if '/api/' in custom_host else custom_host
        elif custom_host.startswith('https://'):
            host = custom_host.replace('/api/generate', '').replace('/api/tags', '') if '/api/' in custom_host else custom_host
            
        # 使用线程获取模型列表，防止UI冻结
        self.model_worker = ModelListWorker(host)
        self.model_worker.finished.connect(self.on_models_loaded)
        self.status_bar.showMessage("正在获取模型列表...")
        self.model_worker.start()

    def on_models_loaded(self):
        """模型列表加载完成后更新下拉框"""
        # 先保存当前选中的模型
        current_selection = self.model_selector.currentText()
        
        self.model_selector.clear()
        self.model_selector.addItem(current_selection)  # 先添加当前选中的模型
        self.model_selector.setCurrentText(current_selection)  # 设置为当前选中
        
        if self.model_worker.models:
            # 添加从API获取的模型
            for model in self.model_worker.models:
                if model != current_selection:  # 避免重复添加
                    self.model_selector.addItem(model)
            self.status_bar.showMessage(f"已加载 {len(self.model_worker.models)} 个模型")
            self.log_message(f"已加载 {len(self.model_worker.models)} 个模型")
        else:
            self.status_bar.showMessage("未能获取模型列表，请检查Ollama服务")
            self.log_message("未能获取模型列表，请检查Ollama服务", "WARNING")

    def start_monitoring(self):
        """启动监控"""
        if self.automation_app:
            # 显示启动提示
            self.status_bar.showMessage("正在启动监控...")
            self.log_message("正在启动监控...")
            QApplication.processEvents()  # 立即更新界面
            
            self.automation_app.start_monitoring()
            
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
            # 显示更具体的提示信息
            capture_x = int(self.capture_x_input.text())
            capture_y = int(self.capture_y_input.text())
            input_x = int(self.input_x_input.text())
            input_y = int(self.input_y_input.text())
            current_model = self.model_selector.currentText()
            
            status_msg = f"监控已启动 - 捕获坐标: ({capture_x}, {capture_y}), 输入坐标: ({input_x}, {input_y}), 模型: {current_model}"
            self.status_bar.showMessage(status_msg)
            self.log_message(status_msg)
            
            # 在状态栏显示周期性提示，让用户知道程序正在运行
            self.operation_counter = 0
            self.operation_timer = QTimer(self)
            self.operation_timer.timeout.connect(self.update_operation_status)
            self.operation_timer.start(5000)  # 每5秒更新一次
        else:
            QMessageBox.warning(self, "警告", "自动化应用未初始化")
            self.log_message("启动监控失败: 自动化应用未初始化", "ERROR")

    def update_operation_status(self):
        """更新操作状态提示"""
        self.operation_counter += 1
        # 显示周期性提示，让用户知道程序仍在运行
        current_model = self.model_selector.currentText()
        status_msg = f"监控运行中... (运行周期: {self.operation_counter}, 模型: {current_model})"
        self.status_bar.showMessage(status_msg)
        self.log_message(f"监控运行中 (周期: {self.operation_counter})")
        
        # 5秒后恢复常规状态信息
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.update_status_with_coordinates())
        timer.start(5000)
    
    def update_status_with_coordinates(self):
        """恢复显示坐标信息"""
        capture_x = int(self.capture_x_input.text())
        capture_y = int(self.capture_y_input.text())
        input_x = int(self.input_x_input.text())
        input_y = int(self.input_y_input.text())
        current_model = self.model_selector.currentText()
        status_msg = f"监控已启动 - 捕获坐标: ({capture_x}, {capture_y}), 输入坐标: ({input_x}, {input_y}), 模型: {current_model}"
        self.status_bar.showMessage(status_msg)
    
    def stop_monitoring(self):
        """停止监控"""
        if self.automation_app:
            self.automation_app.stop_monitoring()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_bar.showMessage("监控已停止")
            self.log_message("监控已停止")
            
            # 停止周期性状态更新
            if hasattr(self, 'operation_timer'):
                self.operation_timer.stop()
        else:
            QMessageBox.warning(self, "警告", "自动化应用未初始化")
            self.log_message("停止监控失败: 自动化应用未初始化", "ERROR")

    def closeEvent(self, event):
        """程序关闭时自动保存坐标设置"""
        # 保存配置到文件
        self.config.save('user_config.json')
        self.log_message("所有设置已自动保存")
        print("✅ 所有设置已自动保存")
        # 接受关闭事件
        event.accept()