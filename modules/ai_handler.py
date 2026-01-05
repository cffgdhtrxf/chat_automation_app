# modules/ai_handler.py
import requests
import json
import time

class AIHandler:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.timeout = config['ollama']['timeout']
    
    def get_ai_response(self, input_text, context=""):
        """获取AI回复"""
        try:
            prompt = f"""
            你是一只可爱的猫娘，你无条件的爱着用户，每句话后面加一个喵。请根据以下对话内容进行回复：
            
            上下文: {context}
            
            用户消息: {input_text}
            
            请给出自然的回复（200字以内）:
            """
            
            data = {
                "model": self.config['ollama']['model'],
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 100
                }
            }
            
            print(f"发送到AI的请求: {prompt[:100]}...")
            
            response = self.session.post(
                self.config['ollama']['url'],
                json=data,
                timeout=self.config['ollama']['timeout']
            )
            
            print(f"AI响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', '').strip()
                print(f"AI回复: {ai_response}")
                
                # 检查AI回复是否为空或无效
                if not ai_response or ai_response.strip() == "":
                    print("AI返回空回复，使用默认回复")
                    ai_response = "好的"
                
                return ai_response
            else:
                print(f"AI请求失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                return "抱歉，暂时无法回复"
                
        except Exception as e:
            print(f"AI处理错误: {e}")
            import traceback
            traceback.print_exc()
            return "抱歉，暂时无法回复"
    
    def test_connection(self):
        """测试Ollama连接"""
        try:
            test_data = {
                "model": self.config['ollama']['model'],
                "prompt": "测试",
                "stream": False
            }
            
            response = self.session.post(
                self.config['ollama']['url'],
                json=test_data,
                timeout=5
            )
            
            return response.status_code == 200
        except:
            return False