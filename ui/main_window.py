# ui/main_window.py
"""
现代化主窗口 - 基于CustomTkinter的现代化界面
支持LocalSend风格设计、响应式布局和传统Tkinter fallback
"""

import tkinter as tk
from tkinter import ttk, messagebox
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    # Fallback到传统Tkinter和ttkthemes
    try:
        from ttkthemes import ThemedTk
        TTKTHEMES_AVAILABLE = True
    except ImportError:
        TTKTHEMES_AVAILABLE = False

from .themes.theme_manager import ThemeManager
from .components.base_components import ModernFrame, ModernLabel, ModernButton
from .layouts.responsive_layout import ResponsiveLayoutManager, AdaptiveThemeManager

class ModernMainWindow:
    """现代化主窗口框架 - 支持响应式布局"""
    
    def __init__(self, title="云内端文件上传工具", version="v5.0"):
        self.title = title
        self.version = version
        
        # 初始化主窗口
        self._create_root_window()
        self._setup_window_properties()
        
        # 初始化主题和布局管理器
        self.theme_manager = ThemeManager()
        self.layout_manager = ResponsiveLayoutManager(self.root)
        self.adaptive_theme = AdaptiveThemeManager(self.theme_manager, self.layout_manager)
        
        self._setup_modern_styles()
        
        # 布局容器
        self.main_container = None
        self.content_area = None
        
        # 注册布局变化回调
        self.layout_manager.register_layout_callback(self._on_responsive_change)
    
    def _create_root_window(self):
        """创建根窗口，优先使用CustomTkinter"""
        if CTK_AVAILABLE:
            # 使用CustomTkinter
            self.root = ctk.CTk()
            ctk.set_appearance_mode("light")  # 默认亮色主题
            ctk.set_default_color_theme("blue")
        else:
            # Fallback策略
            try:
                # 尝试使用ttkthemes
                self.root = ThemedTk(theme="plastik")
            except:
                # 最终fallback到标准Tkinter
                self.root = tk.Tk()
                self._show_fallback_notice()
    
    def _show_fallback_notice(self):
        """显示fallback提示"""
        def show_notice():
            messagebox.showinfo(
                "界面兼容模式", 
                "检测到CustomTkinter不可用，已切换到兼容模式。\n"
                "建议安装CustomTkinter以获得最佳体验：\n"
                "pip install customtkinter"
            )
        # 延迟显示，确保窗口已创建
        self.root.after(100, show_notice)
    
    def _setup_window_properties(self):
        """设置窗口基本属性"""
        self.root.title(f"{self.title} {self.version} - 现代化版")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 设置窗口图标(如果有的话)
        # self.root.iconbitmap("path/to/icon.ico")
        
        # 居中显示
        self._center_window()
    
    def _center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _on_responsive_change(self, breakpoint):
        """响应式布局变化回调"""
        self.update_status(f"布局已适配到 {breakpoint} 断点")
        # 这里可以添加更多响应式变化的处理逻辑
    
    def _setup_modern_styles(self):
        """设置现代化样式"""
        if not self.theme_manager.is_customtkinter_available():
            # 为传统Tkinter设置现代化样式
            style = ttk.Style(self.root)
            
            # 配置基础样式
            style.configure("Modern.TFrame", 
                           background=self.theme_manager.get_color('background'),
                           relief='flat')
            
            style.configure("Card.TFrame",
                           background=self.theme_manager.get_color('card_bg'),
                           relief='flat',
                           borderwidth=1)
            
            style.configure("Modern.TLabel",
                           background=self.theme_manager.get_color('background'),
                           foreground=self.theme_manager.get_color('text_primary'),
                           font=self.theme_manager.get_font('body'))
            
            style.configure("Title.TLabel",
                           background=self.theme_manager.get_color('background'),
                           foreground=self.theme_manager.get_color('text_primary'),
                           font=self.theme_manager.get_font('title'))
            
            style.configure("Modern.TButton",
                           font=self.theme_manager.get_font('body'))
            
            style.configure("Primary.TButton",
                           font=self.theme_manager.get_font('body'))
            
            # 映射按钮颜色
            style.map('Primary.TButton',
                     background=[('active', self.theme_manager.get_color('primary_hover')), 
                               ('!disabled', self.theme_manager.get_color('primary'))],
                     foreground=[('!disabled', 'white')])
    
    def create_layout(self):
        """创建主要布局结构"""
        # 主容器
        if self.theme_manager.is_customtkinter_available():
            self.main_container = ctk.CTkFrame(self.root, corner_radius=0)
            self.main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        else:
            self.main_container = ttk.Frame(self.root, style="Modern.TFrame")
            self.main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # 创建标题栏
        self._create_title_bar()
        
        # 创建内容区域
        self._create_content_area()
        
        # 创建状态栏
        self._create_status_bar()
    
    def _create_title_bar(self):
        """创建标题栏"""
        # 获取响应式间距
        spacing = self.adaptive_theme.get_responsive_spacing('md')
        title_font = self.adaptive_theme.get_responsive_font('title')
        
        if self.theme_manager.is_customtkinter_available():
            title_frame = ctk.CTkFrame(self.main_container, height=60, corner_radius=0)
            title_frame.pack(fill=tk.X, padx=0, pady=(0, spacing))
            title_frame.pack_propagate(False)
            
            # 标题
            title_label = ctk.CTkLabel(
                title_frame, 
                text=f"{self.title} {self.version}",
                font=title_font,
                text_color=self.theme_manager.get_color('text_primary')
            )
            title_label.pack(side=tk.LEFT, padx=spacing, pady=spacing)
            
            # 主题切换按钮
            theme_btn = ctk.CTkButton(
                title_frame,
                text="🌙 切换主题",
                width=100,
                command=self.toggle_theme,
                font=self.adaptive_theme.get_responsive_font('body')
            )
            theme_btn.pack(side=tk.RIGHT, padx=spacing, pady=spacing)
            
        else:
            title_frame = ttk.Frame(self.main_container, style="Card.TFrame")
            title_frame.pack(fill=tk.X, pady=(0, spacing))
            
            title_label = ttk.Label(
                title_frame,
                text=f"{self.title} {self.version}",
                style="Title.TLabel",
                font=title_font
            )
            title_label.pack(side=tk.LEFT, padx=spacing, pady=spacing)
            
            theme_btn = ttk.Button(
                title_frame,
                text="🌙 切换主题",
                command=self.toggle_theme,
                style="Modern.TButton"
            )
            theme_btn.pack(side=tk.RIGHT, padx=spacing, pady=spacing)
    
    def _create_content_area(self):
        """创建主要内容区域"""
        spacing = self.adaptive_theme.get_responsive_spacing('sm')
        
        if self.theme_manager.is_customtkinter_available():
            self.content_area = ctk.CTkFrame(self.main_container, corner_radius=8)
            self.content_area.pack(fill=tk.BOTH, expand=True, padx=spacing, pady=spacing//2)
        else:
            self.content_area = ttk.Frame(self.main_container, style="Card.TFrame")
            self.content_area.pack(fill=tk.BOTH, expand=True, pady=spacing//2)
    
    def _create_status_bar(self):
        """创建状态栏"""
        spacing = self.adaptive_theme.get_responsive_spacing('sm')
        caption_font = self.adaptive_theme.get_responsive_font('caption')
        
        if self.theme_manager.is_customtkinter_available():
            status_frame = ctk.CTkFrame(self.main_container, height=30, corner_radius=0)
            status_frame.pack(fill=tk.X, pady=(spacing, 0))
            status_frame.pack_propagate(False)
            
            self.status_label = ctk.CTkLabel(
                status_frame,
                text="就绪",
                font=caption_font,
                text_color=self.theme_manager.get_color('text_secondary')
            )
            self.status_label.pack(side=tk.LEFT, padx=spacing, pady=4)
            
            # 显示当前断点信息
            breakpoint_label = ctk.CTkLabel(
                status_frame,
                text=f"断点: {self.layout_manager.get_current_breakpoint()}",
                font=caption_font,
                text_color=self.theme_manager.get_color('text_secondary')
            )
            breakpoint_label.pack(side=tk.RIGHT, padx=spacing, pady=4)
            self.breakpoint_label = breakpoint_label
            
        else:
            status_frame = ttk.Frame(self.main_container, style="Modern.TFrame")
            status_frame.pack(fill=tk.X, pady=(spacing, 0))
            
            self.status_label = ttk.Label(
                status_frame,
                text="就绪",
                style="Modern.TLabel",
                font=caption_font
            )
            self.status_label.pack(side=tk.LEFT, padx=spacing, pady=4)
            
            breakpoint_label = ttk.Label(
                status_frame,
                text=f"断点: {self.layout_manager.get_current_breakpoint()}",
                style="Modern.TLabel",
                font=caption_font
            )
            breakpoint_label.pack(side=tk.RIGHT, padx=spacing, pady=4)
            self.breakpoint_label = breakpoint_label
    
    def toggle_theme(self):
        """切换主题"""
        current = self.theme_manager.current_theme
        new_theme = 'dark' if current == 'light' else 'light'
        self.theme_manager.set_theme(new_theme)
        
        self.update_status(f"已切换到{'深色' if new_theme == 'dark' else '浅色'}主题")
    
    def update_status(self, message):
        """更新状态栏信息"""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)
    
    def update_breakpoint_display(self):
        """更新断点显示"""
        if hasattr(self, 'breakpoint_label'):
            current_bp = self.layout_manager.get_current_breakpoint()
            self.breakpoint_label.configure(text=f"断点: {current_bp}")
    
    def get_content_area(self):
        """获取内容区域容器，供其他组件使用"""
        return self.content_area
    
    def get_root(self):
        """获取根窗口"""
        return self.root
    
    def get_layout_manager(self):
        """获取布局管理器"""
        return self.layout_manager
    
    def get_adaptive_theme(self):
        """获取自适应主题管理器"""
        return self.adaptive_theme
    
    def show(self):
        """显示窗口"""
        self.create_layout()
        return self.root
    
    def set_close_callback(self, callback):
        """设置关闭回调"""
        self.root.protocol("WM_DELETE_WINDOW", callback)