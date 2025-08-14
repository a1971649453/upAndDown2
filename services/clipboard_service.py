# services/clipboard_service.py
"""
剪切板监听服务 - 监控剪切板变化并触发上传
与现有的剪切板监听逻辑集成
"""

import threading
import time
import os
from typing import Callable, List, Optional

import pyperclip
import win32clipboard
import win32con

class ClipboardMonitor:
    """剪切板监听器"""
    
    def __init__(self):
        self.is_monitoring = False
        self.monitor_thread = None
        self.monitor_event = threading.Event()
        
        # 监听状态
        self.text_monitoring = False
        self.file_monitoring = False
        
        # 最近的内容缓存
        self.recent_text = ""
        self.recent_files = []
        
        # 事件回调
        self.callbacks = {
            'text_changed': None,    # 文本变化回调
            'files_changed': None,   # 文件变化回调
            'error': None           # 错误回调
        }
    
    def set_callback(self, event_type: str, callback: Callable):
        """设置事件回调"""
        if event_type in self.callbacks:
            self.callbacks[event_type] = callback
    
    def _emit_event(self, event_type: str, data):
        """触发事件回调"""
        callback = self.callbacks.get(event_type)
        if callback:
            try:
                callback(data)
            except Exception as e:
                print(f"剪切板回调执行出错 {event_type}: {e}")
    
    def start_monitoring(self, text_enabled: bool = True, files_enabled: bool = True):
        """开始监听剪切板"""
        self.text_monitoring = text_enabled
        self.file_monitoring = files_enabled
        
        if not self.text_monitoring and not self.file_monitoring:
            return False
        
        if self.is_monitoring:
            return True
        
        self.is_monitoring = True
        self.monitor_event.set()
        
        self.monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
        self.monitor_thread.start()
        
        return True
    
    def stop_monitoring(self):
        """停止监听剪切板"""
        self.is_monitoring = False
        self.monitor_event.clear()
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
    
    def update_monitoring_settings(self, text_enabled: bool, files_enabled: bool):
        """更新监听设置"""
        self.text_monitoring = text_enabled
        self.file_monitoring = files_enabled
        
        # 如果都禁用了，停止监听
        if not text_enabled and not files_enabled:
            self.stop_monitoring()
        # 如果有任何一个启用且当前未监听，启动监听
        elif (text_enabled or files_enabled) and not self.is_monitoring:
            self.start_monitoring(text_enabled, files_enabled)
    
    def _monitor_worker(self):
        """监听工作线程"""
        while self.monitor_event.is_set() and self.is_monitoring:
            try:
                # 监听文件变化
                if self.file_monitoring:
                    self._check_file_clipboard()
                
                # 监听文本变化
                if self.text_monitoring:
                    self._check_text_clipboard()
                
                # 短暂休眠避免过度占用CPU
                time.sleep(1.5)
                
            except Exception as e:
                self._emit_event('error', f"剪切板监听出错: {e}")
                time.sleep(3)  # 出错后稍长时间休眠
    
    def _check_file_clipboard(self):
        """检查文件剪切板变化"""
        try:
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                    file_paths = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                    
                    if file_paths and file_paths != self.recent_files:
                        self.recent_files = file_paths.copy()
                        
                        # 验证文件是否存在
                        valid_files = []
                        for file_path in file_paths:
                            if os.path.exists(file_path) and os.path.isfile(file_path):
                                valid_files.append(file_path)
                        
                        if valid_files:
                            self._emit_event('files_changed', valid_files)
                            
            finally:
                win32clipboard.CloseClipboard()
                
        except Exception as e:
            self._emit_event('error', f"检查文件剪切板出错: {e}")
    
    def _check_text_clipboard(self):
        """检查文本剪切板变化"""
        try:
            raw_text = pyperclip.paste()
            normalized_text = raw_text.strip()
            
            if normalized_text and normalized_text != self.recent_text:
                self.recent_text = normalized_text
                
                # 过滤掉过短的文本（可能是意外复制）
                if len(normalized_text) >= 3:
                    self._emit_event('text_changed', normalized_text)
                    
        except Exception as e:
            self._emit_event('error', f"检查文本剪切板出错: {e}")
    
    def get_current_text(self) -> Optional[str]:
        """获取当前剪切板文本"""
        try:
            return pyperclip.paste()
        except Exception:
            return None
    
    def get_current_files(self) -> List[str]:
        """获取当前剪切板文件列表"""
        try:
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                    return win32clipboard.GetClipboardData(win32con.CF_HDROP)
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            pass
        return []

class ClipboardService:
    """剪切板服务 - 高级封装"""
    
    def __init__(self, file_service=None):
        self.file_service = file_service
        self.monitor = ClipboardMonitor()
        
        # 设置监听器回调
        self.monitor.set_callback('text_changed', self._on_text_changed)
        self.monitor.set_callback('files_changed', self._on_files_changed)
        self.monitor.set_callback('error', self._on_monitor_error)
        
        # 外部回调
        self.callbacks = {
            'text_detected': None,
            'files_detected': None,
            'error': None,
            'status': None
        }
    
    def set_callback(self, event_type: str, callback: Callable):
        """设置事件回调"""
        if event_type in self.callbacks:
            self.callbacks[event_type] = callback
    
    def _emit_event(self, event_type: str, data):
        """触发事件回调"""
        callback = self.callbacks.get(event_type)
        if callback:
            try:
                callback(data)
            except Exception as e:
                print(f"剪切板服务回调出错 {event_type}: {e}")
    
    def _on_text_changed(self, text_content: str):
        """文本变化处理"""
        self._emit_event('text_detected', {
            'content': text_content,
            'length': len(text_content),
            'timestamp': time.time()
        })
        
        self._emit_event('status', {
            'type': 'info',
            'message': f'检测到文本变化 (长度: {len(text_content)})'
        })
    
    def _on_files_changed(self, file_paths: List[str]):
        """文件变化处理"""
        self._emit_event('files_detected', {
            'files': file_paths,
            'count': len(file_paths),
            'timestamp': time.time()
        })
        
        self._emit_event('status', {
            'type': 'info',
            'message': f'检测到 {len(file_paths)} 个文件'
        })
    
    def _on_monitor_error(self, error_message: str):
        """监听错误处理"""
        self._emit_event('error', {'message': f'剪切板监听错误: {error_message}'})
    
    def start_monitoring(self, text_enabled: bool = True, files_enabled: bool = True):
        """开始监听"""
        success = self.monitor.start_monitoring(text_enabled, files_enabled)
        
        if success:
            monitor_types = []
            if text_enabled:
                monitor_types.append("文本")
            if files_enabled:
                monitor_types.append("文件")
            
            self._emit_event('status', {
                'type': 'success',
                'message': f'开始监听剪切板: {", ".join(monitor_types)}'
            })
        
        return success
    
    def stop_monitoring(self):
        """停止监听"""
        self.monitor.stop_monitoring()
        
        self._emit_event('status', {
            'type': 'warning',
            'message': '剪切板监听已停止'
        })
    
    def update_settings(self, text_enabled: bool, files_enabled: bool):
        """更新监听设置"""
        self.monitor.update_monitoring_settings(text_enabled, files_enabled)
        
        status_msg = "监听设置已更新: "
        if text_enabled and files_enabled:
            status_msg += "文本+文件"
        elif text_enabled:
            status_msg += "仅文本"
        elif files_enabled:
            status_msg += "仅文件"
        else:
            status_msg += "已禁用"
        
        self._emit_event('status', {
            'type': 'info',
            'message': status_msg
        })
    
    def is_monitoring(self) -> bool:
        """检查是否正在监听"""
        return self.monitor.is_monitoring