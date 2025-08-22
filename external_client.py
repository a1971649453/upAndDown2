# external_client.py (v5.9 - 性能优化版)
# 修改时间：2024-08-22 - 剪切板频繁检测修复版本

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
import asyncio
import concurrent.futures
from datetime import datetime, timedelta
from tkinter import messagebox
import tkinter as tk
from typing import Optional, Dict, Any, Tuple
from collections import deque # Added for clipboard protection

try:
    import customtkinter as ctk
    from tkinter import ttk, scrolledtext
    CTK_AVAILABLE = True
except ImportError:
    from tkinter import ttk, scrolledtext
    CTK_AVAILABLE = False

import urllib.parse

from config_manager import ConfigManager, run_cookie_server
from network_utils import decrypt_and_parse_payload, delete_server_file


def safe_operation(operation_name="操作"):
    """异常处理装饰器，用于安全地执行可能失败的操作"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 获取调用者信息
                caller = func.__name__ if hasattr(func, '__name__') else 'unknown'
                error_msg = f"❌ {operation_name}失败 [{caller}]: {str(e)}"
                
                # 添加详细错误信息
                if hasattr(e, '__traceback__'):
                    import traceback
                    try:
                        tb_info = traceback.format_exc()
                        # 提取关键错误信息
                        lines = tb_info.split('\n')
                        error_details = []
                        for line in lines:
                            if 'File "' in line and '.py' in line:
                                error_details.append(line.strip())
                            elif 'Error:' in line or 'Exception:' in line:
                                error_details.append(line.strip())
                        
                        if error_details:
                            error_msg += f"\n   错误详情: {' | '.join(error_details[:3])}"
                    except:
                        pass
                
                # 记录错误到日志
                if args and hasattr(args[0], 'status_queue'):
                    args[0].status_queue.put(('log', (error_msg, 'error')))
                else:
                    print(error_msg)
                
                return None
        return wrapper
    return decorator


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
        # 立即输出版本标识
        print("🔍 DEBUG: external_client.py 修改版本 - 2024-08-22")
        
        self.root = root
        self.root.title("安全云剪切板 (下载端) v5.9 - 性能优化版")
        self.password = None
        self.config_manager = ConfigManager()
        self.download_dir = "./downloads/"
        self.temp_chunk_dir = os.path.join(self.download_dir, "temp_chunks")
        
        # 分片下载状态跟踪（防止重复下载）
        self.downloaded_chunks = {}  # {upload_id: set(chunk_indices)}
        self.completed_uploads = set()  # 已完成合并的upload_id集合
        self.chunks_lock = threading.Lock()  # 分片状态锁
        
        # 缓存初始化期间的日志消息
        self.init_log_cache = []
        self.ui_created = False
        
        # 智能轮询配置
        self.base_poll_interval = 5  # 基础间隔5秒
        self.current_poll_interval = 5  # 当前动态间隔
        self.max_poll_interval = 60  # 最大间隔60秒
        self.chunk_poll_interval = 1  # 分片传输时的快速轮询间隔（1秒）
        self.is_chunked_transfer = False  # 是否正在进行分片传输
        self.poll_increase_factor = 1.5  # 间隔递增因子
        self.consecutive_empty_polls = 0  # 连续空轮询计数
        self.auto_stop_minutes = 10  # 10分钟无文件自动停止
        
        # 文件过滤配置
        self.min_file_size = 100  # 最小文件大小（字节）
        self.auto_delete_invalid = True  # 自动删除无效文件
        
        # 初始化设计系统颜色（默认值，会在setup_styles中更新）
        self.colors = {
            'primary': '#3b82f6',
            'success': '#10b981', 
            'danger': '#ef4444',
            'warning': '#f59e0b',
            'text': '#0f172a',
            'text_secondary': '#64748b'
        }
        
        # 性能优化配置
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="DownloaderWorker")
        self.session = requests.Session()  # 复用连接
        self.session.headers.update({'User-Agent': 'UpAndDown2-Client/5.9'})
        
        # 性能统计
        self.stats = {
            'total_downloads': 0,
            'total_upload_time': 0.0,
            'average_response_time': 0.0,
            'last_response_time': 0.0,
            'error_count': 0,
            'start_time': time.time()
        }
        
        # 剪切板循环防护机制（优化版）
        self.clipboard_protection = {
            'last_clipboard_content': '',  # 上次剪切板内容
            'last_clipboard_time': 0,      # 上次剪切板时间
            'clipboard_change_count': 0,   # 剪切板变化计数
            'min_interval_seconds': 0.5,   # 最小间隔0.5秒（降低限制）
            'max_changes_per_minute': 30,  # 每分钟最大30次变化（提高限制）
            'change_timestamps': deque(maxlen=60),  # 变化时间戳记录
            'is_self_operation': False,    # 是否是自己操作
            'self_operation_content': '',  # 自己操作的内容
            'self_operation_expire_time': 0,  # 自己操作的过期时间
            'operation_lock': threading.Lock(),  # 操作锁
            'idle_reset_minutes': 2        # 2分钟无活动后重置状态
        }
        
        self.is_monitoring = threading.Event()
        self.monitor_thread = None
        self.status_queue = queue.Queue()
        self.download_count = 0
        self.merge_locks = {}
        self.locks_lock = threading.Lock()
        self.last_file_found_time = None
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)
        
        # 设置CustomTkinter主题
        if CTK_AVAILABLE:
            ctk.set_appearance_mode("light")  # 默认浅色主题
            ctk.set_default_color_theme("blue")  # 蓝色主题
        
        self.setup_styles()
        self.process_queue()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def run_initialization(self):
        self.status_queue.put(('log', ('🔍 开始执行初始化流程...', 'info')))
        try:
            self.status_queue.put(('log', ('正在读取安全密钥...', 'info')))
            self.password = keyring.get_password("cloud_clipboard_service", "secret_key")
            self.status_queue.put(('log', (f'🔍 密钥读取结果: {"成功" if self.password else "失败"}', 'info')))
            if not self.password:
                self.status_queue.put(('init_fail', "密钥错误: 未在系统凭据管理器中找到密钥！"))
                return

            self.status_queue.put(('log', ('正在加载配置文件...', 'info')))
            config = self.config_manager.load_config()
            
            # 强制调试信息
            self.status_queue.put(('log', ('🔍 配置对象获取成功，开始读取参数...', 'info')))
            
            self.download_dir = config['DEFAULT'].get('download_dir', './downloads/')
            self.temp_chunk_dir = os.path.join(self.download_dir, "temp_chunks")
            
            # 加载智能轮询配置
            self.base_poll_interval = int(config['DEFAULT'].get('base_poll_interval', 5))
            self.current_poll_interval = self.base_poll_interval
            self.max_poll_interval = int(config['DEFAULT'].get('max_poll_interval', 60))
            self.chunk_poll_interval = int(config['DEFAULT'].get('chunk_poll_interval_seconds', 1))
            self.poll_increase_factor = float(config['DEFAULT'].get('poll_increase_factor', 1.5))
            self.auto_stop_minutes = int(config['DEFAULT'].get('auto_stop_minutes', 10))
            
            self.status_queue.put(('log', ('🔍 轮询配置读取完成...', 'info')))
            
            # 加载文件过滤配置
            self.min_file_size = int(config['DEFAULT'].get('min_file_size', 100))
            self.auto_delete_invalid = config['DEFAULT'].get('auto_delete_invalid', 'True').lower() == 'true'
            
            # 从配置文件更新剪切板保护参数
            self.clipboard_protection['min_interval_seconds'] = float(config['DEFAULT'].get('clipboard_min_interval_seconds', 0.5))
            self.clipboard_protection['max_changes_per_minute'] = int(config['DEFAULT'].get('clipboard_max_changes_per_minute', 30))
            
            # 记录智能轮询配置
            self.status_queue.put(('log', (f'智能轮询配置加载: 基础间隔={self.base_poll_interval}s, 分片间隔={self.chunk_poll_interval}s, 最大间隔={self.max_poll_interval}s, 递增因子={self.poll_increase_factor}, 自动停止={self.auto_stop_minutes}分钟', 'info')))
            self.status_queue.put(('log', (f'文件过滤配置加载: 最小文件大小={self.min_file_size}字节, 自动删除无效文件={self.auto_delete_invalid}', 'info')))
            self.status_queue.put(('log', (f'剪切板保护配置: 最小间隔={self.clipboard_protection["min_interval_seconds"]}s, 最大变化={self.clipboard_protection["max_changes_per_minute"]}次/分钟', 'info')))
            
            if not os.path.exists(self.download_dir): os.makedirs(self.download_dir)
            if not os.path.exists(self.temp_chunk_dir): os.makedirs(self.temp_chunk_dir)

            self.status_queue.put(('log', ('正在启动内部Cookie服务...', 'info')))
            cookie_thread = threading.Thread(target=run_cookie_server, args=(self.config_manager,), daemon=True)
            cookie_thread.start()

            self.status_queue.put(('init_success', '初始化成功，应用准备就绪。'))
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.status_queue.put(('init_fail', f"初始化失败: {e}\n详细错误:\n{error_detail}"))

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
                    self.ui_created = True
                    
                    # 显示缓存的初始化日志
                    for cached_message, cached_type in self.init_log_cache:
                        self.log_message(cached_message, cached_type)
                    self.init_log_cache.clear()  # 清空缓存
                    
                    # 显示初始化成功消息
                    self.log_message(message, 'success')
                    if CTK_AVAILABLE:
                        self.start_button.configure(state='normal')
                        self.status_label.configure(text="状态: 已就绪", text_color=self.colors['success'])
                        self.status_indicator.configure(fg_color=self.colors['success_light'])
                        self.header_status.configure(text="已就绪", text_color=self.colors['success'])
                    else:
                        self.start_button.config(state='normal')
                        self.status_label.config(text="状态: 已就绪")
                elif msg_type == 'init_fail':
                    self.create_widgets()
                    self.log_message(message, 'error')
                    messagebox.showerror("启动错误", message)
                    if CTK_AVAILABLE:
                        self.status_label.configure(text="状态: 启动失败", text_color=self.colors['danger'])
                        self.status_indicator.configure(fg_color=self.colors['danger'])
                        self.header_status.configure(text="启动失败", text_color="white")
                    else:
                        self.status_label.config(text="状态: 启动失败")
                elif msg_type == 'log':
                    log_message, log_type = message
                    if self.ui_created and hasattr(self, 'log_area'):
                        # UI已创建，直接显示日志
                        self.log_message(log_message, log_type)
                    else:
                        # UI未创建，缓存日志
                        self.init_log_cache.append((log_message, log_type))
                elif msg_type == 'update_count':
                    if hasattr(self, 'count_label'):
                        if CTK_AVAILABLE:
                            # 显示更详细的统计信息
                            avg_time = self.stats['average_response_time']
                            self.count_label.configure(text=f"已下载: {self.download_count} | 平均响应: {avg_time:.1f}ms")
                        else:
                            self.count_label.config(text=f"已下载: {self.download_count}")
                            
                elif msg_type == 'monitoring_started':
                    # 监控启动完成的UI更新
                    if CTK_AVAILABLE:
                        self.start_button.configure(text="▶️  开始监控")
                        self.status_label.configure(text="状态: 智能监控中...", text_color=self.colors['success'])
                        self.status_indicator.configure(fg_color=self.colors['success_light'])
                        self.header_status.configure(text="监控中", text_color=self.colors['success'])
                    else:
                        self.start_button.config(text="▶️  开始监控")
                        self.status_label.config(text="状态: 智能监控中...")
                        
                elif msg_type == 'monitoring_stopped':
                    # 监控停止完成的UI更新
                    if CTK_AVAILABLE:
                        self.start_button.configure(state='normal')
                        self.stop_button.configure(state='disabled', text="⏸️  停止监控")
                        self.status_label.configure(text="状态: 已停止", text_color=self.colors['warning'])
                        self.status_indicator.configure(fg_color=self.colors['warning_light'])
                        self.header_status.configure(text="已停止", text_color=self.colors['warning'])
                    else:
                        self.start_button.config(state='normal')
                        self.stop_button.config(state='disabled', text="⏸️  停止监控")
                        self.status_label.config(text="状态: 已停止")
                        
                elif msg_type == 'monitoring_failed':
                    # 监控启动失败的UI更新
                    if CTK_AVAILABLE:
                        self.start_button.configure(state='normal', text="▶️  开始监控")
                        self.stop_button.configure(state='disabled')
                        self.status_label.configure(text="状态: 启动失败", text_color=self.colors['danger'])
                        self.status_indicator.configure(fg_color=self.colors['danger'])
                        self.header_status.configure(text="启动失败", text_color="white")
                    else:
                        self.start_button.config(state='normal', text="▶️  开始监控")
                        self.stop_button.config(state='disabled')
                        self.status_label.config(text="状态: 启动失败")
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def on_closing(self):
        """应用关闭时的清理工作"""
        if messagebox.askokcancel("退出", "确定要退出程序吗?"):
            # 停止监控
            self.is_monitoring.clear()
            
            # 等待线程池关闭
            try:
                self.executor.shutdown(wait=True, timeout=5.0)
                self.status_queue.put(('log', ("✅ 线程池已安全关闭", 'info')))
            except Exception as e:
                self.status_queue.put(('log', (f"⚠️ 线程池关闭异常: {e}", 'warning')))
            
            # 关闭网络会话
            try:
                self.session.close()
                self.status_queue.put(('log', ("✅ 网络会话已关闭", 'info')))
            except Exception as e:
                self.status_queue.put(('log', (f"⚠️ 会话关闭异常: {e}", 'warning')))
            
            # 安全销毁窗口
            try:
                self.root.destroy()
            except tk.TclError:
                # 窗口已经被销毁，忽略错误
                pass

    def setup_styles(self):
        if CTK_AVAILABLE:
            # LocalSend风格：清新简约色彩方案
            ctk.set_appearance_mode("light")  # 浅色主题
            self.root.configure(fg_color="#f8fafc")  # 浅灰蓝背景
            
            # 定义设计系统颜色
            self.colors = {
                'primary': '#3b82f6',      # 蓝色主色调
                'primary_hover': '#2563eb', # 深蓝悬停
                'success': '#10b981',       # 绿色成功
                'success_hover': '#059669', # 深绿悬停
                'success_light': '#d1fae5', # 浅绿色（监控中状态）
                'success_light_hover': '#a7f3d0', # 浅绿悬停
                'warning_light': '#fef3c7', # 浅橙色（启动中/停止中状态）
                'warning_light_hover': '#fde68a', # 浅橙悬停
                'danger': '#ef4444',        # 红色危险
                'danger_hover': '#dc2626',  # 深红悬停
                'warning': '#f59e0b',       # 橙色警告
                'background': '#f8fafc',    # 背景色
                'card': '#ffffff',          # 卡片背景
                'card_hover': '#f1f5f9',    # 卡片悬停
                'text': '#0f172a',          # 主文本
                'text_secondary': '#64748b', # 次要文本
                'border': '#e2e8f0',        # 边框色
                'shadow': '#00000010'       # 阴影色
            }
        else:
            # 传统Tkinter样式配置（保持向后兼容）
            style = ttk.Style(self.root)
            style.configure("TFrame", background="#f8fafc")
            style.configure("TLabel", background="#f8fafc", font=('SF Pro Display', 11))
            style.configure("TButton", font=('SF Pro Display', 11))
            style.configure("Accent.TButton", font=('SF Pro Display', 11, 'bold'))
            style.map('Accent.TButton', background=[('active', '#2563eb'), ('!disabled', '#3b82f6')],
                      foreground=[('!disabled', 'white')])
            style.configure("Stop.TButton", font=('SF Pro Display', 11, 'bold'))
            style.map('Stop.TButton', background=[('active', '#dc2626'), ('!disabled', '#ef4444')],
                      foreground=[('!disabled', 'white')])
            style.configure("TLabelframe", background="#f8fafc", borderwidth=0, relief="flat")
            style.configure("TLabelframe.Label", background="#f8fafc", font=('SF Pro Display', 12, 'bold'))

    def create_widgets(self):
        if CTK_AVAILABLE:
            self.create_modern_widgets()
        else:
            self.create_classic_widgets()
    
    def create_modern_widgets(self):
        # LocalSend风格的现代化界面
        # 主容器 - 无边框，纯净背景
        main_container = ctk.CTkFrame(self.root, 
                                     corner_radius=0, 
                                     fg_color=self.colors['background'],
                                     border_width=0)
        main_container.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)
        
        # 顶部标题卡片 - 渐变效果
        header_card = ctk.CTkFrame(main_container, 
                                  corner_radius=20, 
                                  fg_color=self.colors['card'],
                                  border_width=1,
                                  border_color=self.colors['border'],
                                  height=100)
        header_card.pack(fill=tk.X, pady=(0, 20))
        header_card.pack_propagate(False)
        
        # 标题内容
        header_content = ctk.CTkFrame(header_card, fg_color="transparent")
        header_content.pack(fill=tk.BOTH, expand=True, padx=32, pady=20)
        
        # 图标和标题
        title_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        title_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # 主标题
        title_label = ctk.CTkLabel(title_frame, 
                                  text="🛡️ 安全云剪切板", 
                                  font=ctk.CTkFont(family="SF Pro Display", size=28, weight="bold"),
                                  text_color=self.colors['text'])
        title_label.pack(anchor="w")
        
        # 副标题
        subtitle_label = ctk.CTkLabel(title_frame, 
                                     text="文件下载与同步工具 • 智能轮询 • 现代界面", 
                                     font=ctk.CTkFont(family="SF Pro Display", size=14),
                                     text_color=self.colors['text_secondary'])
        subtitle_label.pack(anchor="w", pady=(4, 0))
        
        # 右侧状态指示器
        self.status_indicator = ctk.CTkFrame(header_content, 
                                            corner_radius=12, 
                                            fg_color=self.colors['warning_light'],
                                            width=120, height=40)
        self.status_indicator.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_indicator.pack_propagate(False)
        
        self.header_status = ctk.CTkLabel(self.status_indicator, 
                                         text="初始化中", 
                                         font=ctk.CTkFont(family="SF Pro Display", size=12, weight="bold"),
                                         text_color=self.colors['warning'])
        self.header_status.pack(expand=True)
        
        # 控制面板卡片
        control_card = ctk.CTkFrame(main_container, 
                                   corner_radius=20, 
                                   fg_color=self.colors['card'],
                                   border_width=1,
                                   border_color=self.colors['border'])
        control_card.pack(fill=tk.X, pady=(0, 20))
        
        # 控制面板标题
        control_header = ctk.CTkFrame(control_card, fg_color="transparent", height=60)
        control_header.pack(fill=tk.X, padx=32, pady=(24, 0))
        control_header.pack_propagate(False)
        
        control_title = ctk.CTkLabel(control_header, 
                                    text="📋 操作控制", 
                                    font=ctk.CTkFont(family="SF Pro Display", size=18, weight="bold"),
                                    text_color=self.colors['text'])
        control_title.pack(side=tk.LEFT, pady=12)
        
        # 按钮容器
        button_container = ctk.CTkFrame(control_card, fg_color="transparent")
        button_container.pack(fill=tk.X, padx=32, pady=(0, 24))
        
        # 主要操作按钮
        self.start_button = ctk.CTkButton(button_container, 
                                         text="▶️  开始监控", 
                                         command=self.start_monitoring,
                                         height=52, width=160,
                                         font=ctk.CTkFont(family="SF Pro Display", size=15, weight="bold"),
                                         corner_radius=16,
                                         fg_color=self.colors['primary'],
                                         hover_color=self.colors['primary_hover'],
                                         state='disabled')
        self.start_button.pack(side=tk.LEFT, padx=(0, 16))
        
        self.stop_button = ctk.CTkButton(button_container, 
                                        text="⏸️  停止监控", 
                                        command=self.stop_monitoring,
                                        height=52, width=160,
                                        font=ctk.CTkFont(family="SF Pro Display", size=15, weight="bold"),
                                        corner_radius=16,
                                        fg_color=self.colors['danger'],
                                        hover_color=self.colors['danger_hover'],
                                        state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=(0, 16))
        
        # 辅助操作按钮
        self.open_folder_button = ctk.CTkButton(button_container, 
                                               text="📁  打开文件夹", 
                                               command=self.open_download_folder,
                                               height=52, width=160,
                                               font=ctk.CTkFont(family="SF Pro Display", size=15),
                                               corner_radius=16,
                                               fg_color="transparent",
                                               border_width=2,
                                               border_color=self.colors['border'],
                                               text_color=self.colors['text'],
                                               hover_color=self.colors['card_hover'])
        self.open_folder_button.pack(side=tk.RIGHT)
        
        # 状态信息卡片
        status_card = ctk.CTkFrame(main_container, 
                                  corner_radius=20, 
                                  fg_color=self.colors['card'],
                                  border_width=1,
                                  border_color=self.colors['border'])
        status_card.pack(fill=tk.X, pady=(0, 20))
        
        # 状态卡片内容
        status_content = ctk.CTkFrame(status_card, fg_color="transparent")
        status_content.pack(fill=tk.X, padx=32, pady=24)
        
        # 状态标题
        status_title = ctk.CTkLabel(status_content, 
                                   text="📊 运行状态", 
                                   font=ctk.CTkFont(family="SF Pro Display", size=18, weight="bold"),
                                   text_color=self.colors['text'])
        status_title.pack(anchor="w", pady=(0, 16))
        
        # 状态指标网格
        metrics_grid = ctk.CTkFrame(status_content, fg_color="transparent")
        metrics_grid.pack(fill=tk.X)
        
        # 左侧状态
        left_metrics = ctk.CTkFrame(metrics_grid, fg_color="transparent")
        left_metrics.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.status_label = ctk.CTkLabel(left_metrics, 
                                        text="状态: 初始化中...", 
                                        font=ctk.CTkFont(family="SF Pro Display", size=16, weight="bold"),
                                        text_color=self.colors['warning'])
        self.status_label.pack(anchor="w")
        
        # 右侧计数器
        right_metrics = ctk.CTkFrame(metrics_grid, fg_color="transparent")
        right_metrics.pack(side=tk.RIGHT)
        
        self.count_label = ctk.CTkLabel(right_metrics, 
                                       text="已下载: 0", 
                                       font=ctk.CTkFont(family="SF Pro Display", size=16),
                                       text_color=self.colors['text_secondary'])
        self.count_label.pack(anchor="e")
        
        # 日志卡片
        log_card = ctk.CTkFrame(main_container, 
                               corner_radius=20, 
                               fg_color=self.colors['card'],
                               border_width=1,
                               border_color=self.colors['border'])
        log_card.pack(fill=tk.BOTH, expand=True)
        
        # 日志头部
        log_header = ctk.CTkFrame(log_card, fg_color="transparent", height=60)
        log_header.pack(fill=tk.X, padx=32, pady=(24, 0))
        log_header.pack_propagate(False)
        
        log_title = ctk.CTkLabel(log_header, 
                                text="📝 活动日志", 
                                font=ctk.CTkFont(family="SF Pro Display", size=18, weight="bold"),
                                text_color=self.colors['text'])
        log_title.pack(side=tk.LEFT, pady=12)
        
        clear_button = ctk.CTkButton(log_header, 
                                    text="🗑️ 清空", 
                                    command=self.clear_log,
                                    width=80, height=32,
                                    font=ctk.CTkFont(family="SF Pro Display", size=12),
                                    corner_radius=10,
                                    fg_color="transparent",
                                    border_width=1,
                                    border_color=self.colors['border'],
                                    text_color=self.colors['text_secondary'],
                                    hover_color=self.colors['card_hover'])
        clear_button.pack(side=tk.RIGHT, pady=12)
        
        # 日志内容区域
        log_content = ctk.CTkFrame(log_card, 
                                  corner_radius=16, 
                                  fg_color="#f8fafc",
                                  border_width=1,
                                  border_color=self.colors['border'])
        log_content.pack(fill=tk.BOTH, expand=True, padx=32, pady=(0, 24))
        
        self.log_area = ctk.CTkTextbox(log_content, 
                                      font=ctk.CTkFont(family="JetBrains Mono", size=11),
                                      corner_radius=12,
                                      fg_color="#ffffff",
                                      border_width=0,
                                      state='disabled')
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
    def create_classic_widgets(self):
        # 经典界面（向后兼容）
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
        # LocalSend风格的日志图标
        icons = {
            'info': "💬", 
            'success': "✅", 
            'error': "❌", 
            'warning': "⚠️",
            'upload': "🚀",
            'download': "📥",
            'network': "🌐"
        }
        
        # 根据消息类型选择颜色
        colors = {
            'info': '#64748b',
            'success': '#10b981', 
            'error': '#ef4444',
            'warning': '#f59e0b',
            'upload': '#3b82f6',
            'download': '#8b5cf6',
            'network': '#06b6d4'
        }
        
        if CTK_AVAILABLE and hasattr(self.log_area, 'configure'):
            # CustomTkinter TextBox
            self.log_area.configure(state='normal')
            
            # 添加带颜色的日志条目
            log_line = f"[{timestamp}] {icons.get(msg_type, '💬')} {message}\n"
            self.log_area.insert(tk.END, log_line)
            
            self.log_area.configure(state='disabled')
            self.log_area.see(tk.END)
        else:
            # 经典ScrolledText
            self.log_area.config(state='normal')
            self.log_area.insert(tk.END, f"[{timestamp}] {icons.get(msg_type, '💬')} {message}\n")
            self.log_area.config(state='disabled')
            self.log_area.see(tk.END)

    def start_monitoring(self):
        """启动监控 - 毫秒级响应优化"""
        if not self.is_monitoring.is_set():
            # 立即UI反馈（毫秒级响应）
            if CTK_AVAILABLE:
                self.start_button.configure(state='disabled', text="⏳ 启动中...")
                self.stop_button.configure(state='normal')
                self.status_label.configure(text="状态: 正在启动...", text_color=self.colors['warning'])
                self.status_indicator.configure(fg_color=self.colors['warning_light'])
                self.header_status.configure(text="启动中", text_color=self.colors['warning'])
            else:
                self.start_button.config(state='disabled', text="⏳ 启动中...")
                self.stop_button.config(state='normal')
                self.status_label.config(text="状态: 正在启动...")
            
            # 立即强制UI更新
            self.root.update_idletasks()
            
            # 异步执行实际启动逻辑
            self.executor.submit(self._start_monitoring_async)
    
    def _start_monitoring_async(self):
        """异步启动监控逻辑"""
        try:
            # 重置轮询状态
            self.current_poll_interval = self.base_poll_interval
            self.consecutive_empty_polls = 0
            self.last_file_found_time = time.time()
            
            self.is_monitoring.set()
            
            # 更新UI状态
            self.status_queue.put(('monitoring_started', None))
            
            # 启动监控线程
            self.monitor_thread = threading.Thread(target=self.monitor_files_worker, daemon=True)
            self.monitor_thread.start()
            
            self.status_queue.put(('log', (f"🚀 智能监控已启动，初始间隔: {self.base_poll_interval}s", 'success')))
            
        except Exception as e:
            self.status_queue.put(('log', (f"❌ 启动监控失败: {e}", 'error')))
            self.status_queue.put(('monitoring_failed', None))

    def stop_monitoring(self):
        """停止监控 - 毫秒级响应优化"""
        if self.is_monitoring.is_set():
            # 立即UI反馈（毫秒级响应）
            if CTK_AVAILABLE:
                self.stop_button.configure(state='disabled', text="⏳ 停止中...")
                self.status_label.configure(text="状态: 正在停止...", text_color=self.colors['warning'])
                self.status_indicator.configure(fg_color=self.colors['warning_light'])
                self.header_status.configure(text="停止中", text_color=self.colors['warning'])
            else:
                self.stop_button.config(state='disabled', text="⏳ 停止中...")
                self.status_label.config(text="状态: 正在停止...")
            
            # 立即强制UI更新
            self.root.update_idletasks()
            
            # 异步执行实际停止逻辑
            self.executor.submit(self._stop_monitoring_async)
    
    def _stop_monitoring_async(self):
        """异步停止监控逻辑"""
        try:
            self.is_monitoring.clear()
            
            # 等待监控线程结束（最多3秒）
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=3.0)
            
            # 显示智能轮询统计信息
            uptime = time.time() - self.stats['start_time']
            stats_msg = f"📊 监控已停止 [运行时间: {uptime:.1f}s, 下载: {self.stats['total_downloads']}, 错误: {self.stats['error_count']}]"
            
            self.status_queue.put(('monitoring_stopped', None))
            self.status_queue.put(('log', (stats_msg, 'warning')))
            
        except Exception as e:
            self.status_queue.put(('log', (f"❌ 停止监控异常: {e}", 'error')))

    def open_download_folder(self):
        """打开下载文件夹 - 异步优化"""
        # 立即UI反馈
        if CTK_AVAILABLE:
            original_text = self.open_folder_button.cget("text")
            self.open_folder_button.configure(text="📂 打开中...")
        
        # 立即强制UI更新
        self.root.update_idletasks()
        
        # 异步执行文件夹打开
        def open_folder_async():
            try:
                os.startfile(os.path.abspath(self.download_dir))
                self.status_queue.put(('log', (f"📁 已打开下载文件夹: {self.download_dir}", 'info')))
            except Exception as e:
                self.status_queue.put(('log', (f"❌ 无法打开文件夹: {e}", 'error')))
            finally:
                # 恢复按钮文本
                if CTK_AVAILABLE:
                    self.root.after(500, lambda: self.open_folder_button.configure(text=original_text))
        
        self.executor.submit(open_folder_async)

    def clear_log(self):
        if CTK_AVAILABLE and hasattr(self.log_area, 'configure'):
            # CustomTkinter TextBox
            self.log_area.configure(state='normal')
            self.log_area.delete('1.0', tk.END)
            self.log_area.configure(state='disabled')
        else:
            # 经典ScrolledText
            self.log_area.config(state='normal')
            self.log_area.delete('1.0', tk.END)
            self.log_area.config(state='disabled')

    def monitor_files_worker(self):
        """智能轮询工作线程 - 动态间隔，自适应停止"""
        auto_stop_seconds = self.auto_stop_minutes * 60
        
        self.status_queue.put(('log', (f"智能轮询已启动，基础间隔: {self.base_poll_interval}s，最大间隔: {self.max_poll_interval}s", 'info')))
        
        while self.is_monitoring.is_set():
            # 执行文件检查
            files_found = self.process_files()
            
            if not self.is_monitoring.is_set():
                break
                
            # 根据检查结果调整轮询间隔
            if files_found:
                # 发现文件，检查是否是分片传输
                self.consecutive_empty_polls = 0
                self.last_file_found_time = time.time()
                
                if self.is_chunked_transfer:
                    # 分片传输中，使用快速轮询
                    self.current_poll_interval = self.chunk_poll_interval
                    self.status_queue.put(('log', (f"发现文件，分片传输快速轮询: {self.current_poll_interval}s", 'success')))
                else:
                    # 普通文件，使用基础间隔
                    self.current_poll_interval = self.base_poll_interval
                    self.status_queue.put(('log', (f"发现文件，轮询间隔重置为 {self.current_poll_interval}s", 'success')))
            else:
                # 未发现文件，检查分片传输是否完成
                if self.is_chunked_transfer:
                    # 检查是否还有未完成的分片传输
                    with self.chunks_lock:
                        has_active_chunks = any(
                            upload_id not in self.completed_uploads 
                            for upload_id in self.downloaded_chunks
                        )
                        
                    if not has_active_chunks:
                        # 所有分片传输已完成，恢复普通轮询
                        self.is_chunked_transfer = False
                        self.current_poll_interval = self.base_poll_interval
                        self.status_queue.put(('log', (f"分片传输完成，恢复正常轮询: {self.current_poll_interval}s", 'info')))
                
                # 未发现文件，增加轮询间隔（仅限非分片传输）
                if not self.is_chunked_transfer:
                    self.consecutive_empty_polls += 1
                    
                    # 每3次空轮询增加一次间隔
                    if self.consecutive_empty_polls % 3 == 0:
                        old_interval = self.current_poll_interval
                        self.current_poll_interval = min(
                            self.current_poll_interval * self.poll_increase_factor,
                            self.max_poll_interval
                        )
                        if old_interval != self.current_poll_interval:
                            self.status_queue.put(('log', (f"连续 {self.consecutive_empty_polls} 次空轮询，间隔调整为 {self.current_poll_interval:.1f}s", 'info')))
            
            # 检查自动停止条件
            if self.last_file_found_time and (time.time() - self.last_file_found_time > auto_stop_seconds):
                self.status_queue.put(('log', (f"超过 {self.auto_stop_minutes} 分钟未发现新文件，自动停止监控", 'warning')))
                self.stop_monitoring()
                break
            
            # 等待下次轮询（可中断）
            wait_start = time.time()
            while self.is_monitoring.is_set() and (time.time() - wait_start < self.current_poll_interval):
                time.sleep(0.1)  # 短暂睡眠，每100ms检查一次停止信号
        
        self.status_queue.put(('log', ("智能轮询线程已安全退出", 'info')))

    def process_files(self):
        """处理文件检查，返回是否找到文件 - 带性能监控"""
        start_time = time.time()
        config = self.config_manager.get_config()
        
        try:
            # 使用会话复用连接
            headers = {'Cookie': config['DEFAULT']['COOKIE']}
            response = self.session.post(config['DEFAULT']['QUERY_URL'], headers=headers, timeout=30)
            response.raise_for_status()
            
            # 计算响应时间
            response_time_ms = (time.time() - start_time) * 1000
            self.stats['last_response_time'] = response_time_ms
            
            # 更新平均响应时间
            if self.stats['average_response_time'] == 0:
                self.stats['average_response_time'] = response_time_ms
            else:
                self.stats['average_response_time'] = (self.stats['average_response_time'] + response_time_ms) / 2
            
            data = response.json()
            items = data.get("items", [])
            
            if not data.get("success") or not items:
                return False  # 未找到文件
            
            # 处理找到的文件
            files_processed = 0
            for item in items:
                if not self.is_monitoring.is_set():
                    break
                if item['name'].startswith("chunk_"):
                    self.handle_chunk(item, config, headers)
                    files_processed += 1
                elif item['name'].startswith("clipboard_payload_"):
                    self.handle_single_file(item, config, headers)
                    files_processed += 1
            
            if files_processed > 0:
                self.stats['total_downloads'] += files_processed
            
            return files_processed > 0  # 返回是否处理了文件
            
        except Exception as e:
            self.stats['error_count'] += 1
            error_msg = f"🌐 网络请求失败 [响应时间: {(time.time() - start_time)*1000:.1f}ms]: {e}"
            self.status_queue.put(('log', (error_msg, 'error')))
            return False  # 错误时返回未找到文件

    def handle_single_file(self, item, config, headers):
        """处理单个文件 - 异步优化版本"""
        # 异步执行文件下载和处理
        self.executor.submit(self._handle_single_file_async, item, config, headers)
    
    @safe_operation("文件处理")
    def _handle_single_file_async(self, item, config, headers):
        """异步处理单个文件"""
        start_time = time.time()
        try:
            # 添加调试信息
            self.status_queue.put(('log', (f"🔍 开始处理文件: {item.get('name', 'unknown')} (ID: {item.get('id', 'unknown')})", 'info')))
            
            dl_url = config['DEFAULT']['BASE_DOWNLOAD_URL'] + item['fileUrl']
            self.status_queue.put(('log', (f"🔗 下载URL: {dl_url}", 'info')))
            
            # 使用会话进行下载
            dl_response = self.session.get(dl_url, headers=headers, timeout=120)
            if dl_response.status_code != 200: 
                self.status_queue.put(('log', (f"❌ 下载失败，HTTP状态码: {dl_response.status_code}", 'error')))
                return
                
            self.status_queue.put(('log', (f"📥 下载成功，文件大小: {len(dl_response.content)} 字节", 'info')))
            
            # 智能文件过滤：跳过明显不是我们系统的文件
            if len(dl_response.content) < self.min_file_size:  # 文件太小，可能不是加密文件
                self.status_queue.put(('log', (f"⚠️ 跳过小文件: {item.get('name', 'unknown')} ({len(dl_response.content)} 字节 < {self.min_file_size} 字节)", 'warning')))
                # 安全修复：不删除服务器上的小文件，可能是其他用户的合法文件
                self.status_queue.put(('log', (f"💡 提示: 服务器小文件已保留，可能是其他用户的文件", 'info')))
                return
                
            # 解密和解析
            try:
                payload = decrypt_and_parse_payload(dl_response.content, self.password)
                content = base64.b64decode(payload['content_base64'])
                self.status_queue.put(('log', (f"🔓 解密成功，载荷大小: {len(content)} 字节", 'info')))
            except Exception as decrypt_error:
                error_detail = str(decrypt_error) if decrypt_error else "未知解密错误"
                self.status_queue.put(('log', (f"❌ 解密失败: {error_detail}", 'error')))
                
                # 记录文件信息用于调试
                file_info = f"文件名: {item.get('name', 'unknown')}, 大小: {len(dl_response.content)} 字节"
                self.status_queue.put(('log', (f"🔍 解密失败的文件信息: {file_info}", 'warning')))
                
                # 安全修复：只删除本地下载的文件，不删除服务器文件
                # 因为可能是其他人上传的文件，删除服务器文件会影响其他用户
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        self.status_queue.put(('log', (f"🗑️ 已删除本地解密失败的文件: {item.get('name', 'unknown')}", 'info')))
                    except Exception as e:
                        self.status_queue.put(('log', (f"⚠️ 删除本地文件失败: {str(e)}", 'warning')))
                
                self.status_queue.put(('log', (f"💡 提示: 服务器文件已保留，可能是其他用户的文件", 'info')))
                
                # 不抛出异常，直接返回，避免后续处理
                return
            
            download_time_ms = (time.time() - start_time) * 1000
            
            if payload.get('is_from_text', False):
                # 文本内容复制到剪切板
                text_content = content.decode('utf-8')
                if self._is_clipboard_change_safe(text_content):
                    self._safe_copy_to_clipboard(text_content, f"文本内容 '{payload['filename']}'")
                else:
                    self.status_queue.put(('log', (f"📝 文本内容 '{payload['filename']}' 已下载，但剪切板变化过于频繁，跳过复制 [{download_time_ms:.1f}ms]", 'warning')))
            else:
                # 文件保存
                save_path = os.path.join(self.download_dir, payload['filename'])
                with open(save_path, 'wb') as f:
                    f.write(content)
                
                # 安全复制文件路径到剪切板
                file_path = os.path.abspath(save_path)
                if self._is_clipboard_change_safe(file_path):
                    self._safe_copy_to_clipboard(file_path, f"文件路径 '{payload['filename']}'")
                else:
                    self.status_queue.put(('log', (f"📁 文件 '{payload['filename']}' 已下载，但剪切板变化过于频繁，跳过复制 [{download_time_ms:.1f}ms]", 'warning')))
                
                file_size_kb = len(content) / 1024
                self.status_queue.put(('log', (f"📁 文件 '{payload['filename']}' 已下载 [{file_size_kb:.1f}KB, {download_time_ms:.1f}ms]", 'success')))
            
            # 更新统计
            self.download_count += 1
            self.stats['total_downloads'] += 1
            self.status_queue.put(('update_count', ''))
            
            # 异步删除服务器文件
            self.executor.submit(delete_server_file, item['id'], config, self.status_queue)
            
        except Exception as e:
            self.stats['error_count'] += 1
            error_msg = f"❌ 处理单个文件失败: {str(e)}"
            if hasattr(e, '__traceback__'):
                import traceback
                tb_info = traceback.format_exc()
                error_msg += f"\n   详细错误: {tb_info.split('File')[0].strip()}"
            self.status_queue.put(('log', (error_msg, 'error')))
        except BaseException as e:
            # 捕获所有异常，包括KeyboardInterrupt等
            self.stats['error_count'] += 1
            error_msg = f"❌ 处理单个文件失败(严重错误): {str(e)}"
            if hasattr(e, '__traceback__'):
                import traceback
                tb_info = traceback.format_exc()
                error_msg += f"\n   详细错误: {tb_info.split('File')[0].strip()}"
            self.status_queue.put(('log', (error_msg, 'error')))

    def handle_chunk(self, item, config, headers):
        """处理分片文件 - 异步优化版本"""
        # 异步执行分片下载和处理
        self.executor.submit(self._handle_chunk_async, item, config, headers)
    
    @safe_operation("分片处理")
    def _handle_chunk_async(self, item, config, headers):
        """异步处理分片文件"""
        start_time = time.time()
        try:
            file_id, file_name = item['id'], item['name']
            match = re.match(r"chunk_([^_]+)_(\d+)_(\d+)_(.+)\.encrypted", file_name)
            if not match: 
                return
                
            upload_id, chunk_index_str, total_chunks_str, encoded_filename = match.groups()
            original_filename = urllib.parse.unquote(encoded_filename)
            chunk_index, total_chunks = int(chunk_index_str), int(total_chunks_str)
            
            # 检查是否已完成合并，避免重复下载
            with self.chunks_lock:
                if upload_id in self.completed_uploads:
                    self.status_queue.put(('log', (f"ℹ️ 跳过已完成的上传: {original_filename}", 'info')))
                    return
                
                # 检查该分片是否已下载
                if upload_id not in self.downloaded_chunks:
                    self.downloaded_chunks[upload_id] = set()
                    
                if chunk_index in self.downloaded_chunks[upload_id]:
                    self.status_queue.put(('log', (f"ℹ️ 跳过已下载的分片 {chunk_index}/{total_chunks} for {original_filename}", 'info')))
                    return
            
            # 标记正在进行分片传输，启用快速轮询
            self.is_chunked_transfer = True
            
            self.status_queue.put(('log', (f"📦 下载分片 {chunk_index}/{total_chunks} for {original_filename}", 'info')))
            
            # 使用会话下载分片
            dl_url = config['DEFAULT']['BASE_DOWNLOAD_URL'] + item['fileUrl']
            dl_response = self.session.get(dl_url, headers=headers, timeout=300)
            if dl_response.status_code != 200: 
                return
                
            # 解密分片内容
            try:
                payload = decrypt_and_parse_payload(dl_response.content, self.password)
                chunk_content = base64.b64decode(payload['content_base64'])
            except Exception as decrypt_error:
                error_detail = str(decrypt_error) if decrypt_error else "未知解密错误"
                self.status_queue.put(('log', (f"❌ 分片解密失败: {error_detail}", 'error')))
                
                # 记录分片信息
                chunk_info = f"分片 {chunk_index}/{total_chunks}, 文件名: {original_filename}, 大小: {len(dl_response.content)} 字节"
                self.status_queue.put(('log', (f"🔍 解密失败的分片信息: {chunk_info}", 'warning')))
                
                # 安全修复：只删除本地临时文件，不删除服务器文件
                # 因为可能是其他人上传的文件，删除服务器文件会影响其他用户
                if os.path.exists(chunk_path):
                    try:
                        os.remove(chunk_path)
                        self.status_queue.put(('log', (f"🗑️ 已删除本地解密失败的分片: {chunk_index}/{total_chunks}", 'info')))
                    except Exception as e:
                        self.status_queue.put(('log', (f"⚠️ 删除本地分片失败: {str(e)}", 'warning')))
                
                self.status_queue.put(('log', (f"💡 提示: 服务器分片已保留，可能是其他用户的文件", 'info')))
                
                # 删除已下载的分片文件并退出
                self._cleanup_temp_chunks(file_id)
                return
            
            download_time_ms = (time.time() - start_time) * 1000
            chunk_size_kb = len(chunk_content) / 1024
            
            # 保存分片文件
            upload_temp_dir = os.path.join(self.temp_chunk_dir, upload_id)
            if not os.path.exists(upload_temp_dir):
                try:
                    os.makedirs(upload_temp_dir)
                except FileExistsError:
                    pass
            
            chunk_file_path = os.path.join(upload_temp_dir, f"{chunk_index:03d}.chunk")
            with open(chunk_file_path, 'wb') as f:
                f.write(chunk_content)
            
            # 更新分片下载状态
            with self.chunks_lock:
                self.downloaded_chunks[upload_id].add(chunk_index)
                downloaded_count = len(self.downloaded_chunks[upload_id])
            
            self.status_queue.put(('log', (f"✅ 分片 {chunk_index}/{total_chunks} 已保存 [{chunk_size_kb:.1f}KB, {download_time_ms:.1f}ms] ({downloaded_count}/{total_chunks})", 'success')))
            
            # 异步删除服务器文件
            self.executor.submit(delete_server_file, file_id, config, self.status_queue)
            
            # 检查是否可以合并文件（使用锁保证线程安全）
            with self.locks_lock:
                if upload_id not in self.merge_locks:
                    self.merge_locks[upload_id] = threading.Lock()
                merge_lock = self.merge_locks[upload_id]
            
            with merge_lock:
                # 再次检查是否已完成合并，防止重复合并
                with self.chunks_lock:
                    if upload_id in self.completed_uploads:
                        return
                    
                    # 检查是否所有分片都已下载
                    if len(self.downloaded_chunks[upload_id]) == total_chunks:
                        # 标记为已完成，防止重复处理
                        self.completed_uploads.add(upload_id)
                        
                        # 异步合并文件
                        self.executor.submit(self._merge_chunks_async, upload_id, total_chunks, original_filename)
                    
        except Exception as e:
            self.stats['error_count'] += 1
            error_msg = f"❌ 处理分片失败: {str(e)}"
            if hasattr(e, '__traceback__'):
                import traceback
                tb_info = traceback.format_exc()
                error_msg += f"\n   详细错误: {tb_info.split('File')[0].strip()}"
            self.status_queue.put(('log', (error_msg, 'error')))

    @safe_operation("文件合并")
    def _merge_chunks_async(self, upload_id, total_chunks, original_filename):
        """异步合并分片文件"""
        start_time = time.time()
        self.status_queue.put(('log', (f"🔄 开始合并分片: {original_filename} ({total_chunks} 个分片)", 'info')))
        
        upload_temp_dir = os.path.join(self.temp_chunk_dir, upload_id)
        final_path = os.path.join(self.download_dir, original_filename)
        
        try:
            # 短暂等待确保所有分片都已写入完成
            time.sleep(0.1)
            
            if not os.path.isdir(upload_temp_dir):
                self.status_queue.put(('log', (f"⚠️ 合并任务已由其他线程完成: {original_filename}", 'warning')))
                return
            
            total_size = 0
            # 高效的文件合并
            with open(final_path, 'wb') as final_file:
                for i in range(total_chunks):
                    chunk_index = i + 1
                    chunk_file_path = os.path.join(upload_temp_dir, f"{chunk_index:03d}.chunk")
                    
                    if not os.path.exists(chunk_file_path):
                        raise FileNotFoundError(f"分片文件缺失: {chunk_file_path}")
                    
                    # 分块读取以节省内存
                    with open(chunk_file_path, 'rb') as chunk_file:
                        while True:
                            chunk_data = chunk_file.read(8192)  # 8KB块
                            if not chunk_data:
                                break
                            final_file.write(chunk_data)
                            total_size += len(chunk_data)
            
            # 安全复制路径到剪切板
            file_path = os.path.abspath(final_path)
            if self._is_clipboard_change_safe(file_path):
                self._safe_copy_to_clipboard(file_path, f"合并文件路径 '{original_filename}'")
            else:
                self.status_queue.put(('log', (f"🎉 文件合并成功: '{original_filename}'，但剪切板变化过于频繁，跳过复制", 'warning')))
            
            merge_time_ms = (time.time() - start_time) * 1000
            file_size_mb = total_size / (1024 * 1024)
            
            self.status_queue.put(('log', (f"🎉 文件合并成功: '{original_filename}' [{file_size_mb:.2f}MB, {merge_time_ms:.1f}ms]", 'success')))
            
            # 更新统计
            self.download_count += 1
            self.stats['total_downloads'] += 1
            self.status_queue.put(('update_count', ''))
            
        except Exception as e:
            self.stats['error_count'] += 1
            error_msg = f"❌ 合并文件失败: {str(e)}"
            if hasattr(e, '__traceback__'):
                import traceback
                tb_info = traceback.format_exc()
                error_msg += f"\n   详细错误: {tb_info.split('File')[0].strip()}"
            self.status_queue.put(('log', (error_msg, 'error')))
        finally:
            # 清理临时文件夹
            if os.path.exists(upload_temp_dir):
                try:
                    shutil.rmtree(upload_temp_dir, ignore_errors=True)
                except Exception as e:
                    self.status_queue.put(('log', (f"⚠️ 清理临时文件失败: {e}", 'warning')))
            
            # 清理状态跟踪信息
            with self.chunks_lock:
                self.downloaded_chunks.pop(upload_id, None)
                # completed_uploads 保留，用于防止重复下载
            
            # 清理锁
            with self.locks_lock:
                self.merge_locks.pop(upload_id, None)

    def merge_chunks(self, upload_id, total_chunks, original_filename):
        """保持向后兼容的合并方法"""
        self._merge_chunks_async(upload_id, total_chunks, original_filename)

    def _is_clipboard_change_safe(self, new_content: str) -> bool:
        """检查剪切板变化是否安全，防止循环（优化版）"""
        current_time = time.time()
        
        # 添加详细诊断日志 - 显示调用信息
        content_preview = new_content[:50] + '...' if len(new_content) > 50 else new_content
        self.status_queue.put(('log', (f'DEBUG 剪切板安全检查: 内容="{content_preview}", 当前时间={current_time:.1f}', 'debug')))
        
        # 添加详细配置日志
        self.status_queue.put(('log', (f'DEBUG 当前配置：间隔={self.clipboard_protection.get("min_interval_seconds", "未知")}s，限制={self.clipboard_protection.get("max_changes_per_minute", "未知")}/分钟', 'debug')))
        
        with self.clipboard_protection['operation_lock']:
            # 检查是否是自己操作（增强版 - 内容和时间双重检查）
            current_time = time.time()
            
            # 检查自身操作是否过期（2秒后过期）
            if (self.clipboard_protection['is_self_operation'] and 
                current_time > self.clipboard_protection['self_operation_expire_time']):
                self.status_queue.put(('log', ('DEBUG 自身操作标记已过期，清除标记', 'debug')))
                self.clipboard_protection['is_self_operation'] = False
                self.clipboard_protection['self_operation_content'] = ''
            
            # 检查是否是自己操作（内容匹配检查）
            if (self.clipboard_protection['is_self_operation'] and 
                new_content == self.clipboard_protection['self_operation_content']):
                self.status_queue.put(('log', ('DEBUG 检测到自身操作（内容匹配），跳过', 'debug')))
                self.clipboard_protection['is_self_operation'] = False
                self.clipboard_protection['self_operation_content'] = ''
                return False
            elif self.clipboard_protection['is_self_operation']:
                # 内容不匹配，这是一个新的操作
                self.status_queue.put(('log', ('DEBUG 内容不匹配，清除自身操作标记，继续检查', 'debug')))
                self.clipboard_protection['is_self_operation'] = False
                self.clipboard_protection['self_operation_content'] = ''
            
            # 检查内容是否相同
            if new_content == self.clipboard_protection['last_clipboard_content']:
                self.status_queue.put(('log', ('DEBUG 剪切板内容相同，跳过', 'debug')))
                return False
            
            # 检查空闲重置：2分钟无活动后重置状态
            idle_seconds = current_time - self.clipboard_protection['last_clipboard_time']
            self.status_queue.put(('log', (f'DEBUG 空闲检查：{idle_seconds:.1f}s (阈值: {self.clipboard_protection["idle_reset_minutes"] * 60}s)', 'debug')))
            if idle_seconds > (self.clipboard_protection['idle_reset_minutes'] * 60):
                # 长时间无活动，重置保护状态
                self.clipboard_protection['change_timestamps'].clear()
                self.clipboard_protection['clipboard_change_count'] = 0
                self.clipboard_protection['last_clipboard_content'] = ''  # 清理内容缓存
                self.status_queue.put(('log', ('INFO 剪切板保护状态已重置（长时间无活动）', 'info')))
                self.status_queue.put(('log', (f'DEBUG 重置后配置：间隔={self.clipboard_protection["min_interval_seconds"]}s，限制={self.clipboard_protection["max_changes_per_minute"]}/分钟', 'debug')))
            
            # 检查时间间隔
            time_diff = current_time - self.clipboard_protection['last_clipboard_time']
            self.status_queue.put(('log', (f'DEBUG 时间间隔检查：{time_diff:.1f}s (最小要求: {self.clipboard_protection["min_interval_seconds"]}s)', 'debug')))
            if time_diff < self.clipboard_protection['min_interval_seconds']:
                self.status_queue.put(('log', (f'WARNING 剪切板操作间隔过短 ({time_diff:.1f}s < {self.clipboard_protection["min_interval_seconds"]}s)', 'debug')))
                return False
            
            # 清理超过1分钟的时间戳（在检查前先清理）
            cutoff_time = current_time - 60
            old_count = len(self.clipboard_protection['change_timestamps'])
            while (self.clipboard_protection['change_timestamps'] and 
                   self.clipboard_protection['change_timestamps'][0] < cutoff_time):
                self.clipboard_protection['change_timestamps'].popleft()
            new_count = len(self.clipboard_protection['change_timestamps'])
            
            if old_count != new_count:
                self.status_queue.put(('log', (f'DEBUG 清理过期时间戳：{old_count} -> {new_count}', 'debug')))
            
            # 检查每分钟变化次数（在添加新时间戳前检查）
            changes_this_minute = len(self.clipboard_protection['change_timestamps'])
            self.status_queue.put(('log', (f'DEBUG 频率检查：{changes_this_minute}/{self.clipboard_protection["max_changes_per_minute"]} 次/分钟', 'debug')))
            
            if changes_this_minute >= self.clipboard_protection['max_changes_per_minute']:
                self.status_queue.put(('log', (f'WARNING 剪切板变化过于频繁 ({changes_this_minute}/{self.clipboard_protection["max_changes_per_minute"]} 次/分钟)，已启用防护模式', 'warning')))
                # 添加调试信息
                if self.clipboard_protection['change_timestamps']:
                    oldest = self.clipboard_protection['change_timestamps'][0]
                    newest = self.clipboard_protection['change_timestamps'][-1] if len(self.clipboard_protection['change_timestamps']) > 1 else oldest
                    self.status_queue.put(('log', (f'DEBUG 调试：时间戳范围 {oldest:.1f} - {newest:.1f}，当前时间 {current_time:.1f}', 'debug')))
                return False
            
            # 频率检查通过后，添加时间戳
            self.clipboard_protection['change_timestamps'].append(current_time)
            
            self.status_queue.put(('log', ('SUCCESS 剪切板安全检查通过，允许复制', 'debug')))
            
            # 更新状态
            self.clipboard_protection['last_clipboard_content'] = new_content
            self.clipboard_protection['last_clipboard_time'] = current_time
            self.clipboard_protection['clipboard_change_count'] += 1
            
            return True
    
    def _mark_self_operation(self, content: str):
        """标记为自身操作，避免循环（增强版）"""
        with self.clipboard_protection['operation_lock']:
            self.clipboard_protection['is_self_operation'] = True
            self.clipboard_protection['self_operation_content'] = content
            self.clipboard_protection['self_operation_expire_time'] = time.time() + 2.0  # 2秒后过期
            self.status_queue.put(('log', (f'DEBUG 标记自身操作，内容长度={len(content)}，2秒后过期', 'debug')))
    
    def _safe_copy_to_clipboard(self, content: str, operation_name: str = "操作"):
        """安全地复制到剪切板，防止循环"""
        try:
            self.status_queue.put(('log', (f'DEBUG 准备复制到剪切板: {operation_name}', 'debug')))
            
            # 标记为自身操作（传递具体内容）
            self._mark_self_operation(content)
            
            # 复制到剪切板
            pyperclip.copy(content)
            
            # 记录操作
            self.status_queue.put(('log', (f"SUCCESS {operation_name}已复制到剪切板", 'success')))
            
        except Exception as e:
            self.status_queue.put(('log', (f"ERROR 复制到剪切板失败: {e}", 'error')))
    
    def _get_clipboard_protection_status(self) -> str:
        """获取剪切板防护状态信息"""
        with self.clipboard_protection['operation_lock']:
            changes_last_minute = len(self.clipboard_protection['change_timestamps'])
            last_change_ago = time.time() - self.clipboard_protection['last_clipboard_time']
            
            return (f"防护状态: 变化{changes_last_minute}/分钟, "
                   f"上次变化{last_change_ago:.1f}秒前, "
                   f"总变化{self.clipboard_protection['clipboard_change_count']}次")

def main():
    root = None
    try:
        if not os.path.exists('config.ini'):
            messagebox.showerror("错误", "未找到 config.ini 文件！\n请先运行 config_setup.py 进行配置。")
            return
        
        # 初始化主窗口
        if CTK_AVAILABLE:
            root = ctk.CTk()
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
        try:
            if root and root.winfo_exists():
                root.quit()
        except tk.TclError:
            # 窗口已经被销毁，忽略这个错误
            pass
        except Exception as e:
            # 其他清理错误，记录但不阻止程序退出
            print(f"清理时发生错误: {e}")

if __name__ == '__main__':
    main()