# test_responsive_layout.py
"""
测试响应式布局功能 - 验证多分辨率适配
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import ModernMainWindow
from ui.components.card_components import FileUploadCard, StatusCard
from ui.layouts.responsive_layout import ResponsiveContainer

def test_responsive_layout():
    """测试响应式布局的功能"""
    
    # 创建主窗口
    main_window = ModernMainWindow("响应式布局测试", "v5.0-responsive")
    root = main_window.show()
    
    # 获取内容区域和布局管理器
    content_area = main_window.get_content_area()
    layout_manager = main_window.get_layout_manager()
    
    try:
        # 创建响应式容器
        responsive_container = ResponsiveContainer(
            content_area, 
            layout_manager, 
            layout_mode='auto'
        )
        responsive_container.pack(fill='both', expand=True, padx=8, pady=8)
        
        # 获取容器widget
        container_widget = responsive_container.get_container()
        
        # 添加多个卡片组件测试响应式布局
        cards = []
        
        # 创建文件上传卡片
        upload_card = FileUploadCard(container_widget, main_window.theme_manager)
        cards.append(upload_card)
        responsive_container.add_widget(upload_card)
        
        # 创建状态卡片
        status_card = StatusCard(container_widget, main_window.theme_manager, title="📊 布局测试")
        cards.append(status_card)
        responsive_container.add_widget(status_card)
        
        # 添加测试消息
        status_card.add_status_item("响应式布局系统已初始化", "success")
        status_card.add_status_item("支持1280x720到4K分辨率", "info")
        status_card.add_status_item("自动适配屏幕断点", "info")
        
        # 显示当前断点信息
        current_bp = layout_manager.get_current_breakpoint()
        window_size = f"{root.winfo_width()}x{root.winfo_height()}"
        status_card.add_status_item(f"当前断点: {current_bp}", "info")
        status_card.add_status_item(f"窗口大小: {window_size}", "info")
        
        # 注册布局变化回调
        def on_layout_change(breakpoint):
            status_card.add_status_item(f"布局变化: {breakpoint}", "warning")
            main_window.update_breakpoint_display()
        
        layout_manager.register_layout_callback(on_layout_change)
        
        # 设置测试按钮
        upload_card.set_select_command(
            lambda: status_card.add_status_item("选择文件功能测试", "info")
        )
        upload_card.set_upload_command(
            lambda: status_card.add_status_item("上传功能测试", "success")
        )
        
        main_window.update_status("响应式布局测试就绪 - 请调整窗口大小测试")
        
        # 提示用户测试响应式功能
        def show_test_instructions():
            instructions = (
                "响应式布局测试说明：\n\n"
                "1. 调整窗口大小观察布局变化\n"
                "2. 尝试不同的分辨率断点\n"
                "3. 观察状态栏中的断点信息\n"
                "4. 查看活动日志中的布局变化记录\n\n"
                "断点说明：\n"
                "xs: <768px, sm: 768-1024px\n"
                "md: 1024-1280px, lg: 1280-1920px\n"
                "xl: 1920-2560px, xxl: >2560px"
            )
            status_card.add_status_item("测试说明已显示", "info")
            main_window.update_status(instructions.replace('\n', ' | '))
        
        # 延迟显示说明
        root.after(1000, show_test_instructions)
        
    except Exception as e:
        main_window.update_status(f"响应式布局测试出错: {e}")
        print(f"响应式布局测试错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 设置关闭回调
    def on_closing():
        print("关闭响应式布局测试窗口")
        root.destroy()
    
    main_window.set_close_callback(on_closing)
    
    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    print("开始响应式布局测试...")
    test_responsive_layout()
    print("响应式布局测试结束")