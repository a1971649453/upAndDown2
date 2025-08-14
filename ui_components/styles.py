# styles.py - 现代化设计系统
# 基于云外端v5.9的成功设计，提供统一的样式规范

"""
现代化UI样式系统
=================

使用方法：
from ui_components.styles import ModernStyles

style = ModernStyles()
colors = style.get_colors()
fonts = style.get_fonts()
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

import tkinter as tk
from tkinter import ttk


class ModernStyles:
    """现代化设计系统 - 与云外端v5.9保持一致"""
    
    def __init__(self):
        self.setup_design_system()
        
    def setup_design_system(self):
        """初始化设计系统"""
        # LocalSend风格色彩系统
        self.colors = {
            'primary': '#3b82f6',        # 蓝色主色调
            'primary_hover': '#2563eb',  # 主色调悬停
            'success': '#10b981',        # 现代绿色
            'success_hover': '#059669',  # 成功色悬停
            'danger': '#ef4444',         # 温和红色
            'danger_hover': '#dc2626',   # 危险色悬停
            'warning': '#f59e0b',        # 优雅橙色
            'warning_hover': '#d97706',  # 警告色悬停
            'background': '#f8fafc',     # 浅灰蓝背景
            'card': '#ffffff',           # 纯白卡片
            'card_hover': '#f1f5f9',     # 卡片悬停
            'text': '#0f172a',           # 主文本色
            'text_secondary': '#64748b', # 次要文本色
            'text_light': '#94a3b8',     # 浅色文本
            'border': '#e2e8f0',         # 边框色
            'border_focus': '#3b82f6',   # 聚焦边框
            'input_bg': '#ffffff',       # 输入框背景
            'disabled': '#94a3b8',       # 禁用状态
        }
        
        # 字体系统
        self.fonts = {
            'heading_large': ('Segoe UI', 18, 'bold'),
            'heading_medium': ('Segoe UI', 16, 'bold'),
            'heading_small': ('Segoe UI', 14, 'bold'),
            'body_large': ('Segoe UI', 12, 'normal'),
            'body_medium': ('Segoe UI', 11, 'normal'),
            'body_small': ('Segoe UI', 10, 'normal'),
            'caption': ('Segoe UI', 9, 'normal'),
            'monospace': ('Consolas', 10, 'normal'),
        }
        
        # 间距系统
        self.spacing = {
            'xs': 4,
            'sm': 8,
            'md': 16,
            'lg': 24,
            'xl': 32,
            'xxl': 48,
        }
        
        # 圆角系统
        self.radius = {
            'sm': 4,
            'md': 8,
            'lg': 12,
            'xl': 16,
        }
        
        # 阴影系统
        self.shadows = {
            'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
            'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
            'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
        }
    
    def get_colors(self):
        """获取色彩系统"""
        return self.colors.copy()
    
    def get_fonts(self):
        """获取字体系统"""
        return self.fonts.copy()
    
    def get_spacing(self):
        """获取间距系统"""
        return self.spacing.copy()
    
    def get_radius(self):
        """获取圆角系统"""
        return self.radius.copy()
    
    def setup_ctk_theme(self):
        """设置CustomTkinter主题"""
        if not CTK_AVAILABLE:
            return
            
        # 设置全局主题
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # 自定义主题配置
        ctk.ThemeManager.theme["CTkButton"]["fg_color"] = [self.colors['primary'], self.colors['primary']]
        ctk.ThemeManager.theme["CTkButton"]["hover_color"] = [self.colors['primary_hover'], self.colors['primary_hover']]
    
    def get_ttk_style(self, parent_widget):
        """获取TTK样式配置"""
        style = ttk.Style(parent_widget)
        
        # 配置卡片样式
        style.configure("Card.TFrame", 
                       background=self.colors['card'],
                       relief="flat",
                       borderwidth=1)
        
        # 配置标题样式
        style.configure("Heading.TLabel",
                       background=self.colors['card'],
                       foreground=self.colors['text'],
                       font=self.fonts['heading_medium'])
        
        # 配置正文样式
        style.configure("Body.TLabel",
                       background=self.colors['card'],
                       foreground=self.colors['text'],
                       font=self.fonts['body_medium'])
        
        # 配置次要文本样式
        style.configure("Secondary.TLabel",
                       background=self.colors['card'],
                       foreground=self.colors['text_secondary'],
                       font=self.fonts['body_small'])
        
        # 配置按钮样式
        style.configure("Primary.TButton",
                       background=self.colors['primary'],
                       foreground='white',
                       font=self.fonts['body_medium'],
                       focuscolor='none')
        
        style.map("Primary.TButton",
                 background=[('active', self.colors['primary_hover']),
                           ('pressed', self.colors['primary_hover'])])
        
        # 配置成功按钮样式
        style.configure("Success.TButton",
                       background=self.colors['success'],
                       foreground='white',
                       font=self.fonts['body_medium'],
                       focuscolor='none')
        
        style.map("Success.TButton",
                 background=[('active', self.colors['success_hover']),
                           ('pressed', self.colors['success_hover'])])
        
        # 配置危险按钮样式
        style.configure("Danger.TButton",
                       background=self.colors['danger'],
                       foreground='white',
                       font=self.fonts['body_medium'],
                       focuscolor='none')
        
        style.map("Danger.TButton",
                 background=[('active', self.colors['danger_hover']),
                           ('pressed', self.colors['danger_hover'])])
        
        return style


class ComponentStyles:
    """组件特定样式"""
    
    def __init__(self, modern_styles: ModernStyles):
        self.styles = modern_styles
        self.colors = modern_styles.get_colors()
        self.fonts = modern_styles.get_fonts()
        self.spacing = modern_styles.get_spacing()
        self.radius = modern_styles.get_radius()
    
    def get_card_config(self):
        """获取卡片组件配置"""
        if CTK_AVAILABLE:
            return {
                'fg_color': self.colors['card'],
                'corner_radius': self.radius['lg'],
                'border_width': 1,
                'border_color': self.colors['border']
            }
        else:
            return {
                'bg': self.colors['card'],
                'relief': 'flat',
                'bd': 1,
                'highlightbackground': self.colors['border']
            }
    
    def get_button_config(self, variant='primary'):
        """获取按钮组件配置"""
        color_map = {
            'primary': (self.colors['primary'], self.colors['primary_hover']),
            'success': (self.colors['success'], self.colors['success_hover']),
            'danger': (self.colors['danger'], self.colors['danger_hover']),
            'warning': (self.colors['warning'], self.colors['warning_hover']),
        }
        
        bg_color, hover_color = color_map.get(variant, color_map['primary'])
        
        if CTK_AVAILABLE:
            return {
                'fg_color': bg_color,
                'hover_color': hover_color,
                'corner_radius': self.radius['md'],
                'font': self.fonts['body_medium'],
                'text_color': 'white'
            }
        else:
            return {
                'bg': bg_color,
                'fg': 'white',
                'font': self.fonts['body_medium'],
                'relief': 'flat',
                'bd': 0,
                'padx': self.spacing['md'],
                'pady': self.spacing['sm']
            }
    
    def get_label_config(self, variant='body'):
        """获取标签组件配置"""
        font_map = {
            'heading': self.fonts['heading_medium'],
            'body': self.fonts['body_medium'],
            'caption': self.fonts['body_small'],
        }
        
        color_map = {
            'heading': self.colors['text'],
            'body': self.colors['text'],
            'caption': self.colors['text_secondary'],
        }
        
        font = font_map.get(variant, self.fonts['body_medium'])
        color = color_map.get(variant, self.colors['text'])
        
        if CTK_AVAILABLE:
            return {
                'font': font,
                'text_color': color,
                'bg_color': 'transparent'
            }
        else:
            return {
                'font': font,
                'fg': color,
                'bg': self.colors['card']
            }
    
    def get_progress_config(self):
        """获取进度条组件配置"""
        if CTK_AVAILABLE:
            return {
                'fg_color': self.colors['border'],
                'progress_color': self.colors['primary'],
                'corner_radius': self.radius['sm'],
                'height': 8
            }
        else:
            return {
                'style': 'Horizontal.TProgressbar'
            }


# 全局样式实例
modern_styles = ModernStyles()
component_styles = ComponentStyles(modern_styles)