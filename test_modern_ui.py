# test_modern_ui.py
"""
测试现代化UI框架和fallback机制
验证CustomTkinter集成和向后兼容性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import ModernMainWindow
from ui.components.base_components import ModernFrame, ModernButton, ModernLabel

def test_ui_framework():
    """测试UI框架的基本功能"""
    
    # 创建主窗口
    main_window = ModernMainWindow("测试现代化UI", "v5.0-test")
    root = main_window.show()
    
    # 获取内容区域
    content_area = main_window.get_content_area()
    
    # 测试组件创建
    try:
        # 创建测试卡片
        test_frame = ModernFrame(content_area, main_window.theme_manager, card_style=True)
        test_frame.pack(fill='x', padx=16, pady=8)
        
        # 添加标题
        title_label = ModernLabel(
            test_frame.get_widget(), 
            "UI框架测试", 
            main_window.theme_manager, 
            text_style='heading'
        )
        title_label.pack(pady=8)
        
        # 添加测试按钮
        primary_btn = ModernButton(
            test_frame.get_widget(),
            "主要按钮",
            command=lambda: main_window.update_status("主要按钮已点击"),
            theme_manager=main_window.theme_manager,
            style='primary'
        )
        primary_btn.pack(pady=4)
        
        secondary_btn = ModernButton(
            test_frame.get_widget(),
            "次要按钮", 
            command=lambda: main_window.update_status("次要按钮已点击"),
            theme_manager=main_window.theme_manager,
            style='secondary'
        )
        secondary_btn.pack(pady=4)
        
        # 检测使用的UI框架
        framework_name = "CustomTkinter" if main_window.theme_manager.is_customtkinter_available() else "传统Tkinter (兼容模式)"
        
        framework_label = ModernLabel(
            test_frame.get_widget(),
            f"当前使用: {framework_name}",
            main_window.theme_manager,
            text_style='caption'
        )
        framework_label.pack(pady=8)
        
        main_window.update_status(f"UI框架测试完成 - {framework_name}")
        
    except Exception as e:
        main_window.update_status(f"测试出错: {e}")
        print(f"UI测试错误: {e}")
    
    # 设置关闭回调
    def on_closing():
        print("关闭UI测试窗口")
        root.destroy()
    
    main_window.set_close_callback(on_closing)
    
    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    print("开始UI框架测试...")
    test_ui_framework()
    print("UI框架测试结束")