# intranet_gui_client_optimized.py - v5.1 优化版
# 基于Sprint计划实现：
# 1. 上下布局优化：主功能区(3/4) + 活动日志(1/4)
# 2. 修复剪切板监听：智能间隔调整(0.5-2秒)，混合策略检测
# 3. 文件自动清理：完成状态4秒延迟清理
# 4. 集成性能监控日志输出
# 5. 移除一键上传功能，简化界面

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
from datetime import datetime, timedelta
from tkinter import scrolledtext, messagebox, filedialog, ttk
import tkinter as tk
import urllib.parse
from typing import Optional, Dict, Any, Tuple
import concurrent.futures

# CustomTkinter现代化UI支持（带降级处理）
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

# 剪切板操作库
import pyperclip
try:
    import win32clipboard
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

from config_manager import ConfigManager, run_cookie_server
from network_utils import get_encryption_key, upload_data
from cryptography.fernet import Fernet

# 全局缓存和配置
UPLOAD_CACHE = deque(maxlen=20)

# 设计系统颜色配置
COLOR_SCHEME = {
    'modern': {
        'primary': '#3b82f6',
        'primary_hover': '#2563eb', 
        'success': '#10b981',
        'warning': '#f59e0b',
        'danger': '#ef4444',
        'surface': '#f8fafc',
        'surface_variant': '#e2e8f0',
        'text': '#0f172a',
        'text_secondary': '#64748b',
        'border': '#d1d5db'
    },
    'legacy': {
        'primary': '#0078D7',
        'primary_hover': '#005a9e',
        'success': '#107c10',
        'warning': '#ff8c00', 
        'danger': '#d13438',
        'surface': '#f0f0f0',
        'surface_variant': '#e0e0e0',
        'text': '#000000',
        'text_secondary': '#666666',
        'border': '#cccccc'
    }
}


class OptimizedClipboardUploader:
    """优化版云内端上传工具 v5.1
    
    核心优化:
    - 上下布局：主功能区75% + 日志区25%
    - 智能剪切板监听：动态间隔调整(0.5-2秒)
    - 自动文件清理：完成状态4秒延迟清理
    - 性能监控集成：实时状态跟踪
    - 简化界面：移除一键上传，专注核心功能
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("安全云剪切板 (上传端) v5.1 - 优化版")
        self.root.geometry("900x700")
        self.root.minsize(750, 550)
        
        # UI框架检测和配置
        self.ui_framework = 'ctk' if CTK_AVAILABLE else 'tkinter'
        self.colors = COLOR_SCHEME['modern'] if CTK_AVAILABLE else COLOR_SCHEME['legacy']
        
        # 性能优化配置
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=3, thread_name_prefix="UploadWorker"
        )
        
        # 智能监听配置 - 优化间隔策略
        self.clipboard_monitor_config = {
            'base_interval': 0.5,      # 基础间隔0.5秒
            'current_interval': 0.5,   # 当前动态间隔
            'max_interval': 2.0,       # 最大间隔2秒
            'increase_factor': 1.2,    # 间隔递增因子
            'activity_reset_factor': 0.8,  # 活动时重置因子
            'consecutive_idle_count': 0,    # 连续空闲计数
            'last_content_hash': '',        # 上次内容哈希
            'last_file_paths': [],          # 上次文件路径
        }
        
        # 文件清理配置 - 4秒延迟
        self.file_cleanup_config = {
            'completion_delay': 4.0,   # 完成后4秒延迟
            'cleanup_enabled': True,   # 启用自动清理
            'pending_cleanups': {},    # 待清理文件映射
        }
        
        # 剪切板循环防护机制
        self.clipboard_protection = {
            'last_text_content': '',       # 上次文本内容
            'last_text_hash': '',          # 上次文本哈希
            'last_file_paths': [],         # 上次文件路径
            'last_change_time': 0,         # 上次变化时间
            'min_interval_seconds': 1.5,   # 最小间隔1.5秒
            'max_changes_per_minute': 15,  # 每分钟最大变化次数
            'change_timestamps': deque(maxlen=60),  # 变化时间戳记录
            'is_self_operation': False,    # 是否是自己操作
            'operation_lock': threading.Lock(),  # 操作锁
            'content_blacklist': set(),    # 内容黑名单（最近处理过的）
            'blacklist_max_size': 50      # 黑名单最大大小
        }
        
        # 性能统计
        self.performance_stats = {
            'total_uploads': 0,
            'successful_uploads': 0, 
            'total_upload_time': 0.0,
            'clipboard_checks': 0,
            'startup_time': time.time(),
            'last_activity_time': time.time()
        }
        
        # 初始化系统
        self._init_configuration()
        self._setup_ui_framework()
        self._init_security()
        self._init_components()
        self._create_optimized_ui()
        self._start_services()
        
        # 设置窗口关闭处理
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self._log_system_info()
        
    def _init_configuration(self):
        """初始化配置系统"""
        try:
            self.config_manager = ConfigManager()
            # 修复1: 必须先调用load_config()才能读取配置文件
            config = self.config_manager.load_config()
            # 修复2: 使用小写键名匹配配置文件中的实际键名
            self.max_file_size_mb = int(config['DEFAULT'].get('max_file_size_mb', 6))
            self.chunk_size_mb = int(config['DEFAULT'].get('chunk_size_mb', 3)) 
            self.max_file_size_bytes = self.max_file_size_mb * 1024 * 1024
            self.chunk_size_bytes = self.chunk_size_mb * 1024 * 1024
            self.poll_interval = float(config['DEFAULT'].get('poll_interval_seconds', 10))
            
            self._log_message(f"配置加载成功: 文件限制{self.max_file_size_mb}MB, 分块{self.chunk_size_mb}MB", 'info')
        except Exception as e:
            self.config_manager = None
            self.max_file_size_mb = 6
            self.chunk_size_mb = 3
            self.max_file_size_bytes = 6 * 1024 * 1024
            self.chunk_size_bytes = 3 * 1024 * 1024 
            self.poll_interval = 10
            print(f"警告: 配置加载失败，使用默认值: {e}")
    
    def _setup_ui_framework(self):
        """设置 UI 框架和样式"""
        try:
            if CTK_AVAILABLE:
                ctk.set_appearance_mode("light")
                ctk.set_default_color_theme("blue")
                self._log_message("CustomTkinter 现代化UI模式已启用", 'success')
            else:
                style = ttk.Style(self.root)
                style.configure("TFrame", background=self.colors['surface'])
                style.configure("TLabel", background=self.colors['surface'], font=('Segoe UI', 10))
                style.configure("TButton", font=('Segoe UI', 10))
                self._log_message("Tkinter 传统样式模式已启用", 'info')
        except Exception as e:
            print(f"警告: UI框架设置失败: {e}")
    
    def _init_security(self):
        """初始化安全系统"""
        try:
            self.password = keyring.get_password("cloud_clipboard_service", "secret_key")
            if not self.password:
                messagebox.showerror("密钥错误", "未在系统凭据管理器中找到密钥！\n请先运行 config_setup.py 进行配置。")
                sys.exit()
            self._log_message("安全密钥加载成功", 'success')
        except Exception as e:
            messagebox.showerror("Keyring错误", f"无法从系统凭据管理器获取密钥: {e}")
            sys.exit()
    
    def _init_components(self):
        """初始化组件系统"""
        self.status_queue = queue.Queue()
        self.file_completion_queue = queue.Queue()
        
        # 监听控制变量
        self.text_monitoring_enabled = tk.BooleanVar(value=False)
        self.file_monitoring_enabled = tk.BooleanVar(value=False)
        self.monitoring_active = threading.Event()
        self.monitor_thread = None
        
        # 文件清理线程
        self.cleanup_thread = None
        self.cleanup_active = threading.Event()
        
        # 启动队列处理和文件清理服务
        self._start_queue_processing()
        self._start_cleanup_service()
        
        self._log_message("组件系统初始化完成", 'info')
    
    def _create_optimized_ui(self):
        """创建优化UI界面 - 上下布局，底部1/4为活动日志"""
        # 主容器
        if CTK_AVAILABLE:
            main_container = ctk.CTkFrame(self.root, fg_color=self.colors['surface'])
            main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        else:
            main_container = ttk.Frame(self.root, padding="10")
            main_container.pack(fill=tk.BOTH, expand=True)
        
        # 使用 PanedWindow 实现上下分割 (75% : 25%)
        if CTK_AVAILABLE:
            # CustomTkinter 使用 pack 布局模拟分割
            self.main_function_area = ctk.CTkFrame(main_container)
            self.main_function_area.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
            
            self.log_area_frame = ctk.CTkFrame(main_container)
            self.log_area_frame.pack(fill=tk.BOTH, pady=(5, 0))
            
            # 设置固定高度比例
            main_container.update_idletasks()
            container_height = main_container.winfo_reqheight()
            log_height = max(120, int(container_height * 0.25))
            self.log_area_frame.configure(height=log_height)
        else:
            # 传统 Tkinter 使用 PanedWindow
            paned_window = ttk.PanedWindow(main_container, orient=tk.VERTICAL)
            paned_window.pack(fill=tk.BOTH, expand=True)
            
            self.main_function_area = ttk.Frame(paned_window)
            paned_window.add(self.main_function_area, weight=3)
            
            self.log_area_frame = ttk.LabelFrame(paned_window, text="📝 活动日志")
            paned_window.add(self.log_area_frame, weight=1)
        
        # 创建主功能区域内容
        self._create_main_function_area()
        
        # 创建活动日志区域
        self._create_activity_log_area()
        
        self._log_message("优化UI界面创建完成", 'success')
    
    def _create_main_function_area(self):
        """创建主功能区域 - 简化设计，移除一键上传"""
        if CTK_AVAILABLE:
            # 标题区域
            title_frame = ctk.CTkFrame(self.main_function_area, fg_color="transparent")
            title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
            
            title_label = ctk.CTkLabel(
                title_frame,
                text="📁 文件上传管理",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            title_label.pack(side=tk.LEFT)
            
            # 状态指示器
            self.status_indicator = ctk.CTkLabel(
                title_frame,
                text="● 就绪",
                font=ctk.CTkFont(size=14),
                text_color=self.colors['success']
            )
            self.status_indicator.pack(side=tk.RIGHT)
            
            # 文件管理区域
            file_frame = ctk.CTkFrame(self.main_function_area)
            file_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
            
        else:
            # 传统 Tkinter 设计
            title_frame = ttk.Frame(self.main_function_area)
            title_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
            
            title_label = ttk.Label(
                title_frame,
                text="📁 文件上传管理",
                font=('Segoe UI', 14, 'bold')
            )
            title_label.pack(side=tk.LEFT)
            
            self.status_indicator = ttk.Label(
                title_frame,
                text="● 就绪",
                foreground=self.colors['success'],
                font=('Segoe UI', 12)
            )
            self.status_indicator.pack(side=tk.RIGHT)
            
            file_frame = ttk.LabelFrame(self.main_function_area, text="文件列表")
            file_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        
        # 创建文件树
        self._create_file_tree(file_frame)
        
        # 创建操作按钮（简化版）
        self._create_action_buttons(file_frame)
        
        # 创建监听控制区域
        self._create_monitoring_controls()
    
    def _create_file_tree(self, container):
        """创建文件树组件"""
        if CTK_AVAILABLE:
            tree_container = tk.Frame(container)
            tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        else:
            tree_container = ttk.Frame(container)
            tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建列标签
        cols = ('File Name', 'Size', 'Status')
        self.file_tree = ttk.Treeview(tree_container, columns=cols, show='headings', selectmode='extended')
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 设置列尺寸和标题
        self.file_tree.heading('File Name', text='📄 文件名')
        self.file_tree.heading('Size', text='📊 大小')
        self.file_tree.heading('Status', text='🔄 状态')
        
        self.file_tree.column('File Name', width=280, anchor='w')
        self.file_tree.column('Size', width=100, anchor='e')
        self.file_tree.column('Status', width=120, anchor='center')
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.file_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
    
    def _create_action_buttons(self, parent):
        """创建操作按钮 - 简化设计，移除一键上传"""
        if CTK_AVAILABLE:
            button_frame = ctk.CTkFrame(parent, fg_color="transparent")
            button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
            
            # 选择文件按钮
            select_button = ctk.CTkButton(
                button_frame,
                text="📁 选择文件",
                command=self._select_files,
                width=140,
                height=35
            )
            select_button.pack(side=tk.LEFT, padx=(0, 10))
            
            # 上传已选按钮
            upload_button = ctk.CTkButton(
                button_frame,
                text="🚀 上传已选",
                command=self._upload_selected_files,
                width=140,
                height=35,
                fg_color=self.colors['success']
            )
            upload_button.pack(side=tk.LEFT, padx=(0, 10))
            
            # 清理列表按钮
            clear_button = ctk.CTkButton(
                button_frame,
                text="🗑️ 清理列表",
                command=self._clear_file_list,
                width=120,
                height=35,
                fg_color=self.colors['warning']
            )
            clear_button.pack(side=tk.RIGHT)
            
        else:
            button_frame = ttk.Frame(parent)
            button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            ttk.Button(
                button_frame,
                text="📁 选择文件",
                command=self._select_files
            ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
            
            ttk.Button(
                button_frame,
                text="🚀 上传已选",
                command=self._upload_selected_files
            ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 5))
            
            ttk.Button(
                button_frame,
                text="🗑️ 清理列表",
                command=self._clear_file_list
            ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
    
    def _create_monitoring_controls(self):
        """创建监听控制区域"""
        if CTK_AVAILABLE:
            monitor_frame = ctk.CTkFrame(self.main_function_area)
            monitor_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
            
            monitor_title = ctk.CTkLabel(
                monitor_frame,
                text="🔍 智能监听",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            monitor_title.pack(anchor="w", padx=20, pady=(15, 5))
            
            controls_frame = ctk.CTkFrame(monitor_frame, fg_color="transparent")
            controls_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
            
            # 文本监听复选框
            self.text_monitor_checkbox = ctk.CTkCheckBox(
                controls_frame,
                text="监听剪切板 (文本)",
                variable=self.text_monitoring_enabled,
                command=self._update_monitoring_state
            )
            self.text_monitor_checkbox.pack(side=tk.LEFT, padx=(0, 20))
            
            # 文件监听复选框
            if WIN32_AVAILABLE:
                self.file_monitor_checkbox = ctk.CTkCheckBox(
                    controls_frame,
                    text="监听剪切板 (文件)",
                    variable=self.file_monitoring_enabled,
                    command=self._update_monitoring_state
                )
                self.file_monitor_checkbox.pack(side=tk.LEFT)
            
            # 监听状态指示
            self.monitor_status_label = ctk.CTkLabel(
                controls_frame,
                text="监听已停止",
                text_color=self.colors['text_secondary']
            )
            self.monitor_status_label.pack(side=tk.RIGHT)
            
            # 防护状态显示
            self.protection_status_label = ctk.CTkLabel(
                controls_frame,
                text="防护: 就绪",
                text_color=self.colors['success'],
                font=ctk.CTkFont(size=10)
            )
            self.protection_status_label.pack(side=tk.RIGHT, padx=(10, 0))
            
        else:
            monitor_frame = ttk.LabelFrame(self.main_function_area, text="🔍 智能监听")
            monitor_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            controls_frame = ttk.Frame(monitor_frame)
            controls_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Checkbutton(
                controls_frame,
                text="监听剪切板 (文本)",
                variable=self.text_monitoring_enabled,
                command=self._update_monitoring_state
            ).pack(anchor='w', pady=2)
            
            if WIN32_AVAILABLE:
                ttk.Checkbutton(
                    controls_frame,
                    text="监听剪切板 (文件)",
                    variable=self.file_monitoring_enabled,
                    command=self._update_monitoring_state
                ).pack(anchor='w', pady=2)
            
            self.monitor_status_label = ttk.Label(
                controls_frame,
                text="监听已停止",
                foreground=self.colors['text_secondary']
            )
            self.monitor_status_label.pack(anchor='w', pady=(5, 0))
    
    def _create_activity_log_area(self):
        """创建活动日志区域 - 约10行左右"""
        if CTK_AVAILABLE:
            log_title = ctk.CTkLabel(
                self.log_area_frame,
                text="📝 活动日志",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            log_title.pack(anchor="w", padx=20, pady=(15, 5))
            
            log_container = ctk.CTkFrame(self.log_area_frame)
            log_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
            
            self.log_area = scrolledtext.ScrolledText(
                log_container,
                font=('Consolas', 10),
                state='disabled',
                height=8,
                relief='flat',
                bg=self.colors['surface'],
                fg=self.colors['text'],
                wrap=tk.WORD
            )
            self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
        else:
            self.log_area = scrolledtext.ScrolledText(
                self.log_area_frame,
                font=('Consolas', 10),
                state='disabled',
                height=8,
                relief='sunken',
                bg=self.colors['surface'],
                fg=self.colors['text'],
                wrap=tk.WORD
            )
            self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self._log_message("日志系统初始化完成", 'success')
    
    def _start_services(self):
        """启动系统服务"""
        if self.config_manager:
            self.cookie_server_thread = threading.Thread(
                target=run_cookie_server, args=(self.config_manager,), daemon=True)
            self.cookie_server_thread.start()
            self._log_message("Cookie同步服务已启动", 'info')
    
    def _start_queue_processing(self):
        """启动队列处理服务"""
        self._process_status_queue()
        self._process_completion_queue()
    
    def _start_cleanup_service(self):
        """启动文件清理服务"""
        self.cleanup_active.set()
        self.cleanup_thread = threading.Thread(
            target=self._file_cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        
        # 启动防护状态更新
        self._start_protection_status_update()
    
    def _start_protection_status_update(self):
        """启动防护状态更新服务"""
        def update_protection_status():
            while self.root.winfo_exists():
                try:
                    status = self._get_clipboard_protection_status()
                    if hasattr(self, 'protection_status_label'):
                        self.protection_status_label.configure(text=f"防护: {status.split('防护状态: ')[1] if '防护状态: ' in status else '就绪'}")
                except Exception:
                    pass
                time.sleep(5)  # 每5秒更新一次
        
        protection_thread = threading.Thread(target=update_protection_status, daemon=True)
        protection_thread.start()
    
    def _log_system_info(self):
        """记录系统启动信息"""
        startup_time = time.time() - self.performance_stats['startup_time']
        ui_mode = "CustomTkinter 现代模式" if CTK_AVAILABLE else "Tkinter 经典模式"
        
        self._log_message(f"=== 系统启动完成 (耗时: {startup_time:.2f}秒) ===", 'success')
        self._log_message(f"UI框架: {ui_mode}", 'info')
        self._log_message(f"文件限制: {self.max_file_size_mb}MB | 分块大小: {self.chunk_size_mb}MB", 'info')
        
        if WIN32_AVAILABLE:
            self._log_message("文件剪切板支持: 可用", 'success')
        else:
            self._log_message("文件剪切板支持: 不可用 (Win32缺失)", 'warning')
    
    def _log_message(self, message: str, msg_type: str = 'info'):
        """安全的日志记录方法，支持实时状态跟踪"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            icons = {
                'info': "ℹ️",
                'success': "✅", 
                'error': "❌",
                'warning': "⚠️",
                'upload': "🚀",
                'complete': "🎉",
                'monitor': "👁️",
                'cleanup': "🧹"
            }
            
            icon = icons.get(msg_type, 'ℹ️')
            log_line = f"[{timestamp}] {icon} {message}\n"
            
            # 更新日志区域
            if hasattr(self, 'log_area') and self.log_area:
                try:
                    self.log_area.config(state='normal')
                    self.log_area.insert(tk.END, log_line)
                    
                    # 保持日志行数限制（最多200行）
                    lines = self.log_area.get(1.0, tk.END).split('\n')
                    if len(lines) > 200:
                        self.log_area.delete(1.0, f"{len(lines)-150}.0")
                    
                    self.log_area.config(state='disabled')
                    self.log_area.see(tk.END)
                except Exception:
                    pass
            else:
                print(log_line.strip())
            
            # 更新性能统计
            if msg_type == 'success' and '上传成功' in message:
                self.performance_stats['successful_uploads'] += 1
            elif msg_type == 'monitor':
                self.performance_stats['clipboard_checks'] += 1
                
        except Exception as e:
            try:
                print(f"LOG_ERROR: {message} | Error: {e}")
            except:
                pass
    
    def _process_status_queue(self):
        """处理状态消息队列"""
        try:
            while True:
                try:
                    msg_type, message = self.status_queue.get_nowait()
                    self._log_message(message, msg_type)
                except queue.Empty:
                    break
        except Exception as e:
            print(f"队列处理错误: {e}")
        
        self.root.after(100, self._process_status_queue)
    
    def _process_completion_queue(self):
        """处理文件完成消息队列，用于自动清理"""
        try:
            while True:
                try:
                    file_id, completion_time = self.file_completion_queue.get_nowait()
                    if self.file_cleanup_config['cleanup_enabled']:
                        cleanup_time = completion_time + self.file_cleanup_config['completion_delay']
                        self.file_cleanup_config['pending_cleanups'][file_id] = cleanup_time
                        self._log_message(f"已安排文件清理: {file_id} (4秒后)", 'cleanup')
                except queue.Empty:
                    break
        except Exception as e:
            print(f"完成队列处理错误: {e}")
        
        self.root.after(200, self._process_completion_queue)
    
    def _file_cleanup_worker(self):
        """文件清理工作线程"""
        while self.cleanup_active.is_set():
            try:
                current_time = time.time()
                to_cleanup = []
                
                for file_id, cleanup_time in self.file_cleanup_config['pending_cleanups'].items():
                    if current_time >= cleanup_time:
                        to_cleanup.append(file_id)
                
                for file_id in to_cleanup:
                    try:
                        if hasattr(self.file_tree, 'delete'):
                            self.file_tree.delete(file_id)
                        del self.file_cleanup_config['pending_cleanups'][file_id]
                        self._log_message(f"已清理完成文件: {os.path.basename(file_id) if os.path.exists(file_id) else file_id}", 'cleanup')
                    except Exception as cleanup_error:
                        print(f"文件清理错误: {cleanup_error}")
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                print(f"清理工作线程错误: {e}")
                time.sleep(5)  # 出错时等待更长时间
    
    def _update_monitoring_state(self):
        """更新监听状态 - 智能间隔调整机制"""
        try:
            is_any_monitoring_on = (
                self.text_monitoring_enabled.get() or 
                self.file_monitoring_enabled.get()
            )
            
            if is_any_monitoring_on and not (self.monitor_thread and self.monitor_thread.is_alive()):
                # 启动监听
                self.monitoring_active.set()
                
                # 重置监听配置
                self.clipboard_monitor_config['current_interval'] = self.clipboard_monitor_config['base_interval']
                self.clipboard_monitor_config['consecutive_idle_count'] = 0
                
                self.monitor_thread = threading.Thread(
                    target=self._intelligent_clipboard_monitor, daemon=True)
                self.monitor_thread.start()
                
                self._log_message("智能剪切板监听已启动，初始间隔: 0.5秒", 'monitor')
                self._update_monitor_status("监听运行中", 'success')
                
            elif not is_any_monitoring_on:
                # 停止监听
                self.monitoring_active.clear()
                self._log_message("剪切板监听已停止", 'warning')
                self._update_monitor_status("监听已停止", 'text_secondary')
                
        except Exception as e:
            self._log_message(f"更新监听状态失败: {e}", 'error')
    
    def _intelligent_clipboard_monitor(self):
        """智能剪切板监听 - 混合策略（操作+变化双重检测）"""
        recent_text = ""
        recent_file_paths = []
        
        self._log_message("智能监听线程已启动", 'monitor')
        
        while self.monitoring_active.is_set():
            try:
                activity_detected = False
                
                # 文本监听检测
                if self.text_monitoring_enabled.get():
                    try:
                        current_text = pyperclip.paste().strip()
                        if current_text and current_text != recent_text:
                            # 检查剪切板变化是否安全
                            if self._is_clipboard_change_safe(current_text, 'text'):
                                recent_text = current_text
                                activity_detected = True
                                self.performance_stats['last_activity_time'] = time.time()
                                self._process_text_upload(current_text)
                            else:
                                # 记录被防护的内容
                                self._log_message(f"⚠️ 检测到重复文本内容，已跳过处理 (长度: {len(current_text)})", 'warning')
                    except Exception:
                        pass
                
                # 文件监听检测
                if self.file_monitoring_enabled.get() and WIN32_AVAILABLE:
                    try:
                        current_file_paths = self._get_current_file_paths()
                        if current_file_paths != recent_file_paths:
                            # 检查文件路径变化是否安全
                            safe_file_paths = []
                            for file_path in current_file_paths:
                                if self._is_clipboard_change_safe(file_path, 'file'):
                                    safe_file_paths.append(file_path)
                                else:
                                    self._log_message(f"⚠️ 检测到重复文件路径，已跳过处理: {os.path.basename(file_path)}", 'warning')
                            
                            if safe_file_paths:
                                recent_file_paths = safe_file_paths
                                activity_detected = True
                                self.performance_stats['last_activity_time'] = time.time()
                                for file_path in safe_file_paths:
                                    threading.Thread(
                                        target=self._create_upload_task,
                                        args=(file_path,),
                                        daemon=True
                                    ).start()
                            else:
                                recent_file_paths = current_file_paths  # 更新但不处理
                    except Exception:
                        pass
                
                # 调整监听间隔
                self._adjust_monitoring_interval(activity_detected)
                
                # 按当前间隔休眠
                time.sleep(self.clipboard_monitor_config['current_interval'])
                
            except Exception as e:
                self._log_message(f"监听过程出错: {e}", 'error')
                time.sleep(1)
        
        self._log_message("智能监听线程已停止", 'monitor')
    
    def _adjust_monitoring_interval(self, activity_detected: bool):
        """智能间隔调整算法 - 混合策略（操作+变化双重检测）"""
        config = self.clipboard_monitor_config
        
        if activity_detected:
            # 检测到活动，降低间隔
            config['current_interval'] = max(
                config['base_interval'],
                config['current_interval'] * config['activity_reset_factor']
            )
            config['consecutive_idle_count'] = 0
            
            interval_ms = int(config['current_interval'] * 1000)
            self._update_monitor_status(f"活动监听 ({interval_ms}ms)", 'success')
            
        else:
            # 未检测到活动，逐渐增加间隔
            config['consecutive_idle_count'] += 1
            
            if config['consecutive_idle_count'] % 3 == 0:  # 每3次空闲调整一次
                config['current_interval'] = min(
                    config['max_interval'],
                    config['current_interval'] * config['increase_factor']
                )
                
                interval_ms = int(config['current_interval'] * 1000)
                self._update_monitor_status(f"空闲监听 ({interval_ms}ms)", 'text_secondary')
    
    def _update_monitor_status(self, text: str, color_key: str):
        """更新监听状态显示"""
        try:
            if hasattr(self, 'monitor_status_label'):
                self.monitor_status_label.configure(text=text)
                if CTK_AVAILABLE:
                    self.monitor_status_label.configure(text_color=self.colors[color_key])
                else:
                    self.monitor_status_label.configure(foreground=self.colors[color_key])
        except Exception:
            pass
    
    def _get_current_file_paths(self) -> list:
        """获取当前文件剪切板路径列表"""
        try:
            if not WIN32_AVAILABLE:
                return []
                
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                    paths = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                    return list(paths) if paths else []
                return []
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            return []
    
    def _select_files(self):
        """选择文件"""
        try:
            filepaths = filedialog.askopenfilenames()
            if filepaths:
                for path in filepaths:
                    self._add_file_to_list(path)
                self._log_message(f"已选择 {len(filepaths)} 个文件", 'info')
        except Exception as e:
            self._log_message(f"文件选择失败: {e}", 'error')
    
    def _add_file_to_list(self, path):
        """添加文件到列表"""
        try:
            if os.path.exists(path):
                size_str = self._get_file_size(path)
                filename = os.path.basename(path)
                
                # 检查是否已存在
                for item in self.file_tree.get_children():
                    if self.file_tree.item(item)['values'][0] == filename:
                        return  # 已存在，跳过
                
                self.file_tree.insert('', tk.END, iid=path, values=(filename, size_str, '待上传'))
                
        except Exception as e:
            self._log_message(f"添加文件失败: {e}", 'error')
    
    def _upload_selected_files(self):
        """上传选中的文件"""
        try:
            selected_items = self.file_tree.selection()
            if not selected_items:
                messagebox.showwarning("提示", "没有选择任何文件")
                return
            
            self._log_message(f"开始上传 {len(selected_items)} 个文件", 'upload')
            
            for item_id in selected_items:
                threading.Thread(
                    target=self._create_upload_task,
                    args=(item_id, item_id),
                    daemon=True
                ).start()
                
        except Exception as e:
            self._log_message(f"上传失败: {e}", 'error')
    
    def _clear_file_list(self):
        """清理文件列表"""
        try:
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)
            self._log_message("文件列表已清理", 'info')
        except Exception as e:
            self._log_message(f"清理失败: {e}", 'error')
    
    def _get_file_size(self, file_path):
        """获取文件大小字符串"""
        try:
            size = os.path.getsize(file_path)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 ** 2:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / 1024 ** 2:.1f} MB"
        except:
            return "N/A"
    
    def _process_text_upload(self, text_content):
        """处理文本上传"""
        try:
            content_hash = hashlib.sha256(text_content.encode('utf-8')).hexdigest()
            if content_hash in UPLOAD_CACHE:
                self._log_message("文本内容未变，跳过", 'info')
                return
            
            self._log_message(f"处理文本内容 (长度: {len(text_content)})", 'upload')
            
            # 标记为自身操作，避免循环
            self._mark_self_operation()
            
            data_bytes = text_content.encode('utf-8')
            encrypted_payload = self._create_and_encrypt_payload(
                data_bytes, self.password, "clipboard_text.txt", is_from_text=True)
            
            config = self.config_manager.get_config() if self.config_manager else None
            if config and upload_data(encrypted_payload, config, self.status_queue):
                UPLOAD_CACHE.append(content_hash)
                self._log_message("文本上传成功", 'success')
            
        except Exception as e:
            self._log_message(f"文本处理失败: {e}", 'error')
    
    def _create_upload_task(self, file_path, item_id=None):
        """创建上传任务"""
        try:
            if not os.path.exists(file_path):
                self._log_message(f"文件不存在: {file_path}", 'error')
                return
            
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size_bytes:
                self._log_message(f"文件过大: {os.path.basename(file_path)}", 'error')
                return
            
            # 标记为自身操作，避免循环
            self._mark_self_operation()
            
            # 更新状态
            if item_id:
                self._update_file_status(item_id, '上传中')
            
            # 执行上传
            if file_size > self.chunk_size_bytes:
                success = self._process_chunk_upload(file_path, item_id)
            else:
                success = self._process_single_upload(file_path, item_id)
            
            if success:
                if item_id:
                    self._update_file_status(item_id, '完成')
                    # 安排延迟清理
                    self.file_completion_queue.put((item_id, time.time()))
                
                self.performance_stats['successful_uploads'] += 1
                self._log_message(f"文件上传成功: {os.path.basename(file_path)}", 'success')
            else:
                if item_id:
                    self._update_file_status(item_id, '失败')
                self._log_message(f"文件上传失败: {os.path.basename(file_path)}", 'error')
                
        except Exception as e:
            self._log_message(f"上传任务失败: {e}", 'error')
    
    def _update_file_status(self, item_id, status):
        """更新文件状态"""
        try:
            if hasattr(self.file_tree, 'item'):
                current_values = list(self.file_tree.item(item_id)['values'])
                current_values[2] = status
                self.file_tree.item(item_id, values=current_values)
        except Exception:
            pass
    
    def _process_single_upload(self, file_path, item_id=None):
        """处理单文件上传"""
        try:
            with open(file_path, 'rb') as f:
                data_bytes = f.read()
            
            encrypted_payload = self._create_and_encrypt_payload(
                data_bytes, self.password, os.path.basename(file_path))
            
            config = self.config_manager.get_config() if self.config_manager else None
            if config:
                return upload_data(encrypted_payload, config, self.status_queue)
            
        except Exception as e:
            self._log_message(f"单文件上传失败: {e}", 'error')
        return False
    
    def _process_chunk_upload(self, file_path, item_id=None):
        """处理分片上传"""
        try:
            file_size = os.path.getsize(file_path)
            total_chunks = math.ceil(file_size / self.chunk_size_bytes)
            upload_id = f"{int(time.time())}-{base64.urlsafe_b64encode(os.urandom(4)).decode()}"
            
            config = self.config_manager.get_config() if self.config_manager else None
            if not config:
                return False
            
            success = True
            
            with open(file_path, 'rb') as f:
                for i in range(total_chunks):
                    chunk_data = f.read(self.chunk_size_bytes)
                    if not chunk_data:
                        break
                    
                    chunk_index = i + 1
                    if item_id:
                        self._update_file_status(item_id, f'分片 {chunk_index}/{total_chunks}')
                    
                    encrypted_payload = self._create_and_encrypt_payload(
                        chunk_data, self.password, os.path.basename(file_path))
                    
                    chunk_filename = f"chunk_{upload_id}_{chunk_index:03d}_{total_chunks:03d}_{urllib.parse.quote(os.path.basename(file_path))}.encrypted"
                    
                    if not upload_data(encrypted_payload, config, self.status_queue, custom_filename=chunk_filename):
                        success = False
                        break
            
            return success
            
        except Exception as e:
            self._log_message(f"分片上传失败: {e}", 'error')
        return False
    
    def _create_and_encrypt_payload(self, data_bytes, password, original_filename, is_from_text=False):
        """创建和加密载荷"""
        key = get_encryption_key(password)
        fernet = Fernet(key)
        payload = {
            "filename": original_filename,
            "content_base64": base64.b64encode(data_bytes).decode('utf-8'),
            "is_from_text": is_from_text
        }
        return fernet.encrypt(json.dumps(payload).encode('utf-8'))
    
    def _on_closing(self):
        """窗口关闭处理"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？"):
            try:
                self.monitoring_active.clear()
                self.cleanup_active.clear()
                if self.executor:
                    self.executor.shutdown(wait=False)
                self._log_message("程序正在关闭...", 'info')
            except:
                pass
            finally:
                self.root.destroy()

    def _is_clipboard_change_safe(self, new_content: str, content_type: str = 'text') -> bool:
        """检查剪切板变化是否安全，防止循环"""
        current_time = time.time()
        
        with self.clipboard_protection['operation_lock']:
            # 检查是否是自己操作
            if self.clipboard_protection['is_self_operation']:
                self.clipboard_protection['is_self_operation'] = False
                return False
            
            # 检查内容是否在黑名单中
            content_hash = hashlib.sha256(new_content.encode('utf-8')).hexdigest()
            if content_hash in self.clipboard_protection['content_blacklist']:
                return False
            
            # 检查内容是否相同
            if content_type == 'text':
                if new_content == self.clipboard_protection['last_text_content']:
                    return False
            elif content_type == 'file':
                if new_content in self.clipboard_protection['last_file_paths']:
                    return False
            
            # 检查时间间隔
            time_diff = current_time - self.clipboard_protection['last_change_time']
            if time_diff < self.clipboard_protection['min_interval_seconds']:
                return False
            
            # 检查频率限制
            self.clipboard_protection['change_timestamps'].append(current_time)
            
            # 清理超过1分钟的时间戳
            cutoff_time = current_time - 60
            while (self.clipboard_protection['change_timestamps'] and 
                   self.clipboard_protection['change_timestamps'][0] < cutoff_time):
                self.clipboard_protection['change_timestamps'].popleft()
            
            # 检查每分钟变化次数
            if len(self.clipboard_protection['change_timestamps']) > self.clipboard_protection['max_changes_per_minute']:
                self._log_message('⚠️ 剪切板变化过于频繁，已启用防护模式', 'warning')
                return False
            
            # 更新状态
            if content_type == 'text':
                self.clipboard_protection['last_text_content'] = new_content
                self.clipboard_protection['last_text_hash'] = content_hash
            elif content_type == 'file':
                if new_content not in self.clipboard_protection['last_file_paths']:
                    self.clipboard_protection['last_file_paths'].append(new_content)
                    # 保持列表大小
                    if len(self.clipboard_protection['last_file_paths']) > 10:
                        self.clipboard_protection['last_file_paths'].pop(0)
            
            self.clipboard_protection['last_change_time'] = current_time
            
            # 添加到黑名单
            self.clipboard_protection['content_blacklist'].add(content_hash)
            if len(self.clipboard_protection['content_blacklist']) > self.clipboard_protection['blacklist_max_size']:
                # 清理旧的黑名单项
                old_items = list(self.clipboard_protection['content_blacklist'])[:10]
                for item in old_items:
                    self.clipboard_protection['content_blacklist'].discard(item)
            
            return True
    
    def _mark_self_operation(self):
        """标记为自身操作，避免循环"""
        with self.clipboard_protection['operation_lock']:
            self.clipboard_protection['is_self_operation'] = True
    
    def _get_clipboard_protection_status(self) -> str:
        """获取剪切板防护状态信息"""
        with self.clipboard_protection['operation_lock']:
            changes_last_minute = len(self.clipboard_protection['change_timestamps'])
            last_change_ago = time.time() - self.clipboard_protection['last_change_time']
            blacklist_size = len(self.clipboard_protection['content_blacklist'])
            
            return (f"防护状态: 变化{changes_last_minute}/分钟, "
                   f"上次变化{last_change_ago:.1f}秒前, "
                   f"黑名单{blacklist_size}项")


if __name__ == '__main__':
    # 配置文件检查
    if not os.path.exists('config.ini'):
        messagebox.showerror("错误", "未找到 config.ini 文件！\n请先运行 config_setup.py 进行配置。")
        sys.exit()

    # 创建主窗口
    root = tk.Tk()
    
    try:
        app = OptimizedClipboardUploader(root)
        root.mainloop()
    except Exception as e:
        print(f"应用程序运行失败: {e}")
        messagebox.showerror("运行错误", f"应用程序运行失败：\n{e}")