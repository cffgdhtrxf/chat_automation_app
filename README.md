# 🤖 聊天自动化AI助手

一个强大的社交软件AI接入解决方案，支持自动监控聊天内容并使用本地 AI 模型进行智能回复。提供 **桌面GUI** 和 **Web控制台** 两种交互方式。

## ✨ 功能特性

### 核心功能
- 🔍 **智能监控** - 基于 OpenCV 图像的屏幕变化检测，自动捕获聊天界面新消息
- 🧠 **AI驱动回复** - 接入 Ollama 本地大模型，生成上下文感知的智能回复
- 🖥️ **双界面支持** - PyQt5 桌面GUI + Flask Web 控制台，随时随地管理
- 📋 **自动复制模式** - 一键复制聊天内容 → AI 生成回复 → 自动粘贴发送
- 🎯 **坐标选择器** - 可视化拖拽选择捕获点和输入框位置

### 智能增强
- 🕐 **系统信息注入** - AI 可获取实时时间、日期、星期、时区、操作系统等系统信息
- 👤 **人性化模拟** - 鼠标轨迹移动、随机延迟、打字停顿，避免被检测为机器人
- 🧹 **思考过滤** - 自动过滤模型 `<think>` 标签中的推理过程，只保留干净回复
- 🔧 **热键控制** - `Ctrl+Shift+A` 激活应用 / `Ctrl+Shift+P` 暂停/恢复

### Web 控制台特色
- 🌐 **浏览器访问** - 通过 `http://localhost:5000` 远程管理
- 📊 **实时状态** - 运行状态、AI 连接状态、当前模型一目了然
- ⚙️ **在线配置** - 可视化修改坐标、置信度、检查间隔等参数
- 🔄 **模型切换** - 动态获取 Ollama 模型列表，一键切换

## 🛠 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.8+ |
| GUI | PyQt5 |
| Web | Flask + Flask-CORS |
| 图像处理 | OpenCV, Pillow, NumPy |
| 自动化 | PyAutoGUI, Keyboard |
| OCR | Tesseract-OCR |
| AI | Ollama (本地大模型) |
| 通信 | Requests |

## 📦 安装

### 1. 克隆仓库
```bash
git clone https://github.com/cffgdhtrxf/chat_automation_app.git
cd chat_automation_app
```

### 2. 安装依赖
```bash
# 基础依赖（GUI 模式必需）
pip install -r requirements.txt

# Web UI 额外依赖
pip install -r requirements_web.txt
```

### 3. 安装 Tesseract-OCR
从 [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki) 下载安装，默认路径：
```
C:\Program Files\Tesseract-OCR\tesseract.exe
```

### 4. 安装 Ollama 并下载模型
```bash
# 启动 Ollama 服务
ollama serve

# 下载模型（推荐）
ollama pull qwen3:8b
# 或其他模型如 llama3.1:8b、qwen2.5:7b 等
```

## 🚀 使用方式

### 方式一：GUI 桌面应用
```bash
python run_gui.py
```
- 可视化界面操作，设置监控区域、配置坐标
- 选择 AI 模型，一键启动/停止监控
- 支持坐标可视化选择器

### 方式二：Web 控制台
```bash
python run_web.py
```
- 打开浏览器访问 `http://localhost:5000`
- 远程查看状态、修改配置、切换模型
- 适合服务器/无人值守场景

### 方式三：命令行模式
```bash
python main.py
```
- 纯后台运行，使用 `user_config.json` 配置

## ⚙️ 配置文件

`user_config.json` 主要配置项：

```json
{
  "ollama": {
    "url": "http://localhost:11434/api/generate",
    "model": "qwen3:8b",
    "timeout": 30
  },
  "monitoring": {
    "interval": 3,
    "confidence_threshold": 35,
    "region": { "x": 490, "y": 1035, "width": 401, "height": 100 }
  },
  "capture_point": { "x": 502, "y": 1354 },
  "input_point": { "x": 449, "y": 1159 },
  "ollama_model": "qwen3.5:9b",
  "prompt_template": "你是我的聊天助手...",
  "enable_auto_copy": true
}
```

## 📁 项目结构

```
chat_automation_app/
├── main.py                 # 核心主程序入口
├── run_gui.py              # PyQt5 GUI 启动脚本
├── run_web.py              # Flask Web UI 启动脚本
├── config.py               # 默认配置加载器
├── user_config.json        # 用户配置文件
├── requirements.txt        # 基础依赖
├── requirements_web.txt    # Web UI 依赖
│
├── gui/
│   └── gui_app.py          # PyQt5 桌面 GUI 界面
│
├── webui/                  # 🆕 Web 控制台模块
│   ├── api.py              # Flask REST API 后端
│   └── templates/
│       └── index.html      # Web 控制台前端页面
│
├── modules/
│   ├── ai_handler.py       # AI 处理器（Ollama 通信 + 系统信息注入）
│   ├── auto_copy_handler.py # 自动复制粘贴处理器
│   ├── screen_monitor.py   # 屏幕变化检测监控器
│   ├── keyboard_sim.py     # 键盘模拟器（人性化打字）
│   ├── config_loader.py    # 配置文件加载器
│   ├── coordinate_selector.py # 坐标可视化选择器
│   ├── system_info.py      # 系统信息提供者
│   └── __init__.py
│
├── test_coordinate_selector.py  # 坐标选择器测试
├── test_gui.py                  # GUI 功能测试
└── simple_run.py                # 简化运行脚本
```

## 🔄 工作流程

```
聊天消息 → 屏幕捕获(OCR/复制) → AI分析 → 生成回复 → 自动发送
                                    ↑
                              系统信息注入
                          (时间/日期/用户/系统)
```

### 两种工作模式

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| **屏幕监控模式** | OCR 识别屏幕变化 | 文字聊天内容检测 |
| **自动复制模式** | 监听剪贴板变化 | 富文本/图片内容场景 |

## ⚠️ 注意事项

- 确保 Ollama 服务在 `http://localhost:11434` 正常运行
- 坐标设置需根据实际屏幕分辨率和窗口位置调整
- 合理设置检查间隔（建议 0.5~3 秒），避免过度占用资源
- 请遵守相关平台使用条款，仅用于合规场景
- 建议在测试环境中验证后再正式使用

## 📄 许可证

MIT License
