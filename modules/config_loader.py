import os
import json
import sys
from pathlib import Path

# 添加项目根目录到sys.path，以便正确导入config模块
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 使用绝对导入路径
import config
CONFIG = config.CONFIG


class ConfigLoader:
    def __init__(self, config_file="config.json"):
        """
        初始化配置加载器
        :param config_file: 配置文件路径
        """
        # 使用传入的配置文件路径，如果没有找到则使用默认配置
        self.config_file = config_file
        self.config = {}
        
        # 尝试从传入的配置文件加载
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            # 如果传入的配置文件不存在，使用默认配置
            self.config = CONFIG.copy()
        
        # 加载用户配置覆盖默认配置
        if os.path.exists("user_config.json"):
            with open("user_config.json", 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                
                # 更新主配置
                for key, value in user_config.items():
                    if isinstance(value, dict) and key in self.config:
                        self.config[key].update(value)
                    else:
                        self.config[key] = value

    def get(self, key, default=None):
        """
        获取配置值
        :param key: 键名，可以是'key.subkey'格式
        :param default: 默认值
        :return: 配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value

    def set(self, key, value):
        """
        设置配置值
        :param key: 键名，可以是'key.subkey'格式
        :param value: 值
        """
        keys = key.split('.')
        config_ref = self.config
        
        for k in keys[:-1]:
            if k not in config_ref:
                config_ref[k] = {}
            config_ref = config_ref[k]
            
        config_ref[keys[-1]] = value
    
    def update_config(self, key, value):
        """
        更新配置值（与set方法功能相同）
        :param key: 键名，可以是'key.subkey'格式
        :param value: 值
        """
        self.set(key, value)

    def save(self, config_file=None):
        """
        保存配置到文件
        :param config_file: 要保存到的文件路径，默认使用初始化时指定的文件
        """
        target_file = config_file or self.config_file
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)