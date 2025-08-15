# config_manager.py (v1.1 - 懒加载版)

import configparser
import json
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import os # Added for BOM detection

class ConfigManager:
    """
    修改：__init__不再立即加载配置，实现"懒加载"，避免在主线程中产生I/O阻塞。
    """
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        # 禁用插值功能，避免百分号编码问题
        self.config = configparser.ConfigParser(interpolation=None)
        self.lock = threading.Lock()
        # --- 核心修改：移除这里的 self.load_config() 调用 ---

    def load_config(self):
        """从磁盘加载最新的配置。"""
        with self.lock:
            # 重新创建config对象，确保禁用插值
            self.config = configparser.ConfigParser(interpolation=None)
            
            # 检查并处理BOM问题
            self._ensure_config_file_valid()
            
            self.config.read(self.config_file, encoding='utf-8')
            return self.config
    
    def _ensure_config_file_valid(self):
        """确保配置文件格式有效，处理BOM等问题"""
        try:
            if not os.path.exists(self.config_file):
                return
            
            # 读取文件内容
            with open(self.config_file, 'rb') as f:
                content = f.read()
            
            # 检查BOM
            if content.startswith(b'\xef\xbb\xbf'):
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 检测到BOM，正在修复配置文件...")
                
                # 移除BOM并重新写入
                content_without_bom = content[3:]
                with open(self.config_file, 'wb') as f:
                    f.write(content_without_bom)
                
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] BOM已移除，配置文件已修复")
                
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 配置文件修复异常: {e}")
    
    def get_config(self):
        """获取当前内存中的配置的一个安全副本。"""
        with self.lock:
            # 创建新的config对象，禁用插值功能
            config_copy = configparser.ConfigParser(interpolation=None)
            
            # 确保配置文件有效
            self._ensure_config_file_valid()
            
            config_copy.read_dict(self.config)
            return config_copy

    def set_cookie(self, cookie_value):
        """线程安全地更新配置文件中的Cookie值。"""
        try:
            with self.lock:
                # 重新加载配置，确保使用最新的
                self.config = configparser.ConfigParser(interpolation=None)
                
                # 确保配置文件有效
                self._ensure_config_file_valid()
                
                self.config.read(self.config_file, encoding='utf-8')
                # 安全处理Cookie字符串，避免字符串插值语法错误
                safe_cookie = self._sanitize_cookie(cookie_value)
                self.config['DEFAULT']['COOKIE'] = safe_cookie
                
                # 写入配置文件时确保不产生BOM
                with open(self.config_file, 'w', encoding='utf-8-sig') as configfile:
                    self.config.write(configfile)
                
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cookie in {self.config_file} updated successfully.")
                return True
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error updating Cookie: {e}")
            return False
    
    def _sanitize_cookie(self, cookie_string):
        """安全处理Cookie字符串，处理特殊字符和编码问题"""
        try:
            # 方法1：如果Cookie包含百分号编码，先解码再重新编码
            if '%' in cookie_string:
                import urllib.parse
                # 尝试解码百分号编码
                try:
                    decoded = urllib.parse.unquote(cookie_string)
                    # 重新编码，确保一致性
                    safe_cookie = urllib.parse.quote(decoded, safe=';=,')
                except:
                    # 如果解码失败，直接使用原字符串但进行转义
                    safe_cookie = cookie_string.replace('%', '%%')
            else:
                # 没有百分号编码，直接使用
                safe_cookie = cookie_string
            
            # 确保Cookie字符串不包含可能导致配置文件解析错误的字符
            safe_cookie = safe_cookie.replace('\n', '').replace('\r', '').strip()
            
            return safe_cookie
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cookie sanitization error: {e}")
            # 如果处理失败，返回安全的默认值
            return ""

# ... (CookieUpdateHandler 和 run_cookie_server 保持不变) ...
class CookieUpdateHandler(BaseHTTPRequestHandler):
    config_manager_instance = None
    
    def _send_cors_headers(self): 
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self): 
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()
    
    def do_POST(self):
        if self.path == '/set_cookie':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)
                cookie = data.get('cookie', '')
                
                if cookie and self.config_manager_instance:
                    # 使用改进的Cookie处理方法
                    success = self.config_manager_instance.set_cookie(cookie)
                    if success:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self._send_cors_headers()
                        self.end_headers()
                        self.wfile.write(json.dumps({'status': 'ok', 'message': 'Cookie updated successfully'}).encode())
                    else:
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self._send_cors_headers()
                        self.end_headers()
                        self.wfile.write(json.dumps({'status': 'error', 'message': 'Failed to update cookie'}).encode())
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'error', 'message': 'Invalid cookie data'}).encode())
                    
            except Exception as e:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cookie update error: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode())
        else: 
            self.send_error(404, "Not Found")

def run_cookie_server(config_manager, port=28570):
    class HandlerWithManager(CookieUpdateHandler): 
        config_manager_instance = config_manager
    server_address = ('localhost', port)
    httpd = HTTPServer(server_address, HandlerWithManager)
    print(f"集成Cookie服务已在 http://localhost:{port} 上启动...")
    httpd.serve_forever()