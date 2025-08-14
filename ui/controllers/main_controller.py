# ui/controllers/main_controller.py
"""
主控制器 - 实现UI与业务逻辑分离的MVP架构
负责协调UI视图和业务服务层
"""

import os
import sys
import keyring
import threading
from tkinter import filedialog, messagebox
from typing import List, Dict, Any

# 导入业务服务
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.file_service import FileUploadService
from services.clipboard_service import ClipboardService
from services.smart_assistant import SmartAssistant
from config_manager import ConfigManager

class MainController:
    """主控制器 - MVP架构的Presenter层"""
    
    def __init__(self, view, main_window):
        self.view = view
        self.main_window = main_window
        
        # 业务服务初始化
        self.config_manager = ConfigManager()
        self.file_service = FileUploadService(self.config_manager)
        self.clipboard_service = ClipboardService(self.file_service)
        self.smart_assistant = SmartAssistant()
        
        # 获取加密密钥
        try:
            self.password = keyring.get_password("cloud_clipboard_service", "secret_key")
            if not self.password:
                messagebox.showerror("密钥错误", "未在系统凭据管理器中找到密钥！\n请先运行 config_setup.py 进行配置。")
                sys.exit()
        except Exception as e:
            messagebox.showerror("Keyring错误", f"无法从系统凭据管理器获取密钥: {e}")
            sys.exit()
        
        # 启动Cookie服务器
        self._start_cookie_server()
        
        # 文件管理
        self.selected_files = {}  # {file_path: file_info}
        self.upload_queue = []
        
        # 绑定事件
        self._setup_event_bindings()
        
        # 初始化视图
        self._initialize_view()
    
    def _start_cookie_server(self):
        """启动Cookie同步服务器"""
        try:
            from config_manager import run_cookie_server
            cookie_thread = threading.Thread(
                target=run_cookie_server, 
                args=(self.config_manager,), 
                daemon=True
            )
            cookie_thread.start()
            self.view.add_status_message("Cookie同步服务已启动", "success")
        except Exception as e:
            self.view.add_status_message(f"Cookie服务启动失败: {e}", "error")
    
    def _setup_event_bindings(self):
        """设置事件绑定"""
        # 绑定视图回调
        self.view.set_callback('file_select', self.on_select_files)
        self.view.set_callback('file_upload', self.on_upload_files)
        self.view.set_callback('monitor_change', self.on_monitor_settings_change)
        self.view.set_callback('drag_drop', self.on_files_dropped)
        
        # 绑定文件服务回调
        self.file_service.set_callback('progress', self.on_upload_progress)
        self.file_service.set_callback('status', self.on_upload_status)
        self.file_service.set_callback('complete', self.on_upload_complete)
        self.file_service.set_callback('error', self.on_upload_error)
        
        # 绑定剪切板服务回调
        self.clipboard_service.set_callback('text_detected', self.on_text_detected)
        self.clipboard_service.set_callback('files_detected', self.on_files_detected)
        self.clipboard_service.set_callback('error', self.on_clipboard_error)
        self.clipboard_service.set_callback('status', self.on_clipboard_status)
    
    def _initialize_view(self):
        """初始化视图状态"""
        self.view.add_status_message("现代化云内端已启动", "success")
        self.view.add_status_message("UI与业务逻辑分离架构已激活", "info")
        self.view.add_status_message("支持拖拽上传和剪切板监听", "info")
        
        # 加载配置并设置初始状态
        try:
            config = self.config_manager.load_config()
            self.view.add_status_message("配置加载成功", "success")
        except Exception as e:
            self.view.add_status_message(f"配置加载失败: {e}", "error")
    
    # === 视图事件处理器 ===
    
    def on_select_files(self):
        """处理文件选择事件"""
        try:
            file_paths = filedialog.askopenfilenames(
                title="选择要上传的文件",
                filetypes=[
                    ("所有文件", "*.*"),
                    ("文档", "*.txt *.doc *.docx *.pdf"),
                    ("图片", "*.jpg *.jpeg *.png *.gif *.bmp"),
                    ("压缩包", "*.zip *.rar *.7z")
                ]
            )
            
            if file_paths:
                self._add_files_to_list(file_paths)
                self.view.add_status_message(f"已选择 {len(file_paths)} 个文件", "info")
            
        except Exception as e:
            self.view.add_status_message(f"文件选择出错: {e}", "error")
    
    def on_upload_files(self):
        """处理文件上传事件"""
        if not self.selected_files:
            messagebox.showwarning("提示", "请先选择要上传的文件")
            return
        
        try:
            upload_count = 0
            for file_path, file_info in self.selected_files.items():
                if file_info['status'] == '待上传':
                    file_info['status'] = '队列中'
                    self.file_service.upload_file_async(file_path, self.password)
                    upload_count += 1
            
            if upload_count > 0:
                self.view.add_status_message(f"开始上传 {upload_count} 个文件", "info")
            else:
                self.view.add_status_message("没有需要上传的文件", "warning")
                
        except Exception as e:
            self.view.add_status_message(f"上传启动失败: {e}", "error")
    
    def on_monitor_settings_change(self):
        """处理监控设置变化"""
        try:
            settings = self.view.get_monitor_settings()
            text_enabled = settings.get('text_monitor', False)
            file_enabled = settings.get('file_monitor', False)
            
            self.clipboard_service.update_settings(text_enabled, file_enabled)
            
    def on_files_dropped(self, file_paths: List[str]):
        """处理拖拽文件"""
        try:
            self.view.add_status_message(f"检测到拖拽文件: {len(file_paths)}个", "info")
            self._add_files_to_list_with_analysis(file_paths)
            
        except Exception as e:
            self.view.add_status_message(f"拖拽文件处理出错: {e}", "error")
    
    def _add_files_to_list_with_analysis(self, file_paths: List[str]):
        """添加文件到列表并进行智能分析"""
        for file_path in file_paths:
            if file_path not in self.selected_files:
                try:
                    # 使用智能助手分析文件
                    analysis = self.smart_assistant.analyze_and_check_file(file_path)
                    
                    file_info = analysis['file_info']
                    is_duplicate = analysis['is_duplicate']
                    recommendation = analysis['recommendation']
                    
                    # 创建文件信息
                    file_data = {
                        'name': file_info.name,
                        'size': file_info.size,
                        'size_str': self.file_service.format_file_size(file_info.size),
                        'status': '重复文件' if is_duplicate else '待上传',
                        'valid': not is_duplicate,
                        'category': analysis['category'],
                        'hash': file_info.hash,
                        'recommendation': recommendation
                    }
                    
                    self.selected_files[file_path] = file_data
                    
                    # 添加到视图
                    status_display = file_data['status']
                    if is_duplicate:
                        status_display += " (跳过)"
                    
                    self.view.add_file_item(
                        file_info.name,
                        file_data['size_str'],
                        status_display
                    )
                    
                    # 显示分析结果
                    if is_duplicate:
                        duplicate_file = analysis['duplicate_file']
                        self.view.add_status_message(
                            f"发现重复文件: {file_info.name} (与 {os.path.basename(duplicate_file.path)} 相同)",
                            "warning"
                        )
                    else:
                        self.view.add_status_message(
                            f"文件分析: {file_info.name} - {analysis['category']} ({file_data['size_str']})",
                            "info"
                        )
                    
                    # 显示智能建议
                    if recommendation:
                        self.view.add_status_message(f"建议: {recommendation}", "info")
                    
                except Exception as e:
                    self.view.add_status_message(f"文件分析失败 {file_path}: {e}", "error")
    
    # === 文件服务回调处理器 ===
    
    def on_upload_progress(self, data: Dict[str, Any]):
        """处理上传进度更新"""
        file_name = data.get('file', '')
        percent = data.get('percent', 0)
        chunk_info = data.get('chunk', '')
        
        # 更新文件列表中的状态
        for file_path, file_info in self.selected_files.items():
            if os.path.basename(file_path) == file_name:
                if chunk_info:
                    file_info['status'] = f'上传中 {chunk_info} ({percent}%)'
                else:
                    file_info['status'] = f'上传中 ({percent}%)'
                break
        
        # 更新状态消息
        if chunk_info:
            self.view.add_status_message(f"{file_name} - {chunk_info} ({percent}%)", "info")
    
    def on_upload_status(self, data: Dict[str, Any]):
        """处理上传状态消息"""
        msg_type = data.get('type', 'info')
        message = data.get('message', '')
        
        self.view.add_status_message(message, msg_type)
    
    def on_upload_complete(self, data: Dict[str, Any]):
        """处理上传完成"""
        file_path = data.get('file_path', '')
        skipped = data.get('skipped', False)
        
        # 更新文件状态
        if file_path in self.selected_files:
            if skipped:
                self.selected_files[file_path]['status'] = '已跳过'
            else:
                self.selected_files[file_path]['status'] = '成功'
        
        file_name = os.path.basename(file_path)
        if skipped:
            self.view.add_status_message(f"{file_name} - 内容未变，已跳过", "info")
        else:
            self.view.add_status_message(f"{file_name} - 上传成功", "success")
    
    def on_upload_error(self, data: Dict[str, Any]):
        """处理上传错误"""
        message = data.get('message', '未知错误')
        self.view.add_status_message(message, "error")
    
    # === 剪切板服务回调处理器 ===
    
    def on_text_detected(self, data: Dict[str, Any]):
        """处理检测到的文本"""
        content = data.get('content', '')
        length = data.get('length', 0)
        
        self.view.add_status_message(f"检测到文本变化 (长度: {length})", "info")
        
        # 自动上传文本
        self.file_service.upload_text_async(content, self.password)
    
    def on_files_detected(self, data: Dict[str, Any]):
        """处理检测到的文件"""
        files = data.get('files', [])
        count = data.get('count', 0)
        
        self.view.add_status_message(f"检测到 {count} 个文件", "info")
        
        # 添加文件到列表并自动上传
        self._add_files_to_list(files)
        
        for file_path in files:
            self.file_service.upload_file_async(file_path, self.password)
    
    def on_clipboard_error(self, data: Dict[str, Any]):
        """处理剪切板错误"""
        message = data.get('message', '未知错误')
        self.view.add_status_message(f"剪切板错误: {message}", "warning")
    
    def on_clipboard_status(self, data: Dict[str, Any]):
        """处理剪切板状态"""
        msg_type = data.get('type', 'info')
        message = data.get('message', '')
        
        self.view.add_status_message(message, msg_type)
    
    # === 辅助方法 ===
    
    def _add_files_to_list(self, file_paths: List[str]):
        """添加文件到列表（传统方法，现在调用智能分析版本）"""
        self._add_files_to_list_with_analysis(file_paths)
    
    def clear_file_list(self):
        """清空文件列表"""
        self.selected_files.clear()
        self.view.clear_file_list()
        self.view.add_status_message("文件列表已清空", "info")
    
    def get_upload_statistics(self) -> Dict[str, int]:
        """获取上传统计"""
        stats = {
            'total': len(self.selected_files),
            'pending': 0,
            'uploading': 0,
            'completed': 0,
            'failed': 0,
            'skipped': 0,
            'duplicates': 0
        }
        
        for file_info in self.selected_files.values():
            status = file_info['status']
            if status == '待上传':
                stats['pending'] += 1
            elif '上传中' in status:
                stats['uploading'] += 1
            elif status == '成功':
                stats['completed'] += 1
            elif status == '已跳过':
                stats['skipped'] += 1
            elif '重复文件' in status:
                stats['duplicates'] += 1
            elif '错误' in status or status == '失败':
                stats['failed'] += 1
        
        return stats
    
    def show_smart_statistics(self):
        """显示智能统计信息"""
        try:
            # 获取智能助手统计
            smart_stats = self.smart_assistant.get_statistics()
            
            # 显示统计信息
            self.view.add_status_message("=== 智能分析统计 ===", "info")
            self.view.add_status_message(f"已分析文件: {smart_stats['files_analyzed']} 个", "info")
            self.view.add_status_message(f"发现重复: {smart_stats['duplicates_found']} 个", "warning")
            self.view.add_status_message(f"重复率: {smart_stats['duplicate_rate']:.1f}%", "info")
            self.view.add_status_message(f"节省空间: {smart_stats['space_saved_mb']:.1f} MB", "success")
            self.view.add_status_message(f"提供建议: {smart_stats['recommendations_given']} 次", "info")
            
        except Exception as e:
            self.view.add_status_message(f"统计信息获取失败: {e}", "error")