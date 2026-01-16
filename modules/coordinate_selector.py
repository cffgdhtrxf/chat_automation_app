"""
coordinate_selector.py - 坐标选择器模块
提供一个全屏覆盖层来捕获用户点击的屏幕坐标
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QDialog
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QScreen


class CoordinateSelector(QDialog):  # 继承QDialog而不是QWidget
    """
    全屏坐标选择器
    显示半透明覆盖层，捕获用户点击的坐标
    """
    coordinates_selected = pyqtSignal(int, int)  # 发射选中的坐标

    def __init__(self):
        super().__init__()
        # 初始化时先创建label
        self.label = None
        self.init_ui()
        # 设置为模态对话框
        self.setModal(True)

    def init_ui(self):
        # 获取主屏幕的几何信息
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        
        # 设置为全屏、无边框、置顶的半透明窗口
        self.setWindowTitle('选择坐标')
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.X11BypassWindowManagerHint  # 绕过窗口管理器（确保全屏）
        )
        # 直接设置几何尺寸，而不是使用WindowState
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setWindowOpacity(0.3)  # 半透明
        
        # 创建提示标签
        self.label = QLabel('点击您想要获取坐标的位置\n按 ESC 键取消', self)
        self.label.setStyleSheet("""
            background-color: black;
            color: white;
            font-size: 18px;
            font-weight: bold;
            padding: 20px;
            border: 2px solid yellow;
            border-radius: 10px;
        """)
        self.label.setAlignment(Qt.AlignCenter)
        
        # 将标签放在屏幕中央
        self.update_label_position()

    def update_label_position(self):
        """更新标签位置"""
        if self.label:
            self.label.setGeometry(
                (self.width() - 400) // 2,
                (self.height() - 100) // 2,
                400,
                100
            )

    def resizeEvent(self, event):
        """窗口大小改变时重新定位标签"""
        self.update_label_position()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        """鼠标点击事件 - 返回全局坐标"""
        if event.button() == Qt.LeftButton:
            # 获取全局坐标（相对于屏幕的坐标）
            pos = event.globalPos()  # 这是关键：获取全局坐标
            x = pos.x()
            y = pos.y()
            print(f"CoordinateSelector: 选中屏幕坐标 ({x}, {y})")
            # 发射坐标信号并关闭
            self.coordinates_selected.emit(x, y)
            self.accept()  # 关闭对话框并返回Accepted状态
            self.close()
    
    def keyPressEvent(self, event):
        """键盘按键事件"""
        if event.key() == Qt.Key_Escape:
            # ESC键取消选择
            self.reject()  # 关闭对话框并返回Rejected状态
            self.close()


def select_coordinates(callback):
    """
    选择坐标的主要函数
    
    Args:
        callback: 回调函数，接收两个参数(x, y)
    """
    # 获取当前应用程序实例
    app = QApplication.instance()
    if app is None:
        # 只有在没有现有应用程序实例时才创建
        app = QApplication(sys.argv)
        created_app = True
    else:
        created_app = False
    
    # 创建并显示坐标选择器
    selector = CoordinateSelector()
    selector.coordinates_selected.connect(callback)
    
    # 使用exec_()来显示模态对话框，这会阻塞直到对话框关闭
    result = selector.exec_()
    
    # 如果是新创建的应用程序实例，才需要运行事件循环
    # 但在这里我们不这样做，因为exec_()已经处理了模态显示