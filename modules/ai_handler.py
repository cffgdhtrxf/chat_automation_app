# modules/ai_handler.py
import requests
import json
import re
import datetime
import platform
import getpass

class SystemInfoProvider:
    def __init__(self):
        pass
    
    def get_basic_info(self):
        """获取基本系统信息"""
        return {
            'current_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'weekday': datetime.datetime.now().strftime("%A"),
            'timezone': str(datetime.datetime.now().astimezone().tzinfo),
            'system_name': platform.system(),
            'machine_type': platform.machine(),
            'user_name': getpass.getuser(),
            'platform_details': platform.platform()
        }
    
    def get_formatted_info(self):
        """获取格式化的系统信息字符串"""
        info = self.get_basic_info()
        return f"""系统信息:
- 当前时间: {info['current_time']}
- 星期: {info['weekday']}
- 时区: {info['timezone']}
- 用户: {info['user_name']}
- 操作系统: {info['system_name']} ({info['platform_details']})"""

class AIHandler:
    def __init__(self, config):
        self.config = config
        self.system_info_provider = SystemInfoProvider()
        print(f"📊 AIHandler初始化完成")

    def test_connection(self):
        """测试Ollama连接"""
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ollama连接测试失败: {e}")
            return False

    def get_ai_response(self, user_message):
        """获取AI回复 - 注入系统信息（使用最初有效的实现方式）"""
        try:
            # 获取系统信息
            system_info_text = self.system_info_provider.get_formatted_info()
            print(f"📊 系统信息已注入: {system_info_text[:100]}...")  # 调试信息
            
            # 使用最初有效的提示词结构
            prompt = f"""你是一个智能对话助手。请根据以下信息进行回复：

{system_info_text}

用户消息: {user_message}

请根据上述系统信息和用户消息进行智能回复:"""
            
            print(f"📝 完整提示内容: {prompt}")  # 调试信息
            
            # 获取模型配置
            if isinstance(self.config, dict):
                # 从配置字典中获取模型信息
                ollama_config = self.config.get('ollama', {})
                model_name = ollama_config.get('model') or self.config.get('ollama_model', 'qwen3:8b')
                ollama_url = ollama_config.get('url', 'http://localhost:11434/api/generate')
            else:
                # 兼容其他配置格式
                ollama_config = self.config.get('ollama', {}) if hasattr(self.config, 'get') else self.config
                model_name = ollama_config.get('model', self.config.get('ollama_model', 'qwen3:8b')) if hasattr(self.config, 'get') else self.config.get('ollama_model', 'qwen3:8b')
                ollama_url = ollama_config.get('url', 'http://localhost:11434/api/generate') if hasattr(self.config, 'get') else 'http://localhost:11434/api/generate'

            print(f"🔧 使用模型: {model_name}, URL: {ollama_url}")  # 调试信息

            # 构建请求数据
            data = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 200
                }
            }

            # 发送请求
            response = requests.post(ollama_url, json=data, timeout=60)
            print(f"AI请求状态码: {response.status_code}, 响应长度: {len(response.text)}")  # 调试信息

            if response.status_code == 200:
                try:
                    result = response.json()
                    full_response = result.get('response', '')
                    print(f"🤖 AI原始响应: {full_response[:100]}...")  # 调试信息

                    # 过滤思考过程
                    filtered_response = self.filter_thinking_process(full_response)
                    print(f"🤖 AI过滤后响应: {filtered_response[:100]}...")  # 调试信息

                    return filtered_response
                except json.JSONDecodeError:
                    print(f"❌ 无法解析AI响应JSON: {response.text[:200]}...")
                    return "抱歉，AI响应格式错误"
            else:
                error_msg = f"AI请求失败: {response.status_code} - {response.text}"
                print(error_msg)
                return "抱歉，暂时无法回复"

        except requests.exceptions.Timeout:
            print("⏰ AI请求超时，请检查Ollama服务状态或增加超时时间")
            return "抱歉，AI响应超时"
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到AI服务，请确保Ollama正在运行且地址正确")
            return "抱歉，无法连接到AI服务"
        except Exception as e:
            print(f"❌ 获取AI回复时发生未知错误: {e}")
            import traceback
            traceback.print_exc()  # 打印详细错误堆栈
            return "抱歉，AI服务出现错误"

    def filter_thinking_process(self, response):
        """过滤AI的思考过程，只返回最终回复"""
        import re

        # 移除<think>...</think>标签及其内容
        no_thinking = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)

        # 移除[think]...[/think]标签及其内容
        no_thinking = re.sub(r'\[think\].*?\[/think\]', '', no_thinking, flags=re.DOTALL | re.IGNORECASE)

        # 移除<!--think-->...<!--/think-->注释及其内容
        no_thinking = re.sub(r'<!--think-->.*?<!--/think-->', '', no_thinking, flags=re.DOTALL | re.IGNORECASE)

        # 移除其他可能的思考标记
        no_thinking = re.sub(r'Thought:.*?(?=AI回复:|$)', '', no_thinking, flags=re.DOTALL | re.IGNORECASE)
        no_thinking = re.sub(r'思考:.*?(?=回复:|$)', '', no_thinking, flags=re.DOTALL | re.IGNORECASE)

        # 清理多余的空白行和空格
        lines = [line.strip() for line in no_thinking.split('\n') if line.strip()]
        cleaned_response = '\n'.join(lines).strip()

        # 如果清理后为空，返回原响应的非思考部分
        if not cleaned_response:
            # 只移除思考部分，保留其他内容
            fallback = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)
            fallback = re.sub(r'\[think\].*?\[/think\]', '', fallback, flags=re.DOTALL | re.IGNORECASE)
            fallback = fallback.strip()

            if fallback:
                # 提取第一个完整句子作为回复
                sentences = re.split(r'[。！!?]', fallback)
                for sentence in sentences:
                    clean_sentence = sentence.strip()
                    if len(clean_sentence) > 0 and not clean_sentence.startswith('<') and not clean_sentence.startswith('['):
                        return clean_sentence + '。'
                return sentences[0].strip() + '。' if sentences else "我理解了，谢谢！"
            else:
                return "我理解了，谢谢！"

        return cleaned_response