<<<<<<< HEAD
# config.py
import os
import json

def load_user_config():
    """加载用户配置文件"""
    config_file = 'user_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_config():
    user_config = load_user_config()
    
    # 默认配置
    default_config = {
        "ollama": {
            "url": "http://localhost:11434/api/generate",
            "model": user_config.get('ollama', {}).get('model', 'llama3.1:8b'),  # 修改为llama3.1:8b
            "timeout": 30
        },
        "monitoring": {
            "interval": 3,  # 稍微减少间隔，但不过快
            "ocr_lang": "chi_sim+eng",
            "min_text_length": 1,  # 降低最小长度要求到1
            "confidence_threshold": 35  # 提高置信度要求
        },
        "gui": {
            "window_size": (800, 600),
            "refresh_rate": 1000
        },
        "paths": {
            "tesseract_path": r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        }
    }
    
    # 如果用户配置中有监控区域，添加到配置中
    if 'monitoring' in user_config:
        default_config['monitoring'].update(user_config['monitoring'])
    
    return default_config

=======
# config.py
import os
import json

def load_user_config():
    """加载用户配置文件"""
    config_file = 'user_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_config():
    user_config = load_user_config()
    
    # 默认配置
    default_config = {
        "ollama": {
            "url": "http://localhost:11434/api/generate",
            "model": user_config.get('ollama', {}).get('model', 'deepseek-r1:7b'),
            "timeout": 30
        },
        "monitoring": {
            "interval": 3,  # 稍微减少间隔，但不过快
            "ocr_lang": "chi_sim+eng",
            "min_text_length": 1,  # 降低最小长度要求到1
            "confidence_threshold": 35  # 提高置信度要求
        },
        "gui": {
            "window_size": (800, 600),
            "refresh_rate": 1000
        },
        "paths": {
            "tesseract_path": r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        }
    }
    
    # 如果用户配置中有监控区域，添加到配置中
    if 'monitoring' in user_config:
        default_config['monitoring'].update(user_config['monitoring'])
    
    return default_config

>>>>>>> 1ee4eff02bd1256b18883f945e688489d09d480a
CONFIG = get_config()