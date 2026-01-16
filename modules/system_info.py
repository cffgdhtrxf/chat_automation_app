# modules/system_info.py
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