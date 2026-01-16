# 聊天自动化AI助手

一个强大的社交软件AI接入解决方案，能够自动监控聊天内容并使用AI模型进行智能回复。

## 🚀 功能特性

- **智能监控** - 自动检测聊天界面中的新消息
- **AI驱动回复** - 支持Ollama模型，提供智能回复
- **系统信息注入** - AI可获取实时时间、日期等系统信息
- **人性化行为** - 模拟人类鼠标移动、思考时间等行为
- **多模型支持** - 支持任意Ollama模型
- **可视化界面** - 直观的GUI控制面板

## 🛠 技术栈

- Python 3.8+
- PyQt5 - GUI界面
- OpenCV - 图像处理
- PyAutoGUI - 自动化操作
- Requests - API通信
- Ollama - 本地AI模型

## 📋 依赖安装

```bash
pip install -r requirements.txt

⚙️ 配置说明
1.启动Ollama服务:
ollama serve

2.下载所需模型:
ollama pull qwen3:8b
# 或其他支持的模型

3.运行 GUI 程序:
python run_gui.py

🔧 使用方法
设置监控区域 - 在GUI中设置要监控的屏幕区域
配置坐标 - 设置文本捕获点和输入框坐标
选择AI模型 - 从下拉菜单中选择使用的模型
启动监控 - 点击"启动监控"按钮开始自动回复

💡 系统信息注入
本项目独特功能：AI能够获取并使用实时系统信息，如：

当前时间
星期几
时区
用户信息
操作系统详情
当用户询问时间等问题时，AI会基于系统信息提供准确答案。

🤖 人性化行为模拟
为避免被检测为机器人，程序模拟了人类行为：

鼠标移动轨迹
随机停顿时长
AI思考时间
打字延迟模拟

🔧 配置文件
user_config.json - 用户配置文件
config.json - 默认配置文件

📁 项目结构

chat_automation_app/
├── main.py              # 主程序入口
├── run_gui.py          # GUI启动脚本
├── gui/
│   └── gui_app.py      # GUI界面
├── modules/
│   ├── ai_handler.py   # AI处理器
│   ├── auto_copy_handler.py # 自动复制处理器
│   ├── screen_monitor.py # 屏幕监控器
│   └── ...             # 其他模块
└── requirements.txt    # 依赖包列表

⚠️ 注意事项
确保Ollama服务正常运行
合理设置监控间隔避免过度占用资源
遵守相关平台的使用条款
建议在测试环境中先验证功能
🤝 贡献
欢迎提交Issue和Pull Request来改进项目！

📄 许可证
MIT 许可证

## **如何添加：**

1. **在项目根目录创建文件** `README.md`
2. **复制上述内容到文件中**
3. **保存文件**
4. **提交到GitHub**:
   ```bash
   git add README.md
   git commit -m "Add README.md with project documentation"
   git push origin main
















