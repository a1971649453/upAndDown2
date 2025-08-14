# test_card_components.py
"""
测试卡片组件库 - 验证LocalSend风格的卡片设计
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import ModernMainWindow
from ui.components.card_components import FileUploadCard, StatusCard, SettingsCard

def test_card_components():
    """测试卡片组件的功能"""
    
    # 创建主窗口
    main_window = ModernMainWindow("卡片组件测试", "v5.0-cards")
    root = main_window.show()
    
    # 获取内容区域
    content_area = main_window.get_content_area()
    
    try:
        # 创建左右分栏布局
        if main_window.theme_manager.is_customtkinter_available():
            import customtkinter as ctk
            
            # 创建左右分栏
            left_frame = ctk.CTkFrame(content_area, fg_color="transparent")
            left_frame.pack(side='left', fill='both', expand=True, padx=(8, 4), pady=8)
            
            right_frame = ctk.CTkFrame(content_area, fg_color="transparent")
            right_frame.pack(side='right', fill='both', expand=True, padx=(4, 8), pady=8)
            
        else:
            import tkinter as tk
            
            left_frame = tk.Frame(content_area, bg=main_window.theme_manager.get_color('background'))
            left_frame.pack(side='left', fill='both', expand=True, padx=(8, 4), pady=8)
            
            right_frame = tk.Frame(content_area, bg=main_window.theme_manager.get_color('background'))
            right_frame.pack(side='right', fill='both', expand=True, padx=(4, 8), pady=8)
        
        # 创建文件上传卡片
        upload_card = FileUploadCard(left_frame, main_window.theme_manager)
        upload_card.pack(fill='x', pady=(0, 8))
        
        # 设置卡片命令
        upload_card.set_select_command(lambda: main_window.update_status("选择文件按钮已点击"))
        upload_card.set_upload_command(lambda: main_window.update_status("上传按钮已点击"))
        
        # 创建设置卡片
        settings_card = SettingsCard(left_frame, main_window.theme_manager)
        settings_card.pack(fill='x', pady=(0, 8))
        
        # 创建状态卡片
        status_card = StatusCard(right_frame, main_window.theme_manager, title="📊 活动日志")
        status_card.pack(fill='both', expand=True)
        
        # 添加一些测试状态消息
        status_card.add_status_item("UI组件库初始化完成", "success")
        status_card.add_status_item("正在测试卡片组件", "info")
        status_card.add_status_item("LocalSend风格设计已应用", "success")
        status_card.add_status_item("主题系统运行正常", "info")
        
        # 检测并显示当前UI框架
        framework_name = "CustomTkinter" if main_window.theme_manager.is_customtkinter_available() else "传统Tkinter"
        status_card.add_status_item(f"当前UI框架: {framework_name}", "info")
        
        main_window.update_status("卡片组件测试完成")
        
    except Exception as e:
        main_window.update_status(f"组件测试出错: {e}")
        print(f"卡片组件测试错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 设置关闭回调
    def on_closing():
        print("关闭卡片组件测试窗口")
        root.destroy()
    
    main_window.set_close_callback(on_closing)
    
    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    print("开始卡片组件测试...")
    test_card_components()
    print("卡片组件测试结束")