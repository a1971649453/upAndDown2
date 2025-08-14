# ui/components/drag_drop.py
"""
拖拽上传组件 - 实现现代化的拖拽上传体验
支持文件和文件夹拖拽
"""

import tkinter as tk
from tkinter import messagebox
import tkinterdnd2 as tkdnd
import os
from typing import List, Callable, Optional

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

class DragDropMixin:
    """拖拽功能混入类"""
    
    def __init__(self, widget, callback: Callable[[List[str]], None] = None):
        self.widget = widget
        self.callback = callback
        self.drag_active = False
        
        # 设置拖拽接受
        try:
            # 尝试使用tkinterdnd2
            self.widget.drop_target_register(tkdnd.DND_FILES)
            self.widget.dnd_bind('<<DropEnter>>', self._on_drag_enter)
            self.widget.dnd_bind('<<DropPosition>>', self._on_drag_motion)
            self.widget.dnd_bind('<<DropLeave>>', self._on_drag_leave)
            self.widget.dnd_bind('<<Drop>>', self._on_drop)
            self.dnd_available = True
        except:
            # 如果tkinterdnd2不可用，使用基础的拖拽检测
            self.dnd_available = False
            self._setup_basic_drag_detection()
    
    def _setup_basic_drag_detection(self):
        """设置基础拖拽检测（无实际拖拽功能）"""
        # 绑定鼠标事件来模拟拖拽检测
        self.widget.bind('<Button-1>', self._on_click)
        self.widget.bind('<B1-Motion>', self._on_drag_motion_basic)
        self.widget.bind('<ButtonRelease-1>', self._on_release)
    
    def _on_drag_enter(self, event):
        """拖拽进入事件"""
        self.drag_active = True
        self._update_drag_visual(True)
    
    def _on_drag_motion(self, event):
        """拖拽移动事件"""
        # 可以在这里更新视觉反馈
        pass
    
    def _on_drag_leave(self, event):
        """拖拽离开事件"""
        self.drag_active = False
        self._update_drag_visual(False)
    
    def _on_drop(self, event):
        """文件放置事件"""
        self.drag_active = False
        self._update_drag_visual(False)
        
        # 获取拖拽的文件列表
        files = self._parse_drop_data(event.data)
        
        if files and self.callback:
            # 过滤出有效文件
            valid_files = []
            for file_path in files:
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    valid_files.append(file_path)
            
            if valid_files:
                self.callback(valid_files)
            else:
                messagebox.showwarning("拖拽上传", "未检测到有效的文件")
    
    def _parse_drop_data(self, data: str) -> List[str]:
        """解析拖拽数据"""
        files = []
        
        # 处理不同格式的拖拽数据
        if data.startswith('{') and data.endswith('}'):
            # Windows格式: {file1} {file2}
            data = data.strip('{}')
            files = [f.strip() for f in data.split('} {')]
        else:
            # 简单格式，用空格分隔
            files = data.split()
        
        # 清理路径
        cleaned_files = []
        for file_path in files:
            file_path = file_path.strip(' "\'')
            if file_path:
                cleaned_files.append(file_path)
        
        return cleaned_files
    
    def _update_drag_visual(self, active: bool):
        """更新拖拽视觉反馈"""
        if CTK_AVAILABLE and hasattr(self.widget, 'configure'):
            if active:
                # 拖拽激活时的样式
                self.widget.configure(border_color="#0078D7", border_width=2)
            else:
                # 恢复正常样式
                self.widget.configure(border_color="#e1e1e1", border_width=1)
        else:
            # 传统Tkinter的视觉反馈
            if active:
                self.widget.configure(relief='raised', bd=2)
            else:
                self.widget.configure(relief='flat', bd=1)
    
    def _on_click(self, event):
        """基础拖拽检测 - 点击"""
        pass
    
    def _on_drag_motion_basic(self, event):
        """基础拖拽检测 - 移动"""
        pass
    
    def _on_release(self, event):
        """基础拖拽检测 - 释放"""
        pass

class DragDropFrame:
    """拖拽上传框架组件"""
    
    def __init__(self, parent, theme_manager, callback: Callable[[List[str]], None] = None):
        self.parent = parent
        self.theme_manager = theme_manager
        self.callback = callback
        
        # 创建拖拽区域
        self._create_drop_area()
        
        # 设置拖拽功能
        self.drag_drop = DragDropMixin(self.drop_area, self._on_files_dropped)
    
    def _create_drop_area(self):
        """创建拖拽区域"""
        if CTK_AVAILABLE:
            self.drop_area = ctk.CTkFrame(
                self.parent,
                height=150,
                fg_color=self.theme_manager.get_color('secondary'),
                border_width=2,
                border_color=self.theme_manager.get_color('border'),
                corner_radius=12
            )
        else:
            self.drop_area = tk.Frame(
                self.parent,
                height=150,
                bg=self.theme_manager.get_color('secondary'),
                relief='ridge',
                bd=2
            )
        
        self.drop_area.pack_propagate(False)
        
        # 创建内容
        self._create_drop_content()
    
    def _create_drop_content(self):
        """创建拖拽区域内容"""
        if CTK_AVAILABLE:
            # 图标
            icon_label = ctk.CTkLabel(
                self.drop_area,
                text="🎯",
                font=("Segoe UI", 48),
                text_color=self.theme_manager.get_color('text_secondary')
            )
            icon_label.pack(pady=(20, 10))
            
            # 主要文本
            main_text = ctk.CTkLabel(
                self.drop_area,
                text="拖拽文件到此处",
                font=self.theme_manager.get_font('heading'),
                text_color=self.theme_manager.get_color('text_primary')
            )
            main_text.pack()
            
            # 辅助文本
            sub_text = ctk.CTkLabel(
                self.drop_area,
                text="或点击下方按钮选择文件",
                font=self.theme_manager.get_font('body'),
                text_color=self.theme_manager.get_color('text_secondary')
            )
            sub_text.pack(pady=(5, 20))
            
        else:
            # 传统Tkinter版本
            content_frame = tk.Frame(self.drop_area, bg=self.theme_manager.get_color('secondary'))
            content_frame.pack(expand=True)
            
            # 图标和文本
            icon_label = tk.Label(
                content_frame,
                text="🎯",
                font=("Segoe UI", 48),
                bg=self.theme_manager.get_color('secondary'),
                fg=self.theme_manager.get_color('text_secondary')
            )
            icon_label.pack(pady=(10, 5))
            
            main_text = tk.Label(
                content_frame,
                text="拖拽文件到此处",
                font=self.theme_manager.get_font('heading'),
                bg=self.theme_manager.get_color('secondary'),
                fg=self.theme_manager.get_color('text_primary')
            )
            main_text.pack()
            
            sub_text = tk.Label(
                content_frame,
                text="或点击下方按钮选择文件",
                font=self.theme_manager.get_font('body'),
                bg=self.theme_manager.get_color('secondary'),
                fg=self.theme_manager.get_color('text_secondary')
            )
            sub_text.pack(pady=(5, 10))
    
    def _on_files_dropped(self, files: List[str]):
        """处理文件拖拽"""
        if self.callback:
            self.callback(files)
    
    def pack(self, **kwargs):
        self.drop_area.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.drop_area.grid(**kwargs)
    
    def get_widget(self):
        return self.drop_area

class OneClickUpload:
    """一键上传组件"""
    
    def __init__(self, parent, theme_manager, callback: Callable[[], None] = None):
        self.parent = parent
        self.theme_manager = theme_manager
        self.callback = callback
        
        # 创建一键上传按钮
        self._create_upload_button()
    
    def _create_upload_button(self):
        """创建一键上传按钮"""
        if CTK_AVAILABLE:
            self.upload_button = ctk.CTkButton(
                self.parent,
                text="⚡ 一键上传",
                font=self.theme_manager.get_font('heading'),
                fg_color=self.theme_manager.get_color('primary'),
                hover_color=self.theme_manager.get_color('primary_hover'),
                height=50,
                corner_radius=25,
                command=self._on_upload_click
            )
        else:
            self.upload_button = tk.Button(
                self.parent,
                text="⚡ 一键上传",
                font=self.theme_manager.get_font('heading'),
                bg=self.theme_manager.get_color('primary'),
                fg='white',
                height=2,
                relief='flat',
                command=self._on_upload_click
            )
    
    def _on_upload_click(self):
        """一键上传点击事件"""
        if self.callback:
            self.callback()
    
    def pack(self, **kwargs):
        self.upload_button.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.upload_button.grid(**kwargs)
    
    def configure(self, **kwargs):
        self.upload_button.configure(**kwargs)

# 尝试初始化tkinterdnd2
try:
    import tkinterdnd2 as tkdnd
    
    def enable_drag_drop(root):
        """为根窗口启用拖拽功能"""
        try:
            # 如果root不是TkinterDnD实例，需要转换
            if not hasattr(root, 'tk_dnd'):
                # 创建一个新的TkinterDnD窗口
                dnd_root = tkdnd.TkinterDnD.Tk()
                dnd_root.withdraw()  # 隐藏原始窗口
                return dnd_root
            return root
        except Exception as e:
            print(f"启用拖拽功能失败: {e}")
            return root
    
    DND_AVAILABLE = True
    
except ImportError:
    def enable_drag_drop(root):
        """拖拽功能不可用时的占位函数"""
        print("tkinterdnd2不可用，拖拽功能已禁用")
        return root
    
    DND_AVAILABLE = False