#!/usr/bin/env python3
"""
测试坐标选择功能的脚本
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.coordinate_selector import select_coordinates

def test_callback(x, y):
    print(f"选择的坐标是: ({x}, {y})")

if __name__ == "__main__":
    print("开始测试坐标选择功能...")
    print("点击屏幕上的任意位置来获取坐标，或按ESC键取消")
    
    select_coordinates(test_callback)
    
    print("坐标选择完成")