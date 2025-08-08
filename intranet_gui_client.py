# intranet_gui_client.py (v4.0 - 性能优化版)
# 优化: 1. 实现内存高效的流式文件哈希计算，解决大文件内存瓶颈。
#      2. 准备与流式上传工具库对接。

import os
import sys
import hashlib
import threading
import time
import queue
import keyring
import math
import base64
import json
from collections import deque
from datetime import datetime
from tkinter import scrolledtext, messagebox, filedialog, ttk
import tkinter as tk
from ttkthemes import ThemedTk
import urllib.parse

import pyperclip
import win32clipboard
import win32con

from config_manager import ConfigManager, run_cookie_server
from network_utils import get_encryption_key, upload_data

from cryptography.fernet import Fernet

UPLOAD_CACHE = deque(maxlen=20)


class ClipboardUploaderApp:
    def __init__(self, root):
        config = ConfigManager().get_config()
        self.max_file_size_mb = int(config['DEFAULT'].get('MAX_FILE_SIZE_MB', 50))
        self.chunk_size_mb = int(config['DEFAULT'].get('CHUNK_SIZE_MB', 45))
        self.max_file_size_bytes = self.max_file_size_mb * 1024 * 1024
        self.chunk_size_bytes = self.chunk_size_mb * 1024 * 1024

        self.root = root
        self.root.title(f"安全云剪切板 (上传端) v4.0 - 性能优化版")
        self.root.geometry("850x650")
        self.root.minsize(700, 500)
        self.setup_styles()
        try:
            self.password = keyring.get_password("cloud_clipboard_service", "secret_key")
            if not self.password:
                messagebox.showerror("密钥错误", "未在系统凭据管理器中找到密钥！\n请先运行 config_setup.py 进行配置。")
                sys.exit()
        except Exception as e:
            messagebox.showerror("Keyring错误", f"无法从系统凭据管理器获取密钥: {e}\n请确保您已正确安装和配置keyring。")
            sys.exit()

        self.config_manager = ConfigManager()
        self.cookie_server_thread = threading.Thread(target=run_cookie_server, args=(self.config_manager,), daemon=True)
        self.cookie_server_thread.start()
        self.status_queue = queue.Queue()
        self.text_monitoring_enabled = tk.BooleanVar(value=False)
        self.file_monitoring_enabled = tk.BooleanVar(value=False)
        self.monitoring_active = threading.Event()
        self.monitor_thread = None
        self.create_widgets()
        self.process_queue()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        if messagebox.askokcancel("退出", "确定要退出程序吗?"):
            self.monitoring_active.clear()
            self.root.destroy()

    def setup_styles(self):
        style = ttk.Style(self.root)
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=('Segoe UI', 10))
        style.configure("TButton", font=('Segoe UI', 10))
        style.configure("Accent.TButton", font=('Segoe UI', 10, 'bold'))
        style.map('Accent.TButton',
                  background=[('active', '#005a9e'), ('!disabled', '#0078D7')],
                  foreground=[('!disabled', 'white')])
        style.configure("TLabelframe", background="#f0f0f0", borderwidth=1, relief="groove")
        style.configure("TLabelframe.Label", background="#f0f0f0", font=('Segoe UI', 11, 'bold'))

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_pane = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)
        left_pane = ttk.Frame(main_pane, padding="10")
        main_pane.add(left_pane, weight=1)
        right_pane = ttk.Frame(main_pane, padding="10")
        main_pane.add(right_pane, weight=2)
        manual_frame = ttk.LabelFrame(left_pane, text="手动上传")
        manual_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        tree_frame = ttk.Frame(manual_frame, padding=(0, 5))
        tree_frame.pack(fill=tk.BOTH, expand=True)
        cols = ('File Name', 'Size', 'Status')
        self.file_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='extended')
        self.file_tree.grid(row=0, column=0, sticky="nswe")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.file_tree.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        self.file_tree.configure(yscrollcommand=vsb.set)
        for col in cols: self.file_tree.heading(col, text=col)
        self.file_tree.column('File Name', width=200, anchor='w')
        self.file_tree.column('Size', width=80, anchor='e')
        self.file_tree.column('Status', width=80, anchor='center')
        button_panel = ttk.Frame(manual_frame, padding=(0, 10))
        button_panel.pack(fill=tk.X)
        ttk.Button(button_panel, text="📁 选择文件", command=self.select_files).pack(side=tk.LEFT, expand=True,
                                                                                    fill=tk.X, padx=(0, 5))
        ttk.Button(button_panel, text="🚀 上传已选", command=self.upload_selected_files, style="Accent.TButton").pack(
            side=tk.LEFT, expand=True, fill=tk.X)
        monitor_frame = ttk.LabelFrame(left_pane, text="自动监控")
        monitor_frame.pack(fill=tk.X, pady=10)
        ttk.Checkbutton(monitor_frame, text="监控剪切板 (文本)", variable=self.text_monitoring_enabled,
                        command=self.update_monitoring_state).pack(anchor='w', padx=10, pady=5)
        ttk.Checkbutton(monitor_frame, text="监控剪切板 (文件)", variable=self.file_monitoring_enabled,
                        command=self.update_monitoring_state).pack(anchor='w', padx=10, pady=5)
        log_frame = ttk.LabelFrame(right_pane, text="活动日志")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_area = scrolledtext.ScrolledText(log_frame, font=('Consolas', 10), state='disabled', relief='flat')
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def log_message(self, message, msg_type='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {'info': "ℹ️", 'success': "✅", 'error': "❌", 'warning': "⚠️"}
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, f"[{timestamp}] {icons.get(msg_type, 'ℹ️')} {message}\n")
        self.log_area.config(state='disabled')
        self.log_area.see(tk.END)

    def process_queue(self):
        try:
            while True: msg_type, message = self.status_queue.get_nowait(); self.log_message(message, msg_type)
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def update_monitoring_state(self):
        is_any_monitoring_on = self.text_monitoring_enabled.get() or self.file_monitoring_enabled.get()
        if is_any_monitoring_on and not (self.monitor_thread and self.monitor_thread.is_alive()):
            self.monitoring_active.set()
            self.monitor_thread = threading.Thread(target=self.clipboard_monitor_worker, daemon=True)
            self.monitor_thread.start()
            self.status_queue.put(('success', "后台监控已开启。"))
        elif not is_any_monitoring_on:
            self.monitoring_active.clear()

    def clipboard_monitor_worker(self):
        recent_text, recent_paths = "", []
        self.status_queue.put(('info', "监控线程已启动。"))
        while self.monitoring_active.is_set():
            try:
                if self.file_monitoring_enabled.get():
                    win32clipboard.OpenClipboard()
                    try:
                        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                            paths = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                            if paths and paths != recent_paths:
                                recent_paths = paths
                                for p in paths:
                                    threading.Thread(target=self.create_upload_task, args=(p,)).start()
                    finally:
                        win32clipboard.CloseClipboard()
                if self.text_monitoring_enabled.get():
                    raw_text = pyperclip.paste()
                    normalized_text = raw_text.strip()
                    if normalized_text and normalized_text != recent_text:
                        recent_text = normalized_text
                        self.process_text_upload(normalized_text)
            except Exception as e:
                self.log_message(f"剪切板访问冲突，将重试: {e}", "warning")
            time.sleep(1.5)
        self.status_queue.put(('warning', "后台监控线程已停止。"))

    def create_and_encrypt_payload(self, data_bytes, password, original_filename, is_from_text=False):
        key = get_encryption_key(password)
        fernet = Fernet(key)
        payload = {"filename": original_filename, "content_base64": base64.b64encode(data_bytes).decode('utf-8'),
                   "is_from_text": is_from_text}
        return fernet.encrypt(json.dumps(payload).encode('utf-8'))

    def process_text_upload(self, text_content):
        content_hash = hashlib.sha256(text_content.encode('utf-8')).hexdigest()
        if content_hash in UPLOAD_CACHE:
            self.status_queue.put(('info', "文本内容未变，跳过。"))
            return
        self.status_queue.put(('info', f"处理文本内容 (长度: {len(text_content)})"))
        try:
            data_bytes = text_content.encode('utf-8')
            encrypted_payload = self.create_and_encrypt_payload(data_bytes, self.password, "clipboard_text.txt",
                                                                is_from_text=True)
            config = self.config_manager.get_config()
            if upload_data(encrypted_payload, config, self.status_queue):
                UPLOAD_CACHE.append(content_hash)
        except Exception as e:
            self.status_queue.put(('error', f"处理文本时出错: {e}"))

    def get_file_size(self, file_size_or_path):
        try:
            if isinstance(file_size_or_path, str):
                size = os.path.getsize(file_size_or_path)
            else:
                size = file_size_or_path
            if size < 1024:
                return f"{size} B"
            elif size < 1024 ** 2:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / 1024 ** 2:.1f} MB"
        except FileNotFoundError:
            return "N/A"

    def select_files(self):
        filepaths = filedialog.askopenfilenames()
        if filepaths:
            for path in filepaths:
                if not self.file_tree.exists(path):
                    size_str = self.get_file_size(path)
                    self.file_tree.insert('', tk.END, iid=path, values=(os.path.basename(path), size_str, '待上传'))

    def upload_selected_files(self):
        selected_items = self.file_tree.selection()
        if not selected_items:
            messagebox.showwarning("提示", "没有在列表中选择任何文件。")
            return
        self.log_message(f"开始手动上传 {len(selected_items)} 个文件...", 'info')
        for item_id in selected_items:
            threading.Thread(target=self.create_upload_task, args=(item_id, item_id)).start()

    # --- 新增：内存高效的哈希计算方法 ---
    def hash_file_streamed(self, file_path, item_id=None):
        size_str = self.get_file_size(file_path)
        if item_id: self.file_tree.item(item_id, values=(os.path.basename(file_path), size_str, '计算哈希..'))

        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.status_queue.put(('error', f"计算文件哈希时出错: {e}"))
            return None

    # --- 修改：使用新的流式哈希方法 ---
    def create_upload_task(self, file_path, item_id=None):
        size_str = "N/A"
        try:
            if not os.path.exists(file_path):
                self.status_queue.put(('error', f"文件不存在: {file_path}"))
                if item_id: self.file_tree.item(item_id, values=(os.path.basename(file_path), size_str, '错误'))
                return

            size_str = self.get_file_size(file_path)
            if item_id: self.file_tree.item(item_id, values=(os.path.basename(file_path), size_str, '排队中'))

            # 使用新的流式哈希方法，不再将整个文件读入内存
            content_hash = self.hash_file_streamed(file_path, item_id)
            if not content_hash:
                if item_id: self.file_tree.item(item_id, values=(os.path.basename(file_path), size_str, '哈希失败'))
                return

            if content_hash in UPLOAD_CACHE:
                self.status_queue.put(('info', f"文件 '{os.path.basename(file_path)}' 内容未变，跳过。"))
                if item_id: self.file_tree.item(item_id, values=(os.path.basename(file_path), size_str, '已跳过'))
                return

            file_size = os.path.getsize(file_path)
            if file_size > self.chunk_size_bytes:
                self.process_chunk_upload(file_path, file_size, item_id)
            else:
                self.process_single_upload(file_path, item_id)

            # 移到各自的处理函数中，在成功上传后添加
            # UPLOAD_CACHE.append(content_hash)

        except Exception as e:
            self.status_queue.put(('error', f"创建上传任务时出错: {e}"))
            if item_id:
                self.file_tree.item(item_id, values=(os.path.basename(file_path), size_str, '错误'))

    def process_single_upload(self, file_path, item_id=None):
        size_str = self.get_file_size(file_path)
        if item_id: self.file_tree.item(item_id, values=(os.path.basename(file_path), size_str, '处理中'))

        with open(file_path, 'rb') as f:
            data_bytes = f.read()
        encrypted_payload = self.create_and_encrypt_payload(data_bytes, self.password, os.path.basename(file_path))

        config = self.config_manager.get_config()
        if upload_data(encrypted_payload, config, self.status_queue):
            # 成功上传后才添加到缓存
            with open(file_path, 'rb') as f:
                UPLOAD_CACHE.append(hashlib.sha256(f.read()).hexdigest())
            if item_id: self.file_tree.item(item_id, values=(os.path.basename(file_path), size_str, '成功'))
        else:
            if item_id: self.file_tree.item(item_id, values=(os.path.basename(file_path), size_str, '失败'))

    def process_chunk_upload(self, file_path, file_size, item_id=None):
        self.status_queue.put(('info', f"文件过大，启动分片上传: {os.path.basename(file_path)}"))
        original_filename = os.path.basename(file_path)
        encoded_filename = urllib.parse.quote(original_filename)
        upload_id = f"{int(time.time())}-{base64.urlsafe_b64encode(os.urandom(4)).decode()}"
        total_chunks = math.ceil(file_size / self.chunk_size_bytes)
        config = self.config_manager.get_config()

        success = True
        with open(file_path, 'rb') as f:
            for i in range(total_chunks):
                chunk_data = f.read(self.chunk_size_bytes)
                if not chunk_data: break
                chunk_index = i + 1
                status_msg = f"分片 {chunk_index}/{total_chunks}"
                if item_id: self.file_tree.item(item_id,
                                                values=(original_filename, self.get_file_size(file_size), status_msg))

                encrypted_payload = self.create_and_encrypt_payload(chunk_data, self.password, original_filename)
                chunk_filename = f"chunk_{upload_id}_{chunk_index:03d}_{total_chunks:03d}_{encoded_filename}.encrypted"

                if not upload_data(encrypted_payload, config, self.status_queue, custom_filename=chunk_filename):
                    self.status_queue.put(('error', f"分片 {chunk_index} 上传失败，已终止任务。"))
                    if item_id: self.file_tree.item(item_id,
                                                    values=(original_filename, self.get_file_size(file_size), '失败'))
                    success = False
                    break

        if success:
            self.status_queue.put(('success', f"文件 {original_filename} 所有分片上传完毕。"))
            if item_id: self.file_tree.item(item_id, values=(original_filename, self.get_file_size(file_size), '完成'))
            with open(file_path, 'rb') as f:
                UPLOAD_CACHE.append(hashlib.sha256(f.read()).hexdigest())


if __name__ == '__main__':
    if not os.path.exists('config.ini'):
        messagebox.showerror("错误", "未找到 config.ini 文件！\n请先运行 config_setup.py 进行配置。")
        sys.exit()

    try:
        root = ThemedTk(theme="plastik")
    except Exception:
        root = tk.Tk()

    app = ClipboardUploaderApp(root)
    root.mainloop()