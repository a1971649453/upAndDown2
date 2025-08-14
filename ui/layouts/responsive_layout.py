# ui/layouts/responsive_layout.py
"""
响应式布局管理器 - 支持多分辨率自适应
实现1280x720到4K分辨率的响应式设计
"""

import tkinter as tk
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

class ResponsiveLayoutManager:
    """响应式布局管理器"""
    
    # 断点定义
    BREAKPOINTS = {
        'xs': 0,     # 超小屏幕
        'sm': 768,   # 小屏幕
        'md': 1024,  # 中等屏幕
        'lg': 1280,  # 大屏幕
        'xl': 1920,  # 超大屏幕
        'xxl': 2560  # 4K屏幕
    }
    
    # 响应式间距
    RESPONSIVE_SPACING = {
        'xs': {'padding': 8, 'margin': 4},
        'sm': {'padding': 12, 'margin': 6},
        'md': {'padding': 16, 'margin': 8},
        'lg': {'padding': 20, 'margin': 10},
        'xl': {'padding': 24, 'margin': 12},
        'xxl': {'padding': 32, 'margin': 16}
    }
    
    # 响应式字体大小
    RESPONSIVE_FONTS = {
        'xs': {'title': 14, 'heading': 12, 'body': 9, 'caption': 8},
        'sm': {'title': 16, 'heading': 14, 'body': 10, 'caption': 9},
        'md': {'title': 18, 'heading': 15, 'body': 11, 'caption': 10},
        'lg': {'title': 20, 'heading': 16, 'body': 12, 'caption': 11},
        'xl': {'title': 22, 'heading': 18, 'body': 13, 'caption': 12},
        'xxl': {'title': 28, 'heading': 22, 'body': 16, 'caption': 14}
    }
    
    def __init__(self, root_window):
        self.root = root_window
        self.current_breakpoint = 'md'
        self.layout_callbacks = []
        
        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self._on_window_resize)
        
        # 初始计算断点
        self._update_breakpoint()
    
    def _on_window_resize(self, event):
        """窗口大小变化事件处理"""
        # 只处理根窗口的resize事件
        if event.widget == self.root:
            self._update_breakpoint()
    
    def _update_breakpoint(self):
        """更新当前断点"""
        window_width = self.root.winfo_width()
        old_breakpoint = self.current_breakpoint
        
        # 确定当前断点
        for breakpoint, min_width in reversed(list(self.BREAKPOINTS.items())):
            if window_width >= min_width:
                self.current_breakpoint = breakpoint
                break
        
        # 如果断点发生变化，触发布局更新
        if old_breakpoint != self.current_breakpoint:
            self._trigger_layout_update()
    
    def _trigger_layout_update(self):
        """触发布局更新回调"""
        for callback in self.layout_callbacks:
            try:
                callback(self.current_breakpoint)
            except Exception as e:
                print(f"布局更新回调出错: {e}")
    
    def register_layout_callback(self, callback):
        """注册布局更新回调"""
        self.layout_callbacks.append(callback)
    
    def get_current_breakpoint(self):
        """获取当前断点"""
        return self.current_breakpoint
    
    def get_responsive_spacing(self, breakpoint=None):
        """获取响应式间距"""
        bp = breakpoint or self.current_breakpoint
        return self.RESPONSIVE_SPACING.get(bp, self.RESPONSIVE_SPACING['md'])
    
    def get_responsive_fonts(self, breakpoint=None):
        """获取响应式字体大小"""
        bp = breakpoint or self.current_breakpoint
        return self.RESPONSIVE_FONTS.get(bp, self.RESPONSIVE_FONTS['md'])
    
    def get_responsive_columns(self, breakpoint=None):
        """获取响应式列数"""
        bp = breakpoint or self.current_breakpoint
        column_map = {
            'xs': 1,
            'sm': 1, 
            'md': 2,
            'lg': 2,
            'xl': 3,
            'xxl': 3
        }
        return column_map.get(bp, 2)
    
    def is_mobile(self):
        """判断是否为移动端布局"""
        return self.current_breakpoint in ['xs', 'sm']
    
    def is_desktop(self):
        """判断是否为桌面端布局"""
        return self.current_breakpoint in ['lg', 'xl', 'xxl']

class ResponsiveContainer:
    """响应式容器组件"""
    
    def __init__(self, parent, layout_manager: ResponsiveLayoutManager, 
                 layout_mode='auto', **kwargs):
        self.parent = parent
        self.layout_manager = layout_manager
        self.layout_mode = layout_mode
        self.child_widgets = []
        
        # 创建容器
        if CTK_AVAILABLE:
            self.container = ctk.CTkFrame(parent, **kwargs)
        else:
            self.container = tk.Frame(parent, **kwargs)
        
        # 注册布局更新回调
        self.layout_manager.register_layout_callback(self._on_layout_change)
        
        # 初始布局
        self._update_layout()
    
    def _on_layout_change(self, breakpoint):
        """断点变化时的布局更新"""
        self._update_layout()
    
    def _update_layout(self):
        """更新布局"""
        current_bp = self.layout_manager.get_current_breakpoint()
        spacing = self.layout_manager.get_responsive_spacing()
        
        # 根据布局模式调整
        if self.layout_mode == 'grid':
            self._update_grid_layout(current_bp, spacing)
        elif self.layout_mode == 'flex':
            self._update_flex_layout(current_bp, spacing)
        else:
            self._update_auto_layout(current_bp, spacing)
    
    def _update_grid_layout(self, breakpoint, spacing):
        """更新网格布局"""
        columns = self.layout_manager.get_responsive_columns()
        
        # 重新排列子组件
        for i, widget in enumerate(self.child_widgets):
            row = i // columns
            col = i % columns
            widget.grid(row=row, column=col, 
                       padx=spacing['margin'], 
                       pady=spacing['margin'],
                       sticky='nsew')
        
        # 配置网格权重
        for i in range(columns):
            self.container.grid_columnconfigure(i, weight=1)
    
    def _update_flex_layout(self, breakpoint, spacing):
        """更新弹性布局"""
        # 根据断点决定排列方向
        if self.layout_manager.is_mobile():
            # 移动端垂直排列
            for widget in self.child_widgets:
                widget.pack(fill='x', padx=spacing['padding'], 
                           pady=spacing['margin'])
        else:
            # 桌面端水平排列
            for widget in self.child_widgets:
                widget.pack(side='left', fill='both', expand=True,
                           padx=spacing['margin'], pady=spacing['padding'])
    
    def _update_auto_layout(self, breakpoint, spacing):
        """自动布局模式"""
        # 根据屏幕尺寸自动选择最适合的布局
        if self.layout_manager.is_mobile():
            self._update_flex_layout(breakpoint, spacing)
        else:
            self._update_grid_layout(breakpoint, spacing)
    
    def add_widget(self, widget):
        """添加子组件"""
        self.child_widgets.append(widget)
        self._update_layout()
    
    def remove_widget(self, widget):
        """移除子组件"""
        if widget in self.child_widgets:
            self.child_widgets.remove(widget)
            self._update_layout()
    
    def pack(self, **kwargs):
        self.container.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.container.grid(**kwargs)
    
    def get_container(self):
        return self.container

class AdaptiveThemeManager:
    """自适应主题管理器 - 扩展原有主题管理器"""
    
    def __init__(self, base_theme_manager, layout_manager: ResponsiveLayoutManager):
        self.base_theme = base_theme_manager
        self.layout_manager = layout_manager
        
        # 注册布局变化回调
        self.layout_manager.register_layout_callback(self._on_layout_change)
    
    def _on_layout_change(self, breakpoint):
        """断点变化时更新主题"""
        # 这里可以根据屏幕尺寸调整主题参数
        pass
    
    def get_responsive_font(self, font_type):
        """获取响应式字体"""
        responsive_fonts = self.layout_manager.get_responsive_fonts()
        base_font = self.base_theme.get_font(font_type)
        
        # 更新字体大小
        font_family, _, *style = base_font
        new_size = responsive_fonts.get(font_type, base_font[1])
        
        if style:
            return (font_family, new_size, *style)
        else:
            return (font_family, new_size)
    
    def get_responsive_spacing(self, spacing_type):
        """获取响应式间距"""
        responsive_spacing = self.layout_manager.get_responsive_spacing()
        base_spacing = self.base_theme.get_spacing(spacing_type)
        
        # 根据断点调整间距
        multiplier = {
            'xs': 0.75,
            'sm': 0.9,
            'md': 1.0,
            'lg': 1.1,
            'xl': 1.25,
            'xxl': 1.5
        }
        
        current_bp = self.layout_manager.get_current_breakpoint()
        return int(base_spacing * multiplier.get(current_bp, 1.0))
    
    def __getattr__(self, name):
        """委托其他方法到基础主题管理器"""
        return getattr(self.base_theme, name)