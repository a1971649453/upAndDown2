# ui/components/card_components.py
"""
卡片式组件 - LocalSend风格的现代化卡片设计
"""

import tkinter as tk
from tkinter import ttk
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

from ..themes.theme_manager import ThemeManager
from .base_components import ModernFrame, ModernLabel, ModernButton
from .drag_drop import DragDropMixin

class FileUploadCard:
    """文件上传卡片组件 - LocalSend风格"""
    
    def __init__(self, parent, theme_manager: ThemeManager, **kwargs):
        self.theme_manager = theme_manager
        self.parent = parent
        
        # 主卡片容器
        self.card_frame = ModernFrame(parent, theme_manager, card_style=True)
        
        # 内部布局
        self._create_layout()
    
    def _create_layout(self):
        """创建卡片内部布局"""
        if self.theme_manager.is_customtkinter_available():
            # 使用CustomTkinter布局
            self._create_ctk_layout()
        else:
            # 使用传统Tkinter布局
            self._create_traditional_layout()
    
    def _create_ctk_layout(self):
        """CustomTkinter版本的布局"""
        main_widget = self.card_frame.get_widget()
        
        # 标题区域
        title_frame = ctk.CTkFrame(main_widget, fg_color="transparent")
        title_frame.pack(fill=tk.X, padx=16, pady=(16, 8))
        
        # 图标和标题
        icon_label = ctk.CTkLabel(
            title_frame, 
            text="📁", 
            font=("Segoe UI", 24),
            width=40
        )
        icon_label.pack(side=tk.LEFT)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="文件上传",
            font=self.theme_manager.get_font('heading'),
            anchor="w"
        )
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        
        # 拖拽区域
        self.drop_area = ctk.CTkFrame(
            main_widget,
            height=120,
            fg_color=self.theme_manager.get_color('secondary'),
            border_width=2,
            border_color=self.theme_manager.get_color('border'),
            corner_radius=8
        )
        self.drop_area.pack(fill=tk.X, padx=16, pady=8)
        self.drop_area.pack_propagate(False)
        
        # 拖拽区域内容
        drop_content = ctk.CTkFrame(self.drop_area, fg_color="transparent")
        drop_content.pack(expand=True)
        
        ctk.CTkLabel(
            drop_content,
            text="🎯",
            font=("Segoe UI", 32)
        ).pack(pady=(8, 4))
        
        ctk.CTkLabel(
            drop_content,
            text="拖拽文件到此处或点击选择",
            font=self.theme_manager.get_font('body'),
            text_color=self.theme_manager.get_color('text_secondary')
        ).pack()
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_widget, fg_color="transparent")
        button_frame.pack(fill=tk.X, padx=16, pady=(8, 16))
        
        select_btn = ctk.CTkButton(
            button_frame,
            text="📁 选择文件",
            font=self.theme_manager.get_font('body'),
            width=120
        )
        select_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        upload_btn = ctk.CTkButton(
            button_frame,
            text="🚀 开始上传",
            font=self.theme_manager.get_font('body'),
            fg_color=self.theme_manager.get_color('primary'),
            hover_color=self.theme_manager.get_color('primary_hover'),
            width=120
        )
        upload_btn.pack(side=tk.RIGHT)
        
        # 存储按钮引用
        self.select_button = select_btn
        self.upload_button = upload_btn
        
        # 初始化拖拽功能
        self._setup_drag_drop()
        
    def _setup_drag_drop(self):
        """为上传卡片设置拖拽功能"""
        try:
            self.drag_drop = DragDropMixin(self.drop_area, self._handle_dropped_files)
        except Exception as e:
            print(f"拖拽功能初始化失败: {e}")
            self.drag_drop = None
    
    def _handle_dropped_files(self, files):
        """处理拖拽文件"""
        if hasattr(self, '_drag_callback') and self._drag_callback:
            self._drag_callback(files)
    
    def _setup_drag_drop_events(self, callback):
        """设置拖拽事件回调（由MainView调用）"""
        self._drag_callback = callback
    
    def _create_traditional_layout(self):
        """传统Tkinter版本的布局"""
        main_widget = self.card_frame.get_widget()
        
        # 标题区域
        title_frame = tk.Frame(main_widget, bg=self.theme_manager.get_color('card_bg'))
        title_frame.pack(fill=tk.X, padx=16, pady=(16, 8))
        
        # 图标和标题
        icon_label = tk.Label(
            title_frame,
            text="📁",
            font=("Segoe UI", 24),
            bg=self.theme_manager.get_color('card_bg'),
            width=3
        )
        icon_label.pack(side=tk.LEFT)
        
        title_label = tk.Label(
            title_frame,
            text="文件上传",
            font=self.theme_manager.get_font('heading'),
            bg=self.theme_manager.get_color('card_bg'),
            fg=self.theme_manager.get_color('text_primary'),
            anchor="w"
        )
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        
        # 拖拽区域
        self.drop_area = tk.Frame(
            main_widget,
            height=120,
            bg=self.theme_manager.get_color('secondary'),
            relief='ridge',
            bd=1
        )
        self.drop_area.pack(fill=tk.X, padx=16, pady=8)
        self.drop_area.pack_propagate(False)
        
        # 拖拽区域内容
        tk.Label(
            self.drop_area,
            text="🎯\n拖拽文件到此处或点击选择",
            font=self.theme_manager.get_font('body'),
            bg=self.theme_manager.get_color('secondary'),
            fg=self.theme_manager.get_color('text_secondary'),
            justify=tk.CENTER
        ).pack(expand=True)
        
        # 按钮区域
        button_frame = tk.Frame(main_widget, bg=self.theme_manager.get_color('card_bg'))
        button_frame.pack(fill=tk.X, padx=16, pady=(8, 16))
        
        self.select_button = tk.Button(
            button_frame,
            text="📁 选择文件",
            font=self.theme_manager.get_font('body'),
            width=12
        )
        self.select_button.pack(side=tk.LEFT, padx=(0, 8))
        
        self.upload_button = tk.Button(
            button_frame,
            text="🚀 开始上传",
            font=self.theme_manager.get_font('body'),
            bg=self.theme_manager.get_color('primary'),
            fg='white',
            width=12
        )
        self.upload_button.pack(side=tk.RIGHT)
    
    def set_select_command(self, command):
        """设置选择文件命令"""
        self.select_button.configure(command=command)
    
    def set_upload_command(self, command):
        """设置上传命令"""
        self.upload_button.configure(command=command)
    
    def pack(self, **kwargs):
        self.card_frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.card_frame.grid(**kwargs)

class StatusCard:
    """状态显示卡片组件"""
    
    def __init__(self, parent, theme_manager: ThemeManager, title="状态", **kwargs):
        self.theme_manager = theme_manager
        self.title = title
        
        # 主卡片容器
        self.card_frame = ModernFrame(parent, theme_manager, card_style=True)
        
        # 创建布局
        self._create_layout()
    
    def _create_layout(self):
        """创建状态卡片布局"""
        main_widget = self.card_frame.get_widget()
        
        if self.theme_manager.is_customtkinter_available():
            # CustomTkinter版本
            # 标题
            self.title_label = ctk.CTkLabel(
                main_widget,
                text=self.title,
                font=self.theme_manager.get_font('heading'),
                anchor="w"
            )
            self.title_label.pack(fill=tk.X, padx=16, pady=(16, 8))
            
            # 状态内容区域
            self.content_frame = ctk.CTkScrollableFrame(
                main_widget,
                fg_color="transparent"
            )
            self.content_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
            
        else:
            # 传统Tkinter版本
            self.title_label = tk.Label(
                main_widget,
                text=self.title,
                font=self.theme_manager.get_font('heading'),
                bg=self.theme_manager.get_color('card_bg'),
                fg=self.theme_manager.get_color('text_primary'),
                anchor="w"
            )
            self.title_label.pack(fill=tk.X, padx=16, pady=(16, 8))
            
            # 创建滚动区域（修复版）
            canvas_frame = tk.Frame(main_widget, bg=self.theme_manager.get_color('card_bg'))
            canvas_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
            
            # 创建画布和滚动条
            canvas = tk.Canvas(
                canvas_frame, 
                bg=self.theme_manager.get_color('card_bg'),
                highlightthickness=0
            )
            scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
            
            self.content_frame = tk.Frame(
                canvas, 
                bg=self.theme_manager.get_color('card_bg')
            )
            
            # 布局画布和滚动条
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # 创建滚动窗口
            canvas_window = canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
            
            # 绑定滚动事件
            def configure_scroll_region(event=None):
                canvas.configure(scrollregion=canvas.bbox("all"))
                # 确保内容框架宽度与画布一致
                canvas_width = canvas.winfo_width()
                canvas.itemconfig(canvas_window, width=canvas_width)
            
            self.content_frame.bind("<Configure>", configure_scroll_region)
            canvas.bind("<Configure>", configure_scroll_region)
            
            # 绑定鼠标滚轮事件
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            canvas.bind("<MouseWheel>", _on_mousewheel)  # Windows
            canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
            canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux
    
    def add_status_item(self, message, status_type='info'):
        """添加状态项"""
        icons = {
            'info': "ℹ️",
            'success': "✅", 
            'error': "❌",
            'warning': "⚠️"
        }
        
        icon = icons.get(status_type, "ℹ️")
        
        if self.theme_manager.is_customtkinter_available():
            status_item = ctk.CTkLabel(
                self.content_frame,
                text=f"{icon} {message}",
                font=self.theme_manager.get_font('body'),
                anchor="w"
            )
            status_item.pack(fill=tk.X, pady=2)
        else:
            status_item = tk.Label(
                self.content_frame,
                text=f"{icon} {message}",
                font=self.theme_manager.get_font('body'),
                bg=self.theme_manager.get_color('card_bg'),
                fg=self.theme_manager.get_color('text_primary'),
                anchor="w"
            )
            status_item.pack(fill=tk.X, pady=2)
    
    def pack(self, **kwargs):
        self.card_frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.card_frame.grid(**kwargs)

class SettingsCard:
    """设置卡片组件"""
    
    def __init__(self, parent, theme_manager: ThemeManager, **kwargs):
        self.theme_manager = theme_manager
        
        # 主卡片容器
        self.card_frame = ModernFrame(parent, theme_manager, card_style=True)
        
        # 创建布局
        self._create_layout()
    
    def _create_layout(self):
        """创建设置卡片布局"""
        main_widget = self.card_frame.get_widget()
        
        if self.theme_manager.is_customtkinter_available():
            # 标题
            title_label = ctk.CTkLabel(
                main_widget,
                text="⚙️ 设置",
                font=self.theme_manager.get_font('heading'),
                anchor="w"
            )
            title_label.pack(fill=tk.X, padx=16, pady=(16, 16))
            
            # 监控设置
            monitor_frame = ctk.CTkFrame(main_widget, fg_color="transparent")
            monitor_frame.pack(fill=tk.X, padx=16, pady=(0, 8))
            
            # 添加设置选项
            self.text_monitor_var = tk.BooleanVar()
            self.file_monitor_var = tk.BooleanVar()
            
            text_check = ctk.CTkCheckBox(
                monitor_frame,
                text="监控剪切板文本",
                variable=self.text_monitor_var,
                font=self.theme_manager.get_font('body')
            )
            text_check.pack(anchor="w", pady=4)
            
            file_check = ctk.CTkCheckBox(
                monitor_frame,
                text="监控剪切板文件",
                variable=self.file_monitor_var,
                font=self.theme_manager.get_font('body')
            )
            file_check.pack(anchor="w", pady=4)
            
        else:
            # 传统Tkinter版本
            title_label = tk.Label(
                main_widget,
                text="⚙️ 设置",
                font=self.theme_manager.get_font('heading'),
                bg=self.theme_manager.get_color('card_bg'),
                fg=self.theme_manager.get_color('text_primary'),
                anchor="w"
            )
            title_label.pack(fill=tk.X, padx=16, pady=(16, 16))
            
            monitor_frame = tk.Frame(
                main_widget, 
                bg=self.theme_manager.get_color('card_bg')
            )
            monitor_frame.pack(fill=tk.X, padx=16, pady=(0, 16))
            
            self.text_monitor_var = tk.BooleanVar()
            self.file_monitor_var = tk.BooleanVar()
            
            text_check = tk.Checkbutton(
                monitor_frame,
                text="监控剪切板文本",
                variable=self.text_monitor_var,
                font=self.theme_manager.get_font('body'),
                bg=self.theme_manager.get_color('card_bg'),
                fg=self.theme_manager.get_color('text_primary'),
                anchor="w"
            )
            text_check.pack(anchor="w", pady=4)
            
            file_check = tk.Checkbutton(
                monitor_frame,
                text="监控剪切板文件",
                variable=self.file_monitor_var,
                font=self.theme_manager.get_font('body'),
                bg=self.theme_manager.get_color('card_bg'),
                fg=self.theme_manager.get_color('text_primary'),
                anchor="w"
            )
            file_check.pack(anchor="w", pady=4)
    
    def get_text_monitor_state(self):
        return self.text_monitor_var.get()
    
    def get_file_monitor_state(self):
        return self.file_monitor_var.get()
    
    def set_text_monitor_command(self, command):
        # 这里可以绑定命令到复选框
        pass
    
    def set_file_monitor_command(self, command):
        # 这里可以绑定命令到复选框
        pass
    
    def pack(self, **kwargs):
        self.card_frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.card_frame.grid(**kwargs)