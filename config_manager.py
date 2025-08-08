# config_manager.py (v1.1 - 懒加载版)

import configparser
import json
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class ConfigManager:
    """
    修改：__init__不再立即加载配置，实现“懒加载”，避免在主线程中产生I/O阻塞。
    """
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.lock = threading.Lock()
        # --- 核心修改：移除这里的 self.load_config() 调用 ---

    def load_config(self):
        """从磁盘加载最新的配置。"""
        with self.lock:
            self.config.read(self.config_file, encoding='utf-8')
            return self.config

    def get_config(self):
        """获取当前内存中的配置的一个安全副本。"""
        with self.lock:
            config_copy = configparser.ConfigParser()
            config_copy.read_dict(self.config)
            return config_copy

    def set_cookie(self, cookie_value):
        """线程安全地更新配置文件中的Cookie值。"""
        with self.lock:
            self.config.read(self.config_file, encoding='utf-8')
            self.config['DEFAULT']['COOKIE'] = cookie_value
            with open(self.config_file, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cookie in {self.config_file} updated.")

# ... (CookieUpdateHandler 和 run_cookie_server 保持不变) ...
class CookieUpdateHandler(BaseHTTPRequestHandler):
    config_manager_instance = None
    def _send_cors_headers(self): self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS'); self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    def do_OPTIONS(self): self.send_response(204); self._send_cors_headers(); self.end_headers()
    def do_POST(self):
        if self.path == '/set_cookie':
            try:
                content_length = int(self.headers['Content-Length']); post_data = self.rfile.read(content_length); data = json.loads(post_data); cookie = data.get('cookie', '')
                if cookie and self.config_manager_instance: self.config_manager_instance.set_cookie(cookie)
                self.send_response(200); self.send_header('Content-type', 'application/json'); self._send_cors_headers(); self.end_headers(); self.wfile.write(json.dumps({'status': 'ok'}).encode())
            except Exception as e: self.send_error(500, str(e))
        else: self.send_error(404, "Not Found")
def run_cookie_server(config_manager, port=28570):
    class HandlerWithManager(CookieUpdateHandler): config_manager_instance = config_manager
    server_address = ('localhost', port); httpd = HTTPServer(server_address, HandlerWithManager); print(f"集成Cookie服务已在 http://localhost:{port} 上启动..."); httpd.serve_forever()