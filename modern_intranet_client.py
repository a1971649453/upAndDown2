# modern_intranet_client.py
"""
现代化云内端客户端 - v5.0
UI与业务逻辑分离的现代化架构
支持CustomTkinter、响应式布局、异步处理
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入现代化UI组件
from ui.main_window import ModernMainWindow
from ui.views.main_view import MainView
from ui.controllers.main_controller import MainController

# 导入核心系统
from core.event_system import EventManager, StateManager, AsyncTaskManager, EventType
from core.performance_monitor import ApplicationHealthMonitor

class ModernIntranetApp:
    """现代化云内端应用程序"""
    
    def __init__(self):
        # 检查配置文件
        self._check_config()
        
        # 初始化核心系统
        self.event_manager = EventManager()
        self.state_manager = StateManager(self.event_manager)
        self.task_manager = AsyncTaskManager(self.event_manager)
        self.health_monitor = ApplicationHealthMonitor()
        
        # 初始化UI
        self.main_window = None
        self.main_view = None
        self.main_controller = None
        
        # 应用状态
        self.running = False
    
    def _check_config(self):
        """检查必要的配置文件"""
        if not os.path.exists('config.ini'):
            messagebox.showerror(
                "配置错误", 
                "未找到 config.ini 文件！\n请先运行 config_setup.py 进行配置。"
            )
            sys.exit(1)
    
    def initialize(self):
        """初始化应用程序"""
        try:
            # 启动任务管理器
            self.task_manager.start()
            
            # 启动健康监控
            self.health_monitor.start()
            
            # 发布应用启动事件
            self.event_manager.publish(EventType.APP_STARTED, {
                'version': 'v5.0',
                'architecture': 'Modern MVP'
            })
            
            # 创建主窗口
            self.main_window = ModernMainWindow(
                title="现代化云内端", 
                version="v5.0"
            )
            
            # 获取主窗口实例
            root = self.main_window.show()
            
            # 创建主视图
            content_area = self.main_window.get_content_area()
            layout_manager = self.main_window.get_layout_manager()
            theme_manager = self.main_window.get_adaptive_theme()
            
            self.main_view = MainView(content_area, theme_manager, layout_manager)
            
            # 创建主控制器（连接视图和业务逻辑）
            self.main_controller = MainController(self.main_view, self.main_window)
            
            # 设置关闭回调
            self.main_window.set_close_callback(self._on_closing)
            
            # 初始化应用状态
            self._initialize_app_state()
            
            self.running = True
            return root
            
        except Exception as e:
            messagebox.showerror("初始化错误", f"应用程序初始化失败：\n{e}")
            sys.exit(1)
    
    def _initialize_app_state(self):
        """初始化应用状态"""
        self.state_manager.set_state('app_version', 'v5.0')
        self.state_manager.set_state('ui_framework', 'CustomTkinter' if hasattr(self.main_window.theme_manager, 'ctk_available') and self.main_window.theme_manager.ctk_available else 'Tkinter')
        self.state_manager.set_state('architecture', 'MVP')
        self.state_manager.set_state('files_selected', 0)
        self.state_manager.set_state('upload_active', False)
        self.state_manager.set_state('monitoring_active', False)
        
        # 订阅状态变化
        self.state_manager.subscribe_state_change('files_selected', self._on_files_count_changed)
        self.state_manager.subscribe_state_change('upload_active', self._on_upload_status_changed)
    
    def _on_files_count_changed(self, key: str, new_value: int, old_value: int):
        """文件数量变化处理"""
        if self.main_window:
            if new_value > 0:
                self.main_window.update_status(f"已选择 {new_value} 个文件")
            else:
                self.main_window.update_status("就绪")
    
    def _on_upload_status_changed(self, key: str, new_value: bool, old_value: bool):
        """上传状态变化处理"""
        if self.main_window:
            if new_value:
                self.main_window.update_status("正在上传文件...")
            else:
                self.main_window.update_status("上传完成")
    
    def _on_closing(self):
        """应用关闭处理"""
        if messagebox.askokcancel("退出", "确定要退出现代化云内端吗？"):
            try:
                # 发布应用关闭事件
                self.event_manager.publish(EventType.APP_CLOSING, {
                    'graceful': True
                })
                
                # 停止各种服务
                if hasattr(self.main_controller, 'clipboard_service'):
                    self.main_controller.clipboard_service.stop_monitoring()
                
                # 停止健康监控
                self.health_monitor.stop()
                
                # 停止任务管理器
                self.task_manager.stop()
                
                # 停止事件管理器
                self.event_manager.stop_processing()
                
                self.running = False
                
                # 销毁窗口
                if self.main_window:
                    self.main_window.get_root().destroy()
                    
            except Exception as e:
                print(f"应用关闭时出错: {e}")
                # 强制关闭
                if self.main_window:
                    self.main_window.get_root().destroy()
    
    def run(self):
        """运行应用程序"""
        try:
            # 初始化应用
            root = self.initialize()
            
            # 显示启动消息
            self.main_view.add_status_message("现代化云内端已启动", "success")
            self.main_view.add_status_message("MVP架构 | 事件驱动 | 异步处理", "info")
            
            framework = self.state_manager.get_state('ui_framework')
            self.main_view.add_status_message(f"UI框架: {framework}", "info")
            
            # 显示性能监控信息
            def show_performance_info():
                health_report = self.health_monitor.get_health_report()
                status = health_report['overall_status']
                status_icon = {'healthy': '✅', 'degraded': '⚠️', 'critical': '❌'}.get(status, '❓')
                self.main_view.add_status_message(f"系统健康: {status_icon} {status}", "info")
                
                perf = health_report['performance'].get('latest')
                if perf:
                    self.main_view.add_status_message(
                        f"性能指标: CPU {perf['cpu_percent']:.1f}% | 内存 {perf['memory_mb']:.1f}MB",
                        "info"
                    )
            
            # 延迟显示性能信息
            root.after(2000, show_performance_info)
            
            # 启动主事件循环
            root.mainloop()
            
        except KeyboardInterrupt:
            print("用户中断程序")
        except Exception as e:
            print(f"应用运行时出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 确保清理资源
            if self.running:
                self._cleanup()
    
    def _cleanup(self):
        """清理资源"""
        try:
            if self.task_manager:
                self.task_manager.stop()
            
            if self.event_manager:
                self.event_manager.stop_processing()
                
        except Exception as e:
            print(f"资源清理时出错: {e}")

def main():
    """主函数"""
    print("=== 现代化云内端 v5.0 ===")
    print("架构: MVP | UI框架: CustomTkinter + Fallback")
    print("特性: 响应式布局 | 异步处理 | 事件驱动")
    print("=" * 40)
    
    try:
        app = ModernIntranetApp()
        app.run()
    except Exception as e:
        print(f"应用启动失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("应用已退出")

if __name__ == "__main__":
    main()