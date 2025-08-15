# services/file_service.py
"""
文件服务层 - 封装文件上传相关的业务逻辑
与现有的network_utils.py集成，实现UI与业务逻辑分离
"""

import os
import hashlib
import threading
import queue
import time
import math
import base64
import urllib.parse
from collections import deque
from typing import Callable, Optional, Dict, Any

# 导入现有的核心功能
from network_utils import get_encryption_key, upload_data, create_and_encrypt_payload
from config_manager import ConfigManager

class FileUploadService:
    """文件上传服务 - 业务逻辑层"""
    
    def __init__(self, config_manager: ConfigManager = None):
        self.config_manager = config_manager or ConfigManager()
        
        # 从配置加载参数
        config = self.config_manager.load_config()
        self.max_file_size_mb = int(config['DEFAULT'].get('max_file_size_mb', 50))
        self.chunk_size_mb = int(config['DEFAULT'].get('chunk_size_mb', 45))
        self.max_file_size_bytes = self.max_file_size_mb * 1024 * 1024
        self.chunk_size_bytes = self.chunk_size_mb * 1024 * 1024
        
        # 上传缓存
        self.upload_cache = deque(maxlen=20)
        
        # 事件回调
        self.callbacks = {
            'progress': None,          # 进度更新回调
            'status': None,            # 状态消息回调
            'complete': None,          # 完成回调
            'error': None              # 错误回调
        }
    
    def set_callback(self, event_type: str, callback: Callable):
        """设置事件回调"""
        if event_type in self.callbacks:
            self.callbacks[event_type] = callback
    
    def _emit_event(self, event_type: str, data: Any):
        """触发事件回调"""
        callback = self.callbacks.get(event_type)
        if callback:
            try:
                callback(data)
            except Exception as e:
                print(f"回调执行出错 {event_type}: {e}")
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """计算文件哈希值 - 使用流式处理避免内存问题"""
        try:
            self._emit_event('status', {'type': 'info', 'message': f'正在计算文件哈希: {os.path.basename(file_path)}'})
            
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            
            return sha256_hash.hexdigest()
        except Exception as e:
            self._emit_event('error', {'message': f'计算文件哈希失败: {e}'})
            return None
    
    def _is_file_cached(self, file_hash: str) -> bool:
        """检查文件是否已在缓存中"""
        return file_hash in self.upload_cache
    
    def _add_to_cache(self, file_hash: str):
        """添加文件哈希到缓存"""
        self.upload_cache.append(file_hash)
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """验证文件是否符合上传要求"""
        result = {
            'valid': False,
            'reason': '',
            'file_size': 0,
            'file_name': ''
        }
        
        try:
            if not os.path.exists(file_path):
                result['reason'] = '文件不存在'
                return result
            
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            result['file_size'] = file_size
            result['file_name'] = file_name
            
            if file_size > self.max_file_size_bytes:
                result['reason'] = f'文件大小超过限制({self.max_file_size_mb}MB)'
                return result
            
            if file_size == 0:
                result['reason'] = '文件为空'
                return result
            
            result['valid'] = True
            return result
            
        except Exception as e:
            result['reason'] = f'文件验证出错: {e}'
            return result
    
    def format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小显示"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / 1024 ** 2:.1f} MB"
    
    def upload_file_async(self, file_path: str, password: str) -> bool:
        """异步上传文件"""
        def upload_worker():
            try:
                # 验证文件
                validation = self.validate_file(file_path)
                if not validation['valid']:
                    self._emit_event('error', {'message': validation['reason']})
                    return False
                
                file_name = validation['file_name']
                file_size = validation['file_size']
                
                self._emit_event('status', {
                    'type': 'info',
                    'message': f'开始处理文件: {file_name} ({self.format_file_size(file_size)})'
                })
                
                # 计算文件哈希
                file_hash = self._calculate_file_hash(file_path)
                if not file_hash:
                    return False
                
                # 检查缓存
                if self._is_file_cached(file_hash):
                    self._emit_event('status', {
                        'type': 'info',
                        'message': f'文件 {file_name} 内容未变，跳过上传'
                    })
                    self._emit_event('complete', {
                        'file_path': file_path,
                        'skipped': True,
                        'reason': '内容未变'
                    })
                    return True
                
                # 决定上传方式
                if file_size > self.chunk_size_bytes:
                    success = self._upload_file_chunks(file_path, file_name, file_size, password)
                else:
                    success = self._upload_file_single(file_path, file_name, password)
                
                if success:
                    self._add_to_cache(file_hash)
                    self._emit_event('complete', {
                        'file_path': file_path,
                        'skipped': False,
                        'file_size': file_size
                    })
                
                return success
                
            except Exception as e:
                self._emit_event('error', {'message': f'上传过程出错: {e}'})
                return False
        
        # 在后台线程执行上传
        upload_thread = threading.Thread(target=upload_worker, daemon=True)
        upload_thread.start()
        return True
    
    def _upload_file_single(self, file_path: str, file_name: str, password: str) -> bool:
        """单文件上传"""
        try:
            self._emit_event('status', {'type': 'info', 'message': f'正在上传: {file_name}'})
            self._emit_event('progress', {'file': file_name, 'percent': 0})
            
            # 读取文件内容
            with open(file_path, 'rb') as f:
                data_bytes = f.read()
            
            # 创建加密载荷
            key = get_encryption_key(password)
            from cryptography.fernet import Fernet
            import json
            fernet = Fernet(key)
            
            payload = {
                "filename": file_name,
                "content_base64": base64.b64encode(data_bytes).decode('utf-8'),
                "is_from_text": False
            }
            encrypted_payload = fernet.encrypt(json.dumps(payload).encode('utf-8'))
            
            # 使用现有的上传函数
            config = self.config_manager.get_config()
            status_queue = queue.Queue()
            
            self._emit_event('progress', {'file': file_name, 'percent': 50})
            
            success = upload_data(encrypted_payload, config, status_queue)
            
            # 处理状态队列中的消息
            while not status_queue.empty():
                try:
                    msg_type, message = status_queue.get_nowait()
                    self._emit_event('status', {'type': msg_type, 'message': message})
                except queue.Empty:
                    break
            
            if success:
                self._emit_event('progress', {'file': file_name, 'percent': 100})
                self._emit_event('status', {'type': 'success', 'message': f'文件 {file_name} 上传成功'})
            else:
                self._emit_event('status', {'type': 'error', 'message': f'文件 {file_name} 上传失败'})
            
            return success
            
        except Exception as e:
            self._emit_event('error', {'message': f'单文件上传出错: {e}'})
            return False
    
    def _upload_file_chunks(self, file_path: str, file_name: str, file_size: int, password: str) -> bool:
        """分片上传大文件"""
        try:
            self._emit_event('status', {'type': 'info', 'message': f'启动分片上传: {file_name}'})
            
            encoded_filename = urllib.parse.quote(file_name)
            upload_id = f"{int(time.time())}-{base64.urlsafe_b64encode(os.urandom(4)).decode()}"
            total_chunks = math.ceil(file_size / self.chunk_size_bytes)
            
            config = self.config_manager.get_config()
            
            with open(file_path, 'rb') as f:
                for i in range(total_chunks):
                    chunk_data = f.read(self.chunk_size_bytes)
                    if not chunk_data:
                        break
                    
                    chunk_index = i + 1
                    progress_percent = int((chunk_index / total_chunks) * 100)
                    
                    self._emit_event('progress', {
                        'file': file_name,
                        'percent': progress_percent,
                        'chunk': f'{chunk_index}/{total_chunks}'
                    })
                    
                    self._emit_event('status', {
                        'type': 'info',
                        'message': f'{file_name} - 分片 {chunk_index}/{total_chunks}'
                    })
                    
                    # 创建分片的加密载荷
                    key = get_encryption_key(password)
                    from cryptography.fernet import Fernet
                    import json
                    fernet = Fernet(key)
                    
                    payload = {
                        "filename": file_name,
                        "content_base64": base64.b64encode(chunk_data).decode('utf-8'),
                        "is_from_text": False
                    }
                    encrypted_payload = fernet.encrypt(json.dumps(payload).encode('utf-8'))
                    
                    # 分片文件名
                    chunk_filename = f"chunk_{upload_id}_{chunk_index:03d}_{total_chunks:03d}_{encoded_filename}.encrypted"
                    
                    # 上传分片
                    status_queue = queue.Queue()
                    success = upload_data(encrypted_payload, config, status_queue, custom_filename=chunk_filename)
                    
                    # 处理状态消息
                    while not status_queue.empty():
                        try:
                            msg_type, message = status_queue.get_nowait()
                            self._emit_event('status', {'type': msg_type, 'message': message})
                        except queue.Empty:
                            break
                    
                    if not success:
                        self._emit_event('error', {'message': f'分片 {chunk_index} 上传失败'})
                        return False
            
            self._emit_event('progress', {'file': file_name, 'percent': 100})
            self._emit_event('status', {'type': 'success', 'message': f'分片上传完成: {file_name}'})
            return True
            
        except Exception as e:
            self._emit_event('error', {'message': f'分片上传出错: {e}'})
            return False
    
    def upload_text_async(self, text_content: str, password: str) -> bool:
        """异步上传文本内容"""
        def upload_worker():
            try:
                # 计算文本哈希
                content_hash = hashlib.sha256(text_content.encode('utf-8')).hexdigest()
                
                # 检查缓存
                if self._is_file_cached(content_hash):
                    self._emit_event('status', {'type': 'info', 'message': '文本内容未变，跳过上传'})
                    return True
                
                self._emit_event('status', {
                    'type': 'info',
                    'message': f'正在上传文本内容 (长度: {len(text_content)})'
                })
                
                # 创建加密载荷
                data_bytes = text_content.encode('utf-8')
                key = get_encryption_key(password)
                from cryptography.fernet import Fernet
                import json
                fernet = Fernet(key)
                
                payload = {
                    "filename": "clipboard_text.txt",
                    "content_base64": base64.b64encode(data_bytes).decode('utf-8'),
                    "is_from_text": True
                }
                encrypted_payload = fernet.encrypt(json.dumps(payload).encode('utf-8'))
                
                # 上传
                config = self.config_manager.get_config()
                status_queue = queue.Queue()
                success = upload_data(encrypted_payload, config, status_queue)
                
                # 处理状态消息
                while not status_queue.empty():
                    try:
                        msg_type, message = status_queue.get_nowait()
                        self._emit_event('status', {'type': msg_type, 'message': message})
                    except queue.Empty:
                        break
                
                if success:
                    self._add_to_cache(content_hash)
                    self._emit_event('complete', {
                        'file_path': 'clipboard_text.txt',
                        'skipped': False,
                        'text_upload': True
                    })
                
                return success
                
            except Exception as e:
                self._emit_event('error', {'message': f'文本上传出错: {e}'})
                return False
        
        # 在后台线程执行
        upload_thread = threading.Thread(target=upload_worker, daemon=True)
        upload_thread.start()
        return True