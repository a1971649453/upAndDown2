# ui/themes/theme_manager.py
"""
主题管理器 - 现代化UI主题系统
提供亮色/暗色主题切换，LocalSend风格的卡片式设计
"""

import tkinter as tk
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

class ThemeManager:
    """统一的主题管理器，支持CustomTkinter和传统Tkinter fallback"""
    
    # 色彩系统定义
    COLORS = {
        'light': {
            'primary': '#0078D7',
            'primary_hover': '#005a9e',
            'secondary': '#f0f0f0',
            'surface': '#ffffff',
            'background': '#fafafa',
            'text_primary': '#1f1f1f',
            'text_secondary': '#5f5f5f',
            'border': '#e1e1e1',
            'success': '#107c10',
            'warning': '#ff8c00',
            'error': '#d83b01',
            'card_bg': '#ffffff',
            'card_border': '#e1e1e1',
        },
        'dark': {
            'primary': '#0078D7',
            'primary_hover': '#106ebe',
            'secondary': '#2d2d2d',
            'surface': '#1e1e1e',
            'background': '#161616',
            'text_primary': '#f5f5f5',  # 提高对比度：更亮的白色
            'text_secondary': '#d0d0d0',  # 提高对比度：更亮的灰色
            'border': '#404040',
            'success': '#10ac10',  # 稍微增加亮度
            'warning': '#ffaa33',  # 稍微增加亮度
            'error': '#ff6b6b',    # 稍微增加亮度
            'card_bg': '#2d2d2d',
            'card_border': '#505050',  # 增加边框对比度
        }
    }
    
    # 字体系统
    FONTS = {
        'title': ('Segoe UI', 16, 'bold'),
        'heading': ('Segoe UI', 14, 'bold'),
        'body': ('Segoe UI', 11),
        'caption': ('Segoe UI', 10),
        'code': ('Consolas', 10),
    }
    
    # 间距系统
    SPACING = {
        'xs': 4,
        'sm': 8,
        'md': 16,
        'lg': 24,
        'xl': 32,
    }
    
    def __init__(self):
        self.current_theme = 'light'
        self.ctk_available = CTK_AVAILABLE
        self._setup_customtkinter()
    
    def _setup_customtkinter(self):
        """初始化CustomTkinter设置"""
        if self.ctk_available:
            ctk.set_appearance_mode("light")
            ctk.set_default_color_theme("blue")
    
    def set_theme(self, theme_name):
        """切换主题"""
        if theme_name in self.COLORS:
            self.current_theme = theme_name
            if self.ctk_available:
                ctk.set_appearance_mode(theme_name)
    
    def get_color(self, color_key):
        """获取当前主题的颜色"""
        return self.COLORS[self.current_theme].get(color_key, '#000000')
    
    def get_font(self, font_key):
        """获取字体配置"""
        return self.FONTS.get(font_key, self.FONTS['body'])
    
    def get_spacing(self, spacing_key):
        """获取间距值"""
        return self.SPACING.get(spacing_key, 8)
    
    def is_customtkinter_available(self):
        """检查CustomTkinter是否可用"""
        return self.ctk_available
    
    def create_card_style(self):
        """返回卡片样式配置"""
        return {
            'bg': self.get_color('card_bg'),
            'relief': 'flat',
            'bd': 1,
            'highlightthickness': 1,
            'highlightcolor': self.get_color('card_border'),
            'highlightbackground': self.get_color('card_border'),
        }