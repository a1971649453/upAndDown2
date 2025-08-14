# services/smart_assistant.py
"""
智能化辅助服务 - 提供用户偏好记忆、文件类型识别、重复检测等功能
"""

import os
import json
import hashlib
import mimetypes
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

@dataclass
class UserPreference:
    """用户偏好数据结构"""
    upload_quality: str = "standard"  # standard, high, fast
    auto_upload: bool = False
    preferred_formats: List[str] = None
    max_file_size_mb: int = 50
    enable_compression: bool = False
    theme: str = "light"
    language: str = "zh-cn"
    
    def __post_init__(self):
        if self.preferred_formats is None:
            self.preferred_formats = ["jpg", "png", "pdf", "txt", "docx"]

@dataclass
class FileInfo:
    """文件信息数据结构"""
    path: str
    name: str
    size: int
    mime_type: str
    hash: str
    created_time: float
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None

class SmartFileAnalyzer:
    """智能文件分析器"""
    
    def __init__(self):
        # 文件类型映射
        self.file_type_map = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
            'spreadsheet': ['.xls', '.xlsx', '.csv', '.ods'],
            'presentation': ['.ppt', '.pptx', '.odp'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'video': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg'],
            'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c']
        }
        
        # 文件大小阈值（MB）
        self.size_thresholds = {
            'tiny': 0.1,
            'small': 1,
            'medium': 10,
            'large': 100,
            'huge': 1000
        }
    
    def analyze_file(self, file_path: str) -> FileInfo:
        """分析文件信息"""
        try:
            # 基本信息
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            created_time = os.path.getctime(file_path)
            
            # MIME类型检测
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # 计算文件哈希
            file_hash = self._calculate_file_hash(file_path)
            
            return FileInfo(
                path=file_path,
                name=file_name,
                size=file_size,
                mime_type=mime_type,
                hash=file_hash,
                created_time=created_time
            )
            
        except Exception as e:
            # 创建错误信息对象
            return FileInfo(
                path=file_path,
                name=os.path.basename(file_path),
                size=0,
                mime_type='unknown',
                hash='',
                created_time=0
            )
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # 只读取前1MB来计算哈希，提高速度
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
                    # 限制读取大小，避免大文件影响性能
                    if f.tell() > 1024 * 1024:  # 1MB
                        break
            return sha256_hash.hexdigest()
        except Exception:
            return ''
    
    def get_file_category(self, file_path: str) -> str:
        """获取文件类别"""
        ext = os.path.splitext(file_path)[1].lower()
        
        for category, extensions in self.file_type_map.items():
            if ext in extensions:
                return category
        
        return 'other'
    
    def get_file_size_category(self, file_size: int) -> str:
        """获取文件大小类别"""
        size_mb = file_size / (1024 * 1024)
        
        for category, threshold in self.size_thresholds.items():
            if size_mb <= threshold:
                return category
        
        return 'huge'
    
    def suggest_upload_settings(self, file_info: FileInfo) -> Dict[str, Any]:
        """建议上传设置"""
        suggestions = {
            'quality': 'standard',
            'compression': False,
            'priority': 'normal',
            'batch_size': 1
        }
        
        category = self.get_file_category(file_info.path)
        size_category = self.get_file_size_category(file_info.size)
        
        # 根据文件类型调整建议
        if category == 'image':
            if size_category in ['large', 'huge']:
                suggestions['compression'] = True
                suggestions['quality'] = 'high'
        elif category == 'archive':
            suggestions['priority'] = 'low'  # 压缩文件通常不急
        elif category == 'document':
            suggestions['priority'] = 'high'  # 文档通常比较重要
        
        # 根据文件大小调整
        if size_category == 'huge':
            suggestions['quality'] = 'fast'  # 大文件使用快速模式
        elif size_category == 'tiny':
            suggestions['batch_size'] = 10  # 小文件可以批量处理
        
        return suggestions

class DuplicateDetector:
    """重复文件检测器"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.file_history: Dict[str, FileInfo] = {}  # hash -> FileInfo
        self.lock = threading.RLock()
    
    def check_duplicate(self, file_info: FileInfo) -> Tuple[bool, Optional[FileInfo]]:
        """检查文件是否重复"""
        with self.lock:
            if file_info.hash in self.file_history:
                duplicate_file = self.file_history[file_info.hash]
                return True, duplicate_file
            
            return False, None
    
    def add_file(self, file_info: FileInfo):
        """添加文件到历史记录"""
        with self.lock:
            self.file_history[file_info.hash] = file_info
            
            # 限制历史记录大小
            if len(self.file_history) > self.max_history:
                # 删除最旧的记录（简单策略：删除第一个）
                oldest_hash = next(iter(self.file_history))
                del self.file_history[oldest_hash]
    
    def get_duplicate_files(self) -> List[Tuple[str, List[FileInfo]]]:
        """获取所有重复文件组"""
        hash_groups = {}
        
        with self.lock:
            for file_info in self.file_history.values():
                if file_info.hash not in hash_groups:
                    hash_groups[file_info.hash] = []
                hash_groups[file_info.hash].append(file_info)
        
        # 只返回有重复的组
        duplicates = []
        for file_hash, files in hash_groups.items():
            if len(files) > 1:
                duplicates.append((file_hash, files))
        
        return duplicates
    
    def clear_history(self):
        """清空历史记录"""
        with self.lock:
            self.file_history.clear()

class UserPreferenceManager:
    """用户偏好管理器"""
    
    def __init__(self, config_file: str = "user_preferences.json"):
        self.config_file = config_file
        self.preferences = UserPreference()
        self.lock = threading.RLock()
        
        # 加载现有偏好
        self.load_preferences()
    
    def load_preferences(self):
        """加载用户偏好"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.preferences = UserPreference(**data)
        except Exception as e:
            print(f"加载用户偏好失败: {e}")
            # 使用默认偏好
            self.preferences = UserPreference()
    
    def save_preferences(self):
        """保存用户偏好"""
        try:
            with self.lock:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(asdict(self.preferences), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存用户偏好失败: {e}")
    
    def update_preference(self, key: str, value: Any):
        """更新单个偏好"""
        with self.lock:
            if hasattr(self.preferences, key):
                setattr(self.preferences, key, value)
                self.save_preferences()
    
    def get_preference(self, key: str, default: Any = None):
        """获取偏好值"""
        return getattr(self.preferences, key, default)
    
    def get_all_preferences(self) -> UserPreference:
        """获取所有偏好"""
        return self.preferences

class SmartAssistant:
    """智能助手 - 整合各种智能化功能"""
    
    def __init__(self):
        self.file_analyzer = SmartFileAnalyzer()
        self.duplicate_detector = DuplicateDetector()
        self.preference_manager = UserPreferenceManager()
        
        # 统计信息
        self.stats = {
            'files_analyzed': 0,
            'duplicates_found': 0,
            'total_size_saved': 0,
            'recommendations_given': 0
        }
    
    def analyze_and_check_file(self, file_path: str) -> Dict[str, Any]:
        """分析文件并检查重复"""
        # 分析文件
        file_info = self.file_analyzer.analyze_file(file_path)
        self.stats['files_analyzed'] += 1
        
        # 检查重复
        is_duplicate, duplicate_file = self.duplicate_detector.check_duplicate(file_info)
        
        if is_duplicate:
            self.stats['duplicates_found'] += 1
            self.stats['total_size_saved'] += file_info.size
            file_info.is_duplicate = True
            file_info.duplicate_of = duplicate_file.path
        else:
            # 添加到历史记录
            self.duplicate_detector.add_file(file_info)
        
        # 获取上传建议
        upload_suggestions = self.file_analyzer.suggest_upload_settings(file_info)
        self.stats['recommendations_given'] += 1
        
        # 获取文件类别
        file_category = self.file_analyzer.get_file_category(file_path)
        size_category = self.file_analyzer.get_file_size_category(file_info.size)
        
        return {
            'file_info': file_info,
            'is_duplicate': is_duplicate,
            'duplicate_file': duplicate_file,
            'category': file_category,
            'size_category': size_category,
            'upload_suggestions': upload_suggestions,
            'should_skip': is_duplicate,
            'recommendation': self._generate_recommendation(file_info, is_duplicate, file_category)
        }
    
    def _generate_recommendation(self, file_info: FileInfo, is_duplicate: bool, category: str) -> str:
        """生成智能建议"""
        if is_duplicate:
            return f"检测到重复文件，建议跳过上传以节省空间和时间"
        
        if category == 'image' and file_info.size > 10 * 1024 * 1024:  # 10MB
            return "大型图片文件，建议启用压缩以减少上传时间"
        elif category == 'document':
            return "文档文件，建议高优先级上传"
        elif category == 'archive':
            return "压缩文件，可以低优先级处理"
        else:
            return "文件分析完成，可以正常上传"
    
    def get_smart_defaults(self) -> Dict[str, Any]:
        """获取智能默认设置"""
        prefs = self.preference_manager.get_all_preferences()
        
        return {
            'auto_upload': prefs.auto_upload,
            'upload_quality': prefs.upload_quality,
            'max_file_size_mb': prefs.max_file_size_mb,
            'enable_compression': prefs.enable_compression,
            'preferred_formats': prefs.preferred_formats
        }
    
    def learn_from_user_action(self, action_type: str, file_info: FileInfo, user_choice: str):
        """从用户行为中学习"""
        # 这里可以实现机器学习逻辑
        # 现在只是简单的偏好更新
        
        if action_type == 'upload_quality' and user_choice != self.preference_manager.get_preference('upload_quality'):
            # 用户选择了不同的质量设置，可能想要更新偏好
            category = self.file_analyzer.get_file_category(file_info.path)
            # 可以根据文件类型记录用户偏好
            pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'duplicate_rate': (self.stats['duplicates_found'] / max(self.stats['files_analyzed'], 1)) * 100,
            'space_saved_mb': self.stats['total_size_saved'] / (1024 * 1024)
        }