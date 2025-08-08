# external_client.py (v5.5 - 超时停止版)

import os
import sys
import time
import base64
import re
import shutil
import requests
import pyperclip
import threading
import queue
import keyring
from datetime import datetime
from tkinter import ttk, scrolledtext, messagebox
import tkinter as tk

try:
    from ttkthemes import ThemedTk
    THEMED_TK_AVAILABLE = True
except ImportError:
    THEMED_TK_AVAILABLE = False

import urllib.parse

from config_manager import ConfigManager, run_cookie_server
from network_utils import decrypt_and_parse_payload, delete_server_file


# --- 加载屏类 (无变化) ---
class SplashScreen:
    def __init__(self, parent):
        self.root = tk.Toplevel(parent)
        self.root.title("启动中")
        self.root.geometry("300x150+500+300")
        self.root.overrideredirect(True)
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(expand=True, fill=tk.BOTH)
        style = ttk.Style(self.root)
        style.configure("Splash.TFrame", background="#0078D7")
        style.configure("Splash.TLabel", background="#0078D7", foreground="white", font=('Segoe UI', 10))
        style.layout("Splash.TProgressbar", style.layout("Horizontal.TProgressbar"))
        style.configure("Splash.TProgressbar", troughcolor='#005a9e', background='#ffffff')
        main_frame.config(style="Splash.TFrame")
        ttk.Label(main_frame, text="安全云剪切板 (下载端)", style="Splash.TLabel", font=('Segoe UI', 14, "bold")).pack(
            pady=(0, 10))
        self.status_label = ttk.Label(main_frame, text="正在加载，请稍候...", style="Splash.TLabel")
        self.status_label.pack(pady=5)
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', style="Splash.TProgressbar")
        self.progress.pack(pady=10, fill=tk.X, padx=5)
        self.progress.start(15)

    def close(self):
        self.progress.stop()
        self.root.destroy()


# --- 主应用类 (修正版) ---
class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("安全云剪切板 (下载端) v5.5 - 超时停止版")
        self.password = None
        self.config_manager = ConfigManager()
        self.download_dir = "./downloads/"
        self.temp_chunk_dir = os.path.join(self.download_dir, "temp_chunks")
        self.poll_interval = 10
        self.is_monitoring = threading.Event()
        self.monitor_thread = None
        self.status_queue = queue.Queue()
        self.download_count = 0
        self.merge_locks = {}
        self.locks_lock = threading.Lock()
        self.last_file_found_time = None
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        self.setup_styles()
        self.process_queue()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def run_initialization(self):
        try:
            self.status_queue.put(('log', ('正在读取安全密钥...', 'info')))
            self.password = keyring.get_password("cloud_clipboard_service", "secret_key")
            if not self.password:
                self.status_queue.put(('init_fail', "密钥错误: 未在系统凭据管理器中找到密钥！"))
                return

            self.status_queue.put(('log', ('正在加载配置文件...', 'info')))
            config = self.config_manager.load_config()
            self.download_dir = config['DEFAULT']['DOWNLOAD_DIR']
            self.temp_chunk_dir = os.path.join(self.download_dir, "temp_chunks")
            self.poll_interval = int(config['DEFAULT'].get('POLL_INTERVAL_SECONDS', 10))
            if not os.path.exists(self.download_dir): os.makedirs(self.download_dir)
            if not os.path.exists(self.temp_chunk_dir): os.makedirs(self.temp_chunk_dir)

            self.status_queue.put(('log', ('正在启动内部Cookie服务...', 'info')))
            cookie_thread = threading.Thread(target=run_cookie_server, args=(self.config_manager,), daemon=True)
            cookie_thread.start()

            self.status_queue.put(('init_success', '初始化成功，应用准备就绪。'))
        except Exception as e:
            self.status_queue.put(('init_fail', f"初始化失败: {e}"))

    def process_queue(self):
        try:
            while True:
                msg_type, message = self.status_queue.get_nowait()
                if msg_type == 'loader_done':
                    splash_screen = message
                    splash_screen.close()
                    self.root.deiconify()
                    continue
                if msg_type == 'init_success':
                    self.create_widgets()
                    self.log_message(message, 'success')
                    self.start_button.config(state='normal')
                    self.status_label.config(text="状态: 已就绪")
                elif msg_type == 'init_fail':
                    self.create_widgets()
                    self.log_message(message, 'error')
                    messagebox.showerror("启动错误", message)
                    self.status_label.config(text="状态: 启动失败")
                elif msg_type == 'log':
                    if hasattr(self, 'log_area'):
                        log_message, log_type = message
                        self.log_message(log_message, log_type)
                elif msg_type == 'update_count':
                    if hasattr(self, 'count_label'):
                        self.count_label.config(text=f"已下载: {self.download_count}")
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def on_closing(self):
        if messagebox.askokcancel("退出", "确定要退出程序吗?"):
            self.is_monitoring.clear()
            self.root.destroy()

    def setup_styles(self):
        style = ttk.Style(self.root)
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=('Segoe UI', 10))
        style.configure("TButton", font=('Segoe UI', 10))
        style.configure("Accent.TButton", font=('Segoe UI', 10, 'bold'))
        style.map('Accent.TButton', background=[('active', '#2E7D32'), ('!disabled', '#9E9E9E')],
                  foreground=[('!disabled', 'white')])
        style.configure("Stop.TButton", font=('Segoe UI', 10, 'bold'))
        style.map('Stop.TButton', background=[('active', '#c62828'), ('!disabled', '#F44336')],
                  foreground=[('!disabled', 'white')])
        style.configure("TLabelframe", background="#f0f0f0", borderwidth=1, relief="groove")
        style.configure("TLabelframe.Label", background="#f0f0f0", font=('Segoe UI', 11, 'bold'))

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_frame.pack(fill=tk.X)
        self.start_button = ttk.Button(control_frame, text="🚀 开始监控", command=self.start_monitoring, style="Accent.TButton", state='disabled')
        self.start_button.pack(side=tk.LEFT, padx=5, ipady=5)
        self.stop_button = ttk.Button(control_frame, text="⏹️ 停止监控", command=self.stop_monitoring, state='disabled', style="Stop.TButton")
        self.stop_button.pack(side=tk.LEFT, padx=5, ipady=5)
        self.open_folder_button = ttk.Button(control_frame, text="📁 打开下载文件夹", command=self.open_download_folder)
        self.open_folder_button.pack(side=tk.RIGHT, padx=5, ipady=5)
        status_frame = ttk.LabelFrame(main_frame, text="状态", padding="10")
        status_frame.pack(fill=tk.X, pady=10)
        self.status_label = ttk.Label(status_frame, text="状态: 初始化中...", font=('Segoe UI', 10, 'bold'))
        self.status_label.pack(side=tk.LEFT, padx=5)
        self.count_label = ttk.Label(status_frame, text="已下载: 0")
        self.count_label.pack(side=tk.LEFT, padx=20)
        log_frame = ttk.LabelFrame(main_frame, text="活动日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_area = scrolledtext.ScrolledText(log_frame, font=('Consolas', 10), state='disabled', relief='flat')
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Button(log_frame, text="清除日志", command=self.clear_log).pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

    def log_message(self, message, msg_type='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {'info': "ℹ️", 'success': "✅", 'error': "❌", 'warning': "⚠️"}
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, f"[{timestamp}] {icons.get(msg_type, 'ℹ️')} {message}\n")
        self.log_area.config(state='disabled')
        self.log_area.see(tk.END)

    def start_monitoring(self):
        if not self.is_monitoring.is_set():
            self.is_monitoring.set()
            self.last_file_found_time = time.time()
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.status_label.config(text="状态: 监控中...")
            self.monitor_thread = threading.Thread(target=self.monitor_files_worker, daemon=True)
            self.monitor_thread.start()
            self.status_queue.put(('log', ("监控已启动", 'success')))

    def stop_monitoring(self):
        if self.is_monitoring.is_set():
            self.is_monitoring.clear()
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.status_label.config(text="状态: 已停止")
            self.status_queue.put(('log', ("监控已停止，等待当前轮询结束...", 'warning')))

    def open_download_folder(self):
        try:
            os.startfile(os.path.abspath(self.download_dir))
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹: {e}")

    def clear_log(self):
        self.log_area.config(state='normal')
        self.log_area.delete('1.0', tk.END)
        self.log_area.config(state='disabled')

    def monitor_files_worker(self):
        AUTO_STOP_SECONDS = 300
        while self.is_monitoring.is_set():
            self.process_files()
            if self.is_monitoring.is_set():
                if self.last_file_found_time and (time.time() - self.last_file_found_time > AUTO_STOP_SECONDS):
                    self.status_queue.put(('log', (f"超过 {AUTO_STOP_SECONDS // 60} 分钟未发现新文件，自动停止监控。", 'warning')))
                    self.stop_monitoring()
            self.is_monitoring.wait(self.poll_interval)
        self.status_queue.put(('log', ("监控线程已安全退出。", 'info')))

    def process_files(self):
        config = self.config_manager.get_config()
        headers = {'Cookie': config['DEFAULT']['COOKIE'], 'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.post(config['DEFAULT']['QUERY_URL'], headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
            if not data.get("success") or not items:
                return
            self.last_file_found_time = time.time()
            for item in items:
                if not self.is_monitoring.is_set():
                    break
                if item['name'].startswith("chunk_"):
                    self.handle_chunk(item, config, headers)
                elif item['name'].startswith("clipboard_payload_"):
                    self.handle_single_file(item, config, headers)
        except Exception as e:
            self.status_queue.put(('log', (f"轮询时发生错误: {e}", 'error')))

    def handle_single_file(self, item, config, headers):
        try:
            dl_url = config['DEFAULT']['BASE_DOWNLOAD_URL'] + item['fileUrl']
            dl_response = requests.get(dl_url, headers=headers, timeout=120)
            if dl_response.status_code != 200: return
            payload = decrypt_and_parse_payload(dl_response.content, self.password)
            content = base64.b64decode(payload['content_base64'])
            if payload.get('is_from_text', False):
                pyperclip.copy(content.decode('utf-8'))
                self.status_queue.put(('log', (f"文本内容 '{payload['filename']}' 已复制到剪切板。", 'success')))
            else:
                save_path = os.path.join(self.download_dir, payload['filename'])
                with open(save_path, 'wb') as f:
                    f.write(content)
                pyperclip.copy(os.path.abspath(save_path))
                self.status_queue.put(('log', (f"文件 '{payload['filename']}' 已下载并复制路径。", 'success')))
            self.download_count += 1
            self.status_queue.put(('update_count', ''))
            threading.Thread(target=delete_server_file, args=(item['id'], config, self.status_queue), daemon=True).start()
        except Exception as e:
            self.status_queue.put(('log', (f"处理单个文件时出错: {e}", 'error')))

    def handle_chunk(self, item, config, headers):
        try:
            file_id, file_name = item['id'], item['name']
            match = re.match(r"chunk_([^_]+)_(\d+)_(\d+)_(.+)\.encrypted", file_name)
            if not match: return
            upload_id, chunk_index_str, total_chunks_str, encoded_filename = match.groups()
            original_filename = urllib.parse.unquote(encoded_filename)
            chunk_index, total_chunks = int(chunk_index_str), int(total_chunks_str)
            self.status_queue.put(('log', (f"下载分片 {chunk_index}/{total_chunks} for {original_filename}", 'info')))
            dl_url = config['DEFAULT']['BASE_DOWNLOAD_URL'] + item['fileUrl']
            dl_response = requests.get(dl_url, headers=headers, timeout=300)
            if dl_response.status_code != 200: return
            payload = decrypt_and_parse_payload(dl_response.content, self.password)
            chunk_content = base64.b64decode(payload['content_base64'])
            upload_temp_dir = os.path.join(self.temp_chunk_dir, upload_id)
            if not os.path.exists(upload_temp_dir):
                try:
                    os.makedirs(upload_temp_dir)
                except FileExistsError:
                    pass
            chunk_file_path = os.path.join(upload_temp_dir, f"{chunk_index:03d}.chunk")
            with open(chunk_file_path, 'wb') as f:
                f.write(chunk_content)
            threading.Thread(target=delete_server_file, args=(file_id, config, self.status_queue), daemon=True).start()
            with self.locks_lock:
                if upload_id not in self.merge_locks:
                    self.merge_locks[upload_id] = threading.Lock()
                merge_lock = self.merge_locks[upload_id]
            with merge_lock:
                if not os.path.exists(upload_temp_dir): return
                if len(os.listdir(upload_temp_dir)) == total_chunks:
                    self.merge_chunks(upload_id, total_chunks, original_filename)
        except Exception as e:
            self.status_queue.put(('log', (f"处理分片时出错: {e}", 'error')))

    def merge_chunks(self, upload_id, total_chunks, original_filename):
        self.status_queue.put(('log', (f"所有分片接收完毕，开始合并: {original_filename}", 'success')))
        upload_temp_dir = os.path.join(self.temp_chunk_dir, upload_id)
        final_path = os.path.join(self.download_dir, original_filename)
        try:
            time.sleep(0.5)
            if not os.path.isdir(upload_temp_dir):
                self.status_queue.put(('log', (f"合并任务已由其他线程完成: {original_filename}", 'warning')))
                return
            with open(final_path, 'wb') as final_file:
                for i in range(total_chunks):
                    chunk_index = i + 1
                    chunk_file_path = os.path.join(upload_temp_dir, f"{chunk_index:03d}.chunk")
                    with open(chunk_file_path, 'rb') as chunk_file:
                        final_file.write(chunk_file.read())
            pyperclip.copy(os.path.abspath(final_path))
            self.status_queue.put(('log', (f"文件合并成功: {final_path}，路径已复制。", 'success')))
            self.download_count += 1
            self.status_queue.put(('update_count', ''))
        except Exception as e:
            self.status_queue.put(('log', (f"合并文件时出错: {e}", 'error')))
        finally:
            if os.path.exists(upload_temp_dir):
                shutil.rmtree(upload_temp_dir, ignore_errors=True)
            with self.locks_lock:
                self.merge_locks.pop(upload_id, None)

def main():
    root = None
    try:
        if not os.path.exists('config.ini'):
            messagebox.showerror("错误", "未找到 config.ini 文件！\n请先运行 config_setup.py 进行配置。")
            return
        if THEMED_TK_AVAILABLE:
            root = ThemedTk(theme="plastik")
        else:
            root = tk.Tk()
        root.withdraw()
        splash = SplashScreen(root)
        app = DownloaderApp(root)
        def loader_task():
            app.run_initialization()
            app.status_queue.put(('loader_done', splash))
        threading.Thread(target=loader_task, daemon=True).start()
        root.mainloop()
    except Exception as e:
        messagebox.showerror("严重错误", f"应用发生无法恢复的错误: {e}")
    finally:
        if root and root.winfo_exists():
            root.quit()

if __name__ == '__main__':
    main()