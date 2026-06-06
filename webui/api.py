from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.ai_handler import AIHandler
from modules.auto_copy_handler import AutoCopyHandler
from modules.config_loader import ConfigLoader

# 修复模板文件夹路径
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
CORS(app)

# 全局变量存储实例
current_automation_app = None
current_ai_handler = None
current_config = None

def init_app(automation_app):
    """初始化Web UI应用"""
    global current_automation_app, current_ai_handler, current_config
    current_automation_app = automation_app
    
    # 加载配置
    current_config = ConfigLoader('user_config.json')
    current_ai_handler = AIHandler(current_config.config)

@app.route('/')
def index():
    """Web界面主页"""
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"渲染模板错误: {e}")
        return f"Template error: {e}", 500

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    try:
        return jsonify({
            'running': current_automation_app.is_running if current_automation_app else False,
            'ai_connected': current_ai_handler.test_connection() if current_ai_handler else False,
            'model': current_config.config.get('ollama_model', 'unknown') if current_config else 'unknown'
        })
    except Exception as e:
        print(f"获取状态错误: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/models')
def get_models():
    """获取可用模型"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            return jsonify({'models': models})
        return jsonify({'models': []})
    except Exception as e:
        print(f"获取模型错误: {e}")
        return jsonify({'models': []})

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """处理配置"""
    try:
        if request.method == 'GET':
            return jsonify(current_config.config if current_config else {})
        
        elif request.method == 'POST':
            new_config = request.json
            if current_config:
                current_config.config.update(new_config)
                current_config.save('user_config.json')
                # 如果模型改变，更新AI处理器
                if 'ollama_model' in new_config and current_ai_handler:
                    current_ai_handler = AIHandler(current_config.config)
            return jsonify({'success': True})
    except Exception as e:
        print(f"处理配置错误: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/control', methods=['POST'])
def control_automation():
    """控制自动化"""
    try:
        action = request.json.get('action')
        
        if action == 'start' and current_automation_app:
            current_automation_app.start_listening()
            return jsonify({'status': 'started'})
        elif action == 'stop' and current_automation_app:
            current_automation_app.stop_listening()
            return jsonify({'status': 'stopped'})
        
        return jsonify({'error': 'Invalid operation'})
    except Exception as e:
        print(f"控制自动化错误: {e}")
        return jsonify({'error': str(e)}), 500

# 确保模板目录存在并创建HTML文件
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
os.makedirs(template_dir, exist_ok=True)

html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>聊天自动化AI助手 - Web控制台</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .card { border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; }
        .btn { padding: 8px 16px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background-color: #1890ff; color: white; }
        .btn-success { background-color: #52c41a; color: white; }
        .btn-danger { background-color: #ff4d4f; color: white; }
        .status-running { color: #52c41a; font-weight: bold; }
        .status-stopped { color: #ff4d4f; font-weight: bold; }
        .form-group { margin: 10px 0; }
        label { display: inline-block; width: 120px; }
        input, select { padding: 5px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>聊天自动化AI助手 - Web控制台</h1>
        
        <div class="grid">
            <!-- 左侧：基本控制 -->
            <div>
                <div class="card">
                    <h3>系统控制</h3>
                    <div class="form-group">
                        <span>状态: <span id="status-text" class="status-stopped">已停止</span></span>
                        <button class="btn btn-primary" onclick="toggleAutomation()">启动/停止</button>
                    </div>
                    
                    <div class="form-group">
                        <label>AI模型:</label>
                        <select id="model-select"></select>
                        <button class="btn" onclick="loadModels()">刷新模型</button>
                    </div>
                    
                    <div class="form-group">
                        <button class="btn btn-success" onclick="saveConfig()">保存配置</button>
                        <button class="btn" onclick="loadConfig()">刷新配置</button>
                    </div>
                </div>
                
                <div class="card">
                    <h3>坐标设置</h3>
                    <div class="form-group">
                        <label>捕获点X:</label>
                        <input type="number" id="capture-x" value="0">
                    </div>
                    <div class="form-group">
                        <label>捕获点Y:</label>
                        <input type="number" id="capture-y" value="0">
                    </div>
                    <div class="form-group">
                        <label>输入框X:</label>
                        <input type="number" id="input-x" value="0">
                    </div>
                    <div class="form-group">
                        <label>输入框Y:</label>
                        <input type="number" id="input-y" value="0">
                    </div>
                </div>
            </div>
            
            <!-- 右侧：高级设置 -->
            <div>
                <div class="card">
                    <h3>系统信息</h3>
                    <div class="form-group">
                        <p>AI连接状态: <span id="ai-status">未知</span></p>
                        <p>当前模型: <span id="current-model">未知</span></p>
                    </div>
                </div>
                
                <div class="card">
                    <h3>高级设置</h3>
                    <div class="form-group">
                        <label>置信度:</label>
                        <input type="range" id="confidence" min="0" max="100" value="70">
                        <span id="confidence-value">0.70</span>
                    </div>
                    <div class="form-group">
                        <label>检查间隔(秒):</label>
                        <input type="number" id="interval" step="0.1" value="0.5">
                    </div>
                </div>
                
                <div class="card">
                    <h3>测试功能</h3>
                    <div class="form-group">
                        <button class="btn" onclick="testConnection()">测试AI连接</button>
                        <button class="btn" onclick="updateStatus()">刷新状态</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // API基础URL
        const API_BASE = '/api';
        
        // 页面加载时获取初始数据
        document.addEventListener('DOMContentLoaded', function() {
            loadConfig();
            updateStatus();
            loadModels();
            
            // 监听置信度滑块变化
            document.getElementById('confidence').addEventListener('input', function() {
                const value = this.value / 100;
                document.getElementById('confidence-value').textContent = value.toFixed(2);
            });
        });
        
        async function updateStatus() {
            try {
                const response = await fetch(API_BASE + '/status');
                const data = await response.json();
                
                const statusText = document.getElementById('status-text');
                const aiStatus = document.getElementById('ai-status');
                const currentModel = document.getElementById('current-model');
                
                statusText.textContent = data.running ? '运行中' : '已停止';
                statusText.className = data.running ? 'status-running' : 'status-stopped';
                
                aiStatus.textContent = data.ai_connected ? '已连接' : '未连接';
                currentModel.textContent = data.model;
            } catch (error) {
                console.error('获取状态失败:', error);
            }
        }
        
        async function loadConfig() {
            try {
                const response = await fetch(API_BASE + '/config');
                const config = await response.json();
                
                // 填充表单
                document.getElementById('capture-x').value = config.capture_point?.x || 0;
                document.getElementById('capture-y').value = config.capture_point?.y || 0;
                document.getElementById('input-x').value = config.input_point?.x || 0;
                document.getElementById('input-y').value = config.input_point?.y || 0;
                
                // 设置置信度滑块
                const confidence = Math.round((config.confidence_threshold || 0.7) * 100);
                document.getElementById('confidence').value = confidence;
                document.getElementById('confidence-value').textContent = (config.confidence_threshold || 0.7).toFixed(2);
                
                // 设置检查间隔
                document.getElementById('interval').value = config.check_interval || 0.5;
                
                // 设置模型选择
                const modelSelect = document.getElementById('model-select');
                if (modelSelect && config.ollama_model) {
                    modelSelect.value = config.ollama_model;
                }
            } catch (error) {
                console.error('获取配置失败:', error);
            }
        }
        
        async function saveConfig() {
            const config = {
                capture_point: {
                    x: parseInt(document.getElementById('capture-x').value),
                    y: parseInt(document.getElementById('capture-y').value)
                },
                input_point: {
                    x: parseInt(document.getElementById('input-x').value),
                    y: parseInt(document.getElementById('input-y').value)
                },
                confidence_threshold: parseFloat(document.getElementById('confidence').value) / 100,
                check_interval: parseFloat(document.getElementById('interval').value),
                ollama_model: document.getElementById('model-select').value
            };
            
            try {
                await fetch(API_BASE + '/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                alert('配置已保存！');
            } catch (error) {
                alert('保存配置失败！');
                console.error('保存配置失败:', error);
            }
        }
        
        async function toggleAutomation() {
            const isRunning = document.getElementById('status-text').textContent === '运行中';
            const action = isRunning ? 'stop' : 'start';
            
            try {
                await fetch(API_BASE + '/control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action })
                });
                
                setTimeout(updateStatus, 1000); // 延迟更新状态
            } catch (error) {
                alert('操作失败！');
                console.error('控制操作失败:', error);
            }
        }
        
        async function loadModels() {
            try {
                const response = await fetch(API_BASE + '/models');
                const data = await response.json();
                
                const select = document.getElementById('model-select');
                select.innerHTML = '';
                
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('获取模型列表失败:', error);
            }
        }
        
        async function testConnection() {
            try {
                const response = await fetch(API_BASE + '/config'); // 使用已有API测试连接
                if (response.ok) {
                    alert('连接测试成功！');
                } else {
                    alert('连接测试失败！');
                }
            } catch (error) {
                alert('连接测试失败！');
                console.error('连接测试失败:', error);
            }
        }
    </script>
</body>
</html>'''

# 创建模板文件
template_path = os.path.join(template_dir, 'index.html')
with open(template_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✅ HTML模板已创建: {template_path}")
