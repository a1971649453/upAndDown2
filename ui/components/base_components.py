# ui/components/base_components.py
"""
基础UI组件库 - 统一的现代化组件
支持CustomTkinter和传统Tkinter fallback
"""

import tkinter as tk
from tkinter import ttk
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

from ..themes.theme_manager import ThemeManager

class ModernFrame:
    """现代化框架组件，支持卡片式设计"""
    
    def __init__(self, parent, theme_manager: ThemeManager, card_style=True, **kwargs):
        self.theme_manager = theme_manager
        self.card_style = card_style
        
        if theme_manager.is_customtkinter_available():
            # 使用CustomTkinter
            self.frame = ctk.CTkFrame(parent, **self._get_ctk_kwargs(kwargs))
        else:
            # Fallback到传统Tkinter
            if card_style:
                style_config = theme_manager.create_card_style()
                kwargs.update(style_config)
            self.frame = tk.Frame(parent, **kwargs)
    
    def _get_ctk_kwargs(self, kwargs):
        """转换参数为CustomTkinter格式"""
        ctk_kwargs = {}
        if 'padding' in kwargs:
            # CustomTkinter使用corner_radius而不是padding
            ctk_kwargs['corner_radius'] = 8
        
        # 映射颜色
        ctk_kwargs['fg_color'] = self.theme_manager.get_color('card_bg')
        if self.card_style:
            ctk_kwargs['border_width'] = 1
            ctk_kwargs['border_color'] = self.theme_manager.get_color('card_border')
        
        return ctk_kwargs
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)
    
    def place(self, **kwargs):
        self.frame.place(**kwargs)
    
    def get_widget(self):
        """获取底层widget用于添加子组件"""
        return self.frame

class ModernButton:
    """现代化按钮组件"""
    
    def __init__(self, parent, text, command=None, theme_manager: ThemeManager = None, 
                 style='primary', **kwargs):
        self.theme_manager = theme_manager or ThemeManager()
        self.style = style
        
        if self.theme_manager.is_customtkinter_available():
            # 使用CustomTkinter按钮
            self.button = ctk.CTkButton(
                parent, 
                text=text, 
                command=command,
                **self._get_ctk_button_kwargs(kwargs)
            )
        else:
            # Fallback到ttk按钮
            self.button = ttk.Button(parent, text=text, command=command, **kwargs)
            self._apply_traditional_style()
    
    def _get_ctk_button_kwargs(self, kwargs):
        """为CustomTkinter按钮设置样式"""
        ctk_kwargs = {}
        
        if self.style == 'primary':
            ctk_kwargs['fg_color'] = self.theme_manager.get_color('primary')
            ctk_kwargs['hover_color'] = self.theme_manager.get_color('primary_hover')
            ctk_kwargs['text_color'] = 'white'
        elif self.style == 'secondary':
            ctk_kwargs['fg_color'] = self.theme_manager.get_color('secondary')
            ctk_kwargs['text_color'] = self.theme_manager.get_color('text_primary')
        
        ctk_kwargs['corner_radius'] = 6
        ctk_kwargs['font'] = self.theme_manager.get_font('body')
        
        return ctk_kwargs
    
    def _apply_traditional_style(self):
        """为传统按钮应用样式"""
        # 这里可以配置ttk.Style来模拟现代化外观
        pass
    
    def pack(self, **kwargs):
        self.button.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.button.grid(**kwargs)
    
    def configure(self, **kwargs):
        self.button.configure(**kwargs)

class ModernLabel:
    """现代化标签组件"""
    
    def __init__(self, parent, text, theme_manager: ThemeManager = None, 
                 text_style='body', **kwargs):
        self.theme_manager = theme_manager or ThemeManager()
        
        if self.theme_manager.is_customtkinter_available():
            self.label = ctk.CTkLabel(
                parent, 
                text=text,
                font=self.theme_manager.get_font(text_style),
                text_color=self.theme_manager.get_color('text_primary'),
                **kwargs
            )
        else:
            self.label = tk.Label(
                parent, 
                text=text,
                font=self.theme_manager.get_font(text_style),
                fg=self.theme_manager.get_color('text_primary'),
                bg=self.theme_manager.get_color('background'),
                **kwargs
            )
    
    def pack(self, **kwargs):
        self.label.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.label.grid(**kwargs)
    
    def configure(self, **kwargs):
        self.label.configure(**kwargs)

class ModernProgressBar:
    """现代化进度条组件"""
    
    def __init__(self, parent, theme_manager: ThemeManager = None, **kwargs):
        self.theme_manager = theme_manager or ThemeManager()
        
        if self.theme_manager.is_customtkinter_available():
            self.progress = ctk.CTkProgressBar(
                parent,
                progress_color=self.theme_manager.get_color('primary'),
                **kwargs
            )
        else:
            self.progress = ttk.Progressbar(parent, **kwargs)
    
    def set(self, value):
        """设置进度值 (0.0 - 1.0)"""
        self.progress.set(value)
    
    def pack(self, **kwargs):
        self.progress.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.progress.grid(**kwargs)

class ModernEntry:
    """现代化输入框组件"""
    
    def __init__(self, parent, placeholder_text="", theme_manager: ThemeManager = None, **kwargs):
        self.theme_manager = theme_manager or ThemeManager()
        
        if self.theme_manager.is_customtkinter_available():
            self.entry = ctk.CTkEntry(
                parent,
                placeholder_text=placeholder_text,
                font=self.theme_manager.get_font('body'),
                **kwargs
            )
        else:
            self.entry = tk.Entry(
                parent,
                font=self.theme_manager.get_font('body'),
                **kwargs
            )
            if placeholder_text:
                self._setup_placeholder(placeholder_text)
    
    def _setup_placeholder(self, placeholder_text):
        """为传统Entry设置placeholder效果"""
        self.entry.insert(0, placeholder_text)
        self.entry.config(fg='grey')
        
        def on_focus_in(event):
            if self.entry.get() == placeholder_text:
                self.entry.delete(0, tk.END)
                self.entry.config(fg='black')
        
        def on_focus_out(event):
            if not self.entry.get():
                self.entry.insert(0, placeholder_text)
                self.entry.config(fg='grey')
        
        self.entry.bind('<FocusIn>', on_focus_in)
        self.entry.bind('<FocusOut>', on_focus_out)
    
    def pack(self, **kwargs):
        self.entry.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.entry.grid(**kwargs)
    
    def get(self):
        return self.entry.get()
    
    def set(self, value):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)