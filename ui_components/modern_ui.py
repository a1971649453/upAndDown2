# modern_ui.py - 现代化UI组件库
# 基于云外端v5.9的成功实践，提供可复用的现代化组件

"""
现代化UI组件库
=============

使用方法：
from ui_components.modern_ui import ModernCard, ModernButton, ModernProgressBar

# 创建卡片
card = ModernCard(parent, title="上传文件")
card.pack(fill='x', padx=16, pady=8)

# 创建按钮
button = ModernButton(card, text="开始上传", variant="primary")
button.pack(pady=8)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import threading
from typing import Optional, Callable, Dict, Any

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

from .styles import modern_styles, component_styles


class ModernCard:
    """现代化卡片组件 - LocalSend风格"""
    
    def __init__(self, parent, title: str = "", padding: int = 16):
        self.parent = parent
        self.title = title
        self.padding = padding
        
        # 获取样式配置
        self.colors = modern_styles.get_colors()
        self.fonts = modern_styles.get_fonts()
        self.spacing = modern_styles.get_spacing()
        
        self.create_card()
    
    def create_card(self):
        """创建卡片容器"""
        if CTK_AVAILABLE:
            # CustomTkinter版本
            card_config = component_styles.get_card_config()
            self.frame = ctk.CTkFrame(self.parent, **card_config)
            
            if self.title:
                self.title_label = ctk.CTkLabel(
                    self.frame,
                    text=self.title,
                    font=self.fonts['heading_small'],
                    text_color=self.colors['text']
                )
                self.title_label.pack(pady=(self.padding, self.spacing['sm']), padx=self.padding, anchor='w')
            
            # 内容容器
            self.content_frame = ctk.CTkFrame(
                self.frame,
                fg_color='transparent'
            )
            self.content_frame.pack(fill='both', expand=True, padx=self.padding, pady=(0, self.padding))
            
        else:
            # 传统Tkinter版本
            card_config = component_styles.get_card_config()
            self.frame = tk.Frame(self.parent, **card_config)
            
            if self.title:
                self.title_label = tk.Label(
                    self.frame,
                    text=self.title,
                    font=self.fonts['heading_small'],
                    fg=self.colors['text'],
                    bg=self.colors['card']
                )
                self.title_label.pack(pady=(self.padding, self.spacing['sm']), padx=self.padding, anchor='w')
            
            # 内容容器
            self.content_frame = tk.Frame(
                self.frame,
                bg=self.colors['card']
            )
            self.content_frame.pack(fill='both', expand=True, padx=self.padding, pady=(0, self.padding))
    
    def pack(self, **kwargs):
        """包装pack方法"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """包装grid方法"""
        self.frame.grid(**kwargs)
    
    def get_content_frame(self):
        """获取内容容器"""
        return self.content_frame


class ModernButton:
    """现代化按钮组件"""
    
    def __init__(self, parent, text: str = "", variant: str = "primary", 
                 command: Optional[Callable] = None, width: int = 120, height: int = 32):
        self.parent = parent
        self.text = text
        self.variant = variant
        self.command = command
        self.width = width
        self.height = height
        
        self.create_button()
    
    def create_button(self):
        """创建按钮"""
        button_config = component_styles.get_button_config(self.variant)
        
        if CTK_AVAILABLE:
            self.button = ctk.CTkButton(
                self.parent,
                text=self.text,
                command=self.command,
                width=self.width,
                height=self.height,
                **button_config
            )
        else:
            self.button = tk.Button(
                self.parent,
                text=self.text,
                command=self.command,
                width=self.width // 8,  # 字符宽度转换
                **button_config
            )
    
    def pack(self, **kwargs):
        """包装pack方法"""
        self.button.pack(**kwargs)
    
    def grid(self, **kwargs):
        """包装grid方法"""
        self.button.grid(**kwargs)
    
    def configure(self, **kwargs):
        """配置按钮属性"""
        self.button.configure(**kwargs)
    
    def config(self, **kwargs):
        """配置按钮属性(别名)"""
        self.configure(**kwargs)


class ModernLabel:
    """现代化标签组件"""
    
    def __init__(self, parent, text: str = "", variant: str = "body"):
        self.parent = parent
        self.text = text
        self.variant = variant
        
        self.create_label()
    
    def create_label(self):
        """创建标签"""
        label_config = component_styles.get_label_config(self.variant)
        
        if CTK_AVAILABLE:
            self.label = ctk.CTkLabel(
                self.parent,
                text=self.text,
                **label_config
            )
        else:
            self.label = tk.Label(
                self.parent,
                text=self.text,
                **label_config
            )
    
    def pack(self, **kwargs):
        """包装pack方法"""
        self.label.pack(**kwargs)
    
    def grid(self, **kwargs):
        """包装grid方法"""
        self.label.grid(**kwargs)
    
    def configure(self, **kwargs):
        """配置标签属性"""
        self.label.configure(**kwargs)
    
    def config(self, **kwargs):
        """配置标签属性(别名)"""
        self.configure(**kwargs)


class ModernProgressBar:
    """现代化进度条组件"""
    
    def __init__(self, parent, mode: str = "determinate"):
        self.parent = parent
        self.mode = mode
        
        self.create_progress()
    
    def create_progress(self):
        """创建进度条"""
        if CTK_AVAILABLE:
            progress_config = component_styles.get_progress_config()
            if self.mode == "indeterminate":
                self.progress = ctk.CTkProgressBar(
                    self.parent,
                    mode="indeterminate",
                    **progress_config
                )
            else:
                self.progress = ctk.CTkProgressBar(
                    self.parent,
                    **progress_config
                )
        else:
            # 传统TTK进度条
            style = ttk.Style()
            style.configure("Modern.Horizontal.TProgressbar",
                          troughcolor=modern_styles.colors['border'],
                          background=modern_styles.colors['primary'])
            
            self.progress = ttk.Progressbar(
                self.parent,
                mode=self.mode,
                style="Modern.Horizontal.TProgressbar"
            )
    
    def pack(self, **kwargs):
        """包装pack方法"""
        self.progress.pack(**kwargs)
    
    def grid(self, **kwargs):
        """包装grid方法"""
        self.progress.grid(**kwargs)
    
    def set(self, value: float):
        """设置进度值"""
        if CTK_AVAILABLE:
            self.progress.set(value)
        else:
            self.progress['value'] = value * 100
    
    def start(self, interval: int = 10):
        """开始不定进度动画"""
        if hasattr(self.progress, 'start'):
            self.progress.start(interval)
    
    def stop(self):
        """停止不定进度动画"""
        if hasattr(self.progress, 'stop'):
            self.progress.stop()


class ModernFileArea:
    """现代化文件拖拽区域"""
    
    def __init__(self, parent, on_file_select: Optional[Callable] = None, 
                 on_file_drop: Optional[Callable] = None):
        self.parent = parent
        self.on_file_select = on_file_select
        self.on_file_drop = on_file_drop
        
        self.colors = modern_styles.get_colors()
        self.fonts = modern_styles.get_fonts()
        self.spacing = modern_styles.get_spacing()
        
        self.create_file_area()
    
    def create_file_area(self):
        """创建文件选择区域"""
        if CTK_AVAILABLE:
            self.frame = ctk.CTkFrame(
                self.parent,
                fg_color=self.colors['background'],
                corner_radius=12,
                border_width=2,
                border_color=self.colors['border']
            )
            
            # 图标区域（使用文本替代图标）
            self.icon_label = ctk.CTkLabel(
                self.frame,
                text="📁",
                font=("Segoe UI", 32),
                text_color=self.colors['text_secondary']
            )
            self.icon_label.pack(pady=(32, 8))
            
            # 主要文字
            self.main_label = ctk.CTkLabel(
                self.frame,
                text="点击选择文件或拖拽到此处",
                font=self.fonts['heading_small'],
                text_color=self.colors['text']
            )
            self.main_label.pack(pady=4)
            
            # 次要文字
            self.sub_label = ctk.CTkLabel(
                self.frame,
                text="支持多种文件格式",
                font=self.fonts['body_small'],
                text_color=self.colors['text_secondary']
            )
            self.sub_label.pack(pady=(0, 32))
            
            # 选择按钮
            self.select_button = ctk.CTkButton(
                self.frame,
                text="选择文件",
                command=self.on_file_select,
                **component_styles.get_button_config('primary')
            )
            self.select_button.pack(pady=(0, 24))
            
        else:
            self.frame = tk.Frame(
                self.parent,
                bg=self.colors['background'],
                relief='groove',
                bd=2
            )
            
            # 图标
            self.icon_label = tk.Label(
                self.frame,
                text="📁",
                font=("Segoe UI", 32),
                fg=self.colors['text_secondary'],
                bg=self.colors['background']
            )
            self.icon_label.pack(pady=(32, 8))
            
            # 主要文字
            self.main_label = tk.Label(
                self.frame,
                text="点击选择文件或拖拽到此处",
                font=self.fonts['heading_small'],
                fg=self.colors['text'],
                bg=self.colors['background']
            )
            self.main_label.pack(pady=4)
            
            # 次要文字
            self.sub_label = tk.Label(
                self.frame,
                text="支持多种文件格式",
                font=self.fonts['body_small'],
                fg=self.colors['text_secondary'],
                bg=self.colors['background']
            )
            self.sub_label.pack(pady=(0, 16))
            
            # 选择按钮
            button_config = component_styles.get_button_config('primary')
            self.select_button = tk.Button(
                self.frame,
                text="选择文件",
                command=self.on_file_select,
                **button_config
            )
            self.select_button.pack(pady=(0, 24))
        
        # 绑定拖拽事件（如果支持）
        self._setup_drag_drop()
    
    def _setup_drag_drop(self):
        """设置拖拽支持"""
        # 这里可以添加拖拽支持的实现
        # 由于tkinter的拖拽支持较复杂，暂时留空
        pass
    
    def pack(self, **kwargs):
        """包装pack方法"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """包装grid方法"""
        self.frame.grid(**kwargs)


class ModernLogArea:
    """现代化日志显示区域"""
    
    def __init__(self, parent, height: int = 200):
        self.parent = parent
        self.height = height
        
        self.colors = modern_styles.get_colors()
        self.fonts = modern_styles.get_fonts()
        
        self.create_log_area()
    
    def create_log_area(self):
        """创建日志区域"""
        if CTK_AVAILABLE:
            self.frame = ctk.CTkFrame(self.parent)
            
            # 创建文本框
            self.text_widget = ctk.CTkTextbox(
                self.frame,
                height=self.height,
                font=self.fonts['monospace']
            )
            self.text_widget.pack(fill='both', expand=True, padx=8, pady=8)
            
        else:
            self.frame = tk.Frame(self.parent)
            
            # 创建滚动文本框
            self.text_widget = scrolledtext.ScrolledText(
                self.frame,
                height=self.height // 16,  # 行数估算
                font=self.fonts['monospace'],
                bg=self.colors['card'],
                fg=self.colors['text'],
                wrap=tk.WORD
            )
            self.text_widget.pack(fill='both', expand=True, padx=4, pady=4)
    
    def pack(self, **kwargs):
        """包装pack方法"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """包装grid方法"""
        self.frame.grid(**kwargs)
    
    def append_log(self, message: str, level: str = "info"):
        """添加日志消息"""
        timestamp = tk.datetime.now().strftime("%H:%M:%S")
        
        # 根据级别选择颜色
        level_colors = {
            'info': self.colors['text'],
            'success': self.colors['success'],
            'warning': self.colors['warning'],
            'error': self.colors['danger']
        }
        
        log_text = f"[{timestamp}] {message}\n"
        
        if CTK_AVAILABLE:
            self.text_widget.insert("end", log_text)
            self.text_widget.see("end")
        else:
            self.text_widget.insert(tk.END, log_text)
            self.text_widget.see(tk.END)
    
    def clear(self):
        """清空日志"""
        if CTK_AVAILABLE:
            self.text_widget.delete("1.0", "end")
        else:
            self.text_widget.delete(1.0, tk.END)


class ModernStatusBar:
    """现代化状态栏"""
    
    def __init__(self, parent):
        self.parent = parent
        self.colors = modern_styles.get_colors()
        self.fonts = modern_styles.get_fonts()
        
        self.create_status_bar()
    
    def create_status_bar(self):
        """创建状态栏"""
        if CTK_AVAILABLE:
            self.frame = ctk.CTkFrame(
                self.parent,
                height=32,
                corner_radius=0,
                fg_color=self.colors['background']
            )
            
            self.status_label = ctk.CTkLabel(
                self.frame,
                text="就绪",
                font=self.fonts['body_small'],
                text_color=self.colors['text_secondary']
            )
            self.status_label.pack(side='left', padx=12, pady=6)
            
            self.info_label = ctk.CTkLabel(
                self.frame,
                text="",
                font=self.fonts['body_small'],
                text_color=self.colors['text_secondary']
            )
            self.info_label.pack(side='right', padx=12, pady=6)
            
        else:
            self.frame = tk.Frame(
                self.parent,
                bg=self.colors['background'],
                height=32,
                relief='sunken',
                bd=1
            )
            
            self.status_label = tk.Label(
                self.frame,
                text="就绪",
                font=self.fonts['body_small'],
                fg=self.colors['text_secondary'],
                bg=self.colors['background']
            )
            self.status_label.pack(side='left', padx=8, pady=4)
            
            self.info_label = tk.Label(
                self.frame,
                text="",
                font=self.fonts['body_small'],
                fg=self.colors['text_secondary'],
                bg=self.colors['background']
            )
            self.info_label.pack(side='right', padx=8, pady=4)
    
    def pack(self, **kwargs):
        """包装pack方法"""
        self.frame.pack(**kwargs)
    
    def set_status(self, text: str, status_type: str = "info"):
        """设置状态文本"""
        color_map = {
            'info': self.colors['text_secondary'],
            'success': self.colors['success'],
            'warning': self.colors['warning'],
            'error': self.colors['danger']
        }
        
        color = color_map.get(status_type, self.colors['text_secondary'])
        
        if CTK_AVAILABLE:
            self.status_label.configure(text=text, text_color=color)
        else:
            self.status_label.configure(text=text, fg=color)
    
    def set_info(self, text: str):
        """设置信息文本"""
        if CTK_AVAILABLE:
            self.info_label.configure(text=text)
        else:
            self.info_label.configure(text=text)