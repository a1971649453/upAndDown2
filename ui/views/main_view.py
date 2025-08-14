# ui/views/main_view.py
"""
主界面视图 - 现代化的文件上传界面
集成所有UI组件，实现完整的用户界面
"""

import tkinter as tk
from tkinter import ttk
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

from ..components.card_components import FileUploadCard, StatusCard, SettingsCard
from ..components.drag_drop import DragDropFrame, OneClickUpload
from ..layouts.responsive_layout import ResponsiveContainer

class MainView:
    """主界面视图控制器"""
    
    def __init__(self, parent, theme_manager, layout_manager):
        self.parent = parent
        self.theme_manager = theme_manager
        self.layout_manager = layout_manager
        
        # UI组件引用
        self.upload_card = None
        self.status_card = None
        self.settings_card = None
        self.file_list_frame = None
        
        # 回调函数
        self.callbacks = {
            'file_select': None,
            'file_upload': None,
            'monitor_change': None
        }
        
        # 创建主界面
        self._create_main_interface()
    
    def _create_main_interface(self):
        """创建主界面布局"""
        # 创建响应式容器
        self.main_container = ResponsiveContainer(
            self.parent,
            self.layout_manager,
            layout_mode='auto'
        )
        self.main_container.pack(fill='both', expand=True, padx=8, pady=8)
        
        container = self.main_container.get_container()
        
        # 根据屏幕大小决定布局
        if self.layout_manager.is_mobile():
            self._create_mobile_layout(container)
        else:
            self._create_desktop_layout(container)
    
    def _create_desktop_layout(self, container):
        """创建桌面端布局（左右分栏）"""
        if CTK_AVAILABLE:
            # 左侧面板
            left_panel = ctk.CTkFrame(container, fg_color="transparent")
            left_panel.pack(side='left', fill='both', expand=False, padx=(0, 4))
            
            # 右侧面板
            right_panel = ctk.CTkFrame(container, fg_color="transparent")
            right_panel.pack(side='right', fill='both', expand=True, padx=(4, 0))
        else:
            # 传统Tkinter版本
            left_panel = tk.Frame(container, bg=self.theme_manager.get_color('background'))
            left_panel.pack(side='left', fill='both', expand=False, padx=(0, 4))
            
            right_panel = tk.Frame(container, bg=self.theme_manager.get_color('background'))
            right_panel.pack(side='right', fill='both', expand=True, padx=(4, 0))
        
        # 创建左侧组件
        self._create_left_panel_components(left_panel)
        
        # 创建右侧组件
        self._create_right_panel_components(right_panel)
    
    def _create_mobile_layout(self, container):
        """创建移动端布局（垂直布局）"""
        # 移动端采用垂直堆叠布局
        self._create_left_panel_components(container)
        self._create_right_panel_components(container)
    
    def _create_left_panel_components(self, parent):
        """创建左侧面板组件"""
        # 拖拽上传区域
        self.drag_drop_frame = DragDropFrame(parent, self.theme_manager, self._on_files_dropped)
        self.drag_drop_frame.pack(fill='x', pady=(0, 8))
        
        # 文件上传卡片
        self.upload_card = FileUploadCard(parent, self.theme_manager)
        self.upload_card.pack(fill='x', pady=(0, 8))
        
        # 绑定上传卡片事件
        self.upload_card.set_select_command(self._on_select_files)
        self.upload_card.set_upload_command(self._on_upload_files)
        
        # 一键上传按钮
        self.one_click_upload = OneClickUpload(parent, self.theme_manager, self._on_one_click_upload)
        self.one_click_upload.pack(fill='x', pady=(0, 8))
        
        # 设置卡片
        self.settings_card = SettingsCard(parent, self.theme_manager)
        self.settings_card.pack(fill='x', pady=(0, 8))
        
        # 文件列表卡片
        self._create_file_list_card(parent)
    
    def _create_right_panel_components(self, parent):
        """创建右侧面板组件"""
        # 状态/日志卡片
        self.status_card = StatusCard(parent, self.theme_manager, title="📊 活动日志")
        self.status_card.pack(fill='both', expand=True)
        
        # 添加欢迎消息
        self.status_card.add_status_item("现代化界面已加载", "success")
        self.status_card.add_status_item("支持拖拽上传和剪切板监听", "info")
        
        framework = "CustomTkinter" if CTK_AVAILABLE else "传统Tkinter"
        self.status_card.add_status_item(f"UI框架: {framework}", "info")
    
    def _create_file_list_card(self, parent):
        """创建文件列表卡片"""
        if CTK_AVAILABLE:
            # CustomTkinter版本的文件列表
            list_frame = ctk.CTkFrame(parent)
            list_frame.pack(fill='both', expand=True)
            
            # 标题
            title_label = ctk.CTkLabel(
                list_frame,
                text="📁 文件列表",
                font=self.theme_manager.get_font('heading'),
                anchor="w"
            )
            title_label.pack(fill='x', padx=16, pady=(16, 8))
            
            # 文件列表区域（使用CTkScrollableFrame）
            self.file_list_frame = ctk.CTkScrollableFrame(
                list_frame,
                height=200,
                fg_color=self.theme_manager.get_color('secondary')
            )
            self.file_list_frame.pack(fill='both', expand=True, padx=16, pady=(0, 16))
            
        else:
            # 传统Tkinter版本
            list_frame = tk.Frame(parent, **self.theme_manager.create_card_style())
            list_frame.pack(fill='both', expand=True)
            
            title_label = tk.Label(
                list_frame,
                text="📁 文件列表",
                font=self.theme_manager.get_font('heading'),
                bg=self.theme_manager.get_color('card_bg'),
                fg=self.theme_manager.get_color('text_primary'),
                anchor="w"
            )
            title_label.pack(fill='x', padx=16, pady=(16, 8))
            
            # 创建可滚动的文件列表
            canvas_frame = tk.Frame(list_frame, bg=self.theme_manager.get_color('card_bg'))
            canvas_frame.pack(fill='both', expand=True, padx=16, pady=(0, 16))
            
            canvas = tk.Canvas(canvas_frame, bg=self.theme_manager.get_color('secondary'), height=200)
            scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
            
            self.file_list_frame = tk.Frame(canvas, bg=self.theme_manager.get_color('secondary'))
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # 绑定滚动事件
            canvas.create_window((0, 0), window=self.file_list_frame, anchor="nw")
            self.file_list_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
    
    def _on_select_files(self):
        """选择文件回调"""
        if self.callbacks['file_select']:
            self.callbacks['file_select']()
        else:
            self.status_card.add_status_item("选择文件功能待实现", "warning")
    
    def _on_upload_files(self):
        """上传文件回调"""
        if self.callbacks['file_upload']:
            self.callbacks['file_upload']()
        else:
            self.status_card.add_status_item("上传文件功能待实现", "warning")
    
    def _on_files_dropped(self, files):
        """拖拽文件回调"""
        self.status_card.add_status_item(f"检测到拖拽文件: {len(files)}个", "info")
        # 调用选择文件的回调，传入拖拽的文件列表
        if hasattr(self, '_drag_drop_callback') and self._drag_drop_callback:
            self._drag_drop_callback(files)
        else:
            # 如果没有专门的拖拽回调，添加到文件列表
            for file_path in files:
                import os
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                size_str = self._format_file_size(file_size)
                self.add_file_item(file_name, size_str, "待上传")
    
    def _on_one_click_upload(self):
        """一键上传回调"""
        self.status_card.add_status_item("一键上传功能激活", "info")
        # 模拟选择文件并立即上传
        if self.callbacks['file_select']:
            self.callbacks['file_select']()
            # 延迟一点时间后自动上传
            if hasattr(self.parent, 'after'):
                self.parent.after(500, lambda: self._on_upload_files() if self.callbacks['file_upload'] else None)
    
    def _format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / 1024 ** 2:.1f} MB"
    
    def set_callback(self, event_name, callback):
        """设置回调函数"""
        if event_name in self.callbacks:
            self.callbacks[event_name] = callback
        elif event_name == 'drag_drop':
            self._drag_drop_callback = callback
    
    def add_file_item(self, filename, size, status="待上传"):
        """添加文件项到列表"""
        if CTK_AVAILABLE:
            # CustomTkinter版本
            file_item = ctk.CTkFrame(self.file_list_frame)
            file_item.pack(fill='x', pady=2)
            
            # 文件图标
            icon_label = ctk.CTkLabel(file_item, text="📄", width=30)
            icon_label.pack(side='left', padx=(8, 4))
            
            # 文件信息
            info_frame = ctk.CTkFrame(file_item, fg_color="transparent")
            info_frame.pack(side='left', fill='x', expand=True, padx=4)
            
            name_label = ctk.CTkLabel(info_frame, text=filename, anchor="w")
            name_label.pack(fill='x')
            
            detail_label = ctk.CTkLabel(
                info_frame, 
                text=f"{size} | {status}",
                font=self.theme_manager.get_font('caption'),
                anchor="w"
            )
            detail_label.pack(fill='x')
            
            # 状态指示
            status_colors = {
                "待上传": "gray",
                "上传中": "orange", 
                "成功": "green",
                "失败": "red"
            }
            
            status_label = ctk.CTkLabel(
                file_item,
                text="●",
                text_color=status_colors.get(status, "gray"),
                width=20
            )
            status_label.pack(side='right', padx=8)
            
        else:
            # 传统Tkinter版本
            file_item = tk.Frame(
                self.file_list_frame, 
                bg=self.theme_manager.get_color('background'),
                relief='ridge',
                bd=1
            )
            file_item.pack(fill='x', pady=2, padx=4)
            
            # 文件图标
            icon_label = tk.Label(
                file_item,
                text="📄",
                bg=self.theme_manager.get_color('background'),
                width=3
            )
            icon_label.pack(side='left', padx=(8, 4))
            
            # 文件信息
            info_text = f"{filename}\n{size} | {status}"
            info_label = tk.Label(
                file_item,
                text=info_text,
                bg=self.theme_manager.get_color('background'),
                fg=self.theme_manager.get_color('text_primary'),
                anchor="w",
                justify="left"
            )
            info_label.pack(side='left', fill='x', expand=True, padx=4)
            
            # 状态指示
            status_colors = {
                "待上传": "gray",
                "上传中": "orange",
                "成功": "green", 
                "失败": "red"
            }
            
            status_label = tk.Label(
                file_item,
                text="●",
                fg=status_colors.get(status, "gray"),
                bg=self.theme_manager.get_color('background')
            )
            status_label.pack(side='right', padx=8)
    
    def clear_file_list(self):
        """清空文件列表"""
        if CTK_AVAILABLE:
            for widget in self.file_list_frame.winfo_children():
                widget.destroy()
        else:
            for widget in self.file_list_frame.winfo_children():
                widget.destroy()
    
    def add_status_message(self, message, msg_type="info"):
        """添加状态消息"""
        if self.status_card:
            self.status_card.add_status_item(message, msg_type)
    
    def get_monitor_settings(self):
        """获取监控设置"""
        if self.settings_card:
            return {
                'text_monitor': self.settings_card.get_text_monitor_state(),
                'file_monitor': self.settings_card.get_file_monitor_state()
            }
        return {'text_monitor': False, 'file_monitor': False}