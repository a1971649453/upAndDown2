# core/event_system.py
"""
事件系统 - 实现观察者模式的发布-订阅机制
支持组件间解耦通信和状态管理
"""

import threading
import time
import queue
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    """事件类型枚举"""
    # 文件相关事件
    FILE_SELECTED = "file_selected"
    FILE_ADDED = "file_added"
    FILE_REMOVED = "file_removed"
    
    # 上传相关事件
    UPLOAD_STARTED = "upload_started"
    UPLOAD_PROGRESS = "upload_progress"
    UPLOAD_COMPLETED = "upload_completed"
    UPLOAD_FAILED = "upload_failed"
    UPLOAD_CANCELLED = "upload_cancelled"
    
    # 剪切板事件
    CLIPBOARD_TEXT_CHANGED = "clipboard_text_changed"
    CLIPBOARD_FILES_CHANGED = "clipboard_files_changed"
    
    # UI事件
    THEME_CHANGED = "theme_changed"
    LAYOUT_CHANGED = "layout_changed"
    WINDOW_RESIZED = "window_resized"
    
    # 系统事件
    CONFIG_CHANGED = "config_changed"
    ERROR_OCCURRED = "error_occurred"
    STATUS_UPDATED = "status_updated"
    
    # 应用事件
    APP_STARTED = "app_started"
    APP_CLOSING = "app_closing"

@dataclass
class Event:
    """事件数据结构"""
    type: EventType
    data: Any
    timestamp: float
    source: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class EventManager:
    """事件管理器 - 实现发布-订阅模式"""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_queue = queue.Queue()
        self._processing = False
        self._process_thread = None
        self._lock = threading.RLock()
        
        # 事件历史记录
        self._event_history: List[Event] = []
        self._max_history = 1000
        
        # 错误处理
        self._error_handlers: List[Callable] = []
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """订阅事件"""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """取消订阅事件"""
        with self._lock:
            if event_type in self._subscribers:
                if callback in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(callback)
                
                # 如果没有订阅者了，删除该事件类型
                if not self._subscribers[event_type]:
                    del self._subscribers[event_type]
    
    def publish(self, event_type: EventType, data: Any = None, source: str = None):
        """发布事件"""
        event = Event(
            type=event_type,
            data=data,
            timestamp=time.time(),
            source=source
        )
        
        # 添加到队列进行异步处理
        self._event_queue.put(event)
        
        # 如果处理线程未启动，启动它
        if not self._processing:
            self._start_processing()
    
    def publish_sync(self, event_type: EventType, data: Any = None, source: str = None):
        """同步发布事件（立即处理）"""
        event = Event(
            type=event_type,
            data=data,
            timestamp=time.time(),
            source=source
        )
        
        self._process_event(event)
    
    def _start_processing(self):
        """启动事件处理线程"""
        with self._lock:
            if self._processing:
                return
            
            self._processing = True
            self._process_thread = threading.Thread(target=self._process_events, daemon=True)
            self._process_thread.start()
    
    def _process_events(self):
        """事件处理循环"""
        while self._processing:
            try:
                # 从队列获取事件，设置超时避免无限等待
                event = self._event_queue.get(timeout=1.0)
                self._process_event(event)
                
            except queue.Empty:
                # 队列为空，继续循环
                continue
            except Exception as e:
                self._handle_error(f"事件处理出错: {e}")
    
    def _process_event(self, event: Event):
        """处理单个事件"""
        try:
            # 添加到历史记录
            self._add_to_history(event)
            
            # 获取订阅者列表
            with self._lock:
                subscribers = self._subscribers.get(event.type, []).copy()
            
            # 调用所有订阅者
            for callback in subscribers:
                try:
                    callback(event)
                except Exception as e:
                    self._handle_error(f"事件回调执行出错 {event.type}: {e}")
                    
        except Exception as e:
            self._handle_error(f"事件处理异常 {event.type}: {e}")
    
    def _add_to_history(self, event: Event):
        """添加事件到历史记录"""
        with self._lock:
            self._event_history.append(event)
            
            # 限制历史记录大小
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]
    
    def _handle_error(self, error_message: str):
        """处理错误"""
        print(f"EventManager Error: {error_message}")
        
        # 调用错误处理器
        for handler in self._error_handlers:
            try:
                handler(error_message)
            except Exception:
                pass  # 避免错误处理器本身出错导致循环
    
    def add_error_handler(self, handler: Callable[[str], None]):
        """添加错误处理器"""
        if handler not in self._error_handlers:
            self._error_handlers.append(handler)
    
    def get_event_history(self, event_type: EventType = None, limit: int = 100) -> List[Event]:
        """获取事件历史"""
        with self._lock:
            history = self._event_history.copy()
        
        # 过滤事件类型
        if event_type:
            history = [e for e in history if e.type == event_type]
        
        # 限制数量，返回最新的
        return history[-limit:] if limit else history
    
    def get_subscriber_count(self, event_type: EventType = None) -> int:
        """获取订阅者数量"""
        with self._lock:
            if event_type:
                return len(self._subscribers.get(event_type, []))
            else:
                return sum(len(subs) for subs in self._subscribers.values())
    
    def clear_history(self):
        """清空事件历史"""
        with self._lock:
            self._event_history.clear()
    
    def stop_processing(self):
        """停止事件处理"""
        self._processing = False
        if self._process_thread and self._process_thread.is_alive():
            self._process_thread.join(timeout=2)

class StateManager:
    """状态管理器 - 集中化应用状态管理"""
    
    def __init__(self, event_manager: EventManager):
        self.event_manager = event_manager
        self._state: Dict[str, Any] = {}
        self._lock = threading.RLock()
        
        # 状态变化回调
        self._state_callbacks: Dict[str, List[Callable]] = {}
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """获取状态值"""
        with self._lock:
            return self._state.get(key, default)
    
    def set_state(self, key: str, value: Any, emit_event: bool = True):
        """设置状态值"""
        old_value = None
        
        with self._lock:
            old_value = self._state.get(key)
            self._state[key] = value
        
        # 触发状态变化回调
        self._trigger_state_callbacks(key, value, old_value)
        
        # 发布状态变化事件
        if emit_event:
            self.event_manager.publish(
                EventType.STATUS_UPDATED,
                {
                    'key': key,
                    'value': value,
                    'old_value': old_value
                },
                source='StateManager'
            )
    
    def update_state(self, updates: Dict[str, Any], emit_event: bool = True):
        """批量更新状态"""
        changes = {}
        
        with self._lock:
            for key, value in updates.items():
                old_value = self._state.get(key)
                self._state[key] = value
                changes[key] = {'value': value, 'old_value': old_value}
        
        # 触发回调
        for key, change in changes.items():
            self._trigger_state_callbacks(key, change['value'], change['old_value'])
        
        # 发布事件
        if emit_event:
            self.event_manager.publish(
                EventType.STATUS_UPDATED,
                {'batch_update': changes},
                source='StateManager'
            )
    
    def get_all_state(self) -> Dict[str, Any]:
        """获取所有状态"""
        with self._lock:
            return self._state.copy()
    
    def subscribe_state_change(self, key: str, callback: Callable[[str, Any, Any], None]):
        """订阅状态变化"""
        with self._lock:
            if key not in self._state_callbacks:
                self._state_callbacks[key] = []
            
            if callback not in self._state_callbacks[key]:
                self._state_callbacks[key].append(callback)
    
    def unsubscribe_state_change(self, key: str, callback: Callable[[str, Any, Any], None]):
        """取消订阅状态变化"""
        with self._lock:
            if key in self._state_callbacks:
                if callback in self._state_callbacks[key]:
                    self._state_callbacks[key].remove(callback)
                
                if not self._state_callbacks[key]:
                    del self._state_callbacks[key]
    
    def _trigger_state_callbacks(self, key: str, new_value: Any, old_value: Any):
        """触发状态变化回调"""
        callbacks = []
        
        with self._lock:
            callbacks = self._state_callbacks.get(key, []).copy()
        
        for callback in callbacks:
            try:
                callback(key, new_value, old_value)
            except Exception as e:
                print(f"状态回调执行出错 {key}: {e}")
    
    def clear_state(self):
        """清空所有状态"""
        with self._lock:
            self._state.clear()

class AsyncTaskManager:
    """异步任务管理器 - 管理后台任务执行"""
    
    def __init__(self, event_manager: EventManager, max_workers: int = 4):
        self.event_manager = event_manager
        self.max_workers = max_workers
        
        # 任务队列和工作线程
        self._task_queue = queue.Queue()
        self._workers: List[threading.Thread] = []
        self._running = False
        self._lock = threading.Lock()
        
        # 任务管理
        self._tasks: Dict[str, Dict] = {}  # {task_id: task_info}
        self._task_counter = 0
    
    def start(self):
        """启动任务管理器"""
        with self._lock:
            if self._running:
                return
            
            self._running = True
            
            # 创建工作线程
            for i in range(self.max_workers):
                worker = threading.Thread(target=self._worker_loop, args=(i,), daemon=True)
                worker.start()
                self._workers.append(worker)
    
    def stop(self):
        """停止任务管理器"""
        with self._lock:
            self._running = False
        
        # 等待所有工作线程结束
        for worker in self._workers:
            worker.join(timeout=2)
        
        self._workers.clear()
    
    def submit_task(self, task_func: Callable, *args, **kwargs) -> str:
        """提交异步任务"""
        with self._lock:
            task_id = f"task_{self._task_counter}"
            self._task_counter += 1
        
        task_info = {
            'id': task_id,
            'func': task_func,
            'args': args,
            'kwargs': kwargs,
            'status': 'pending',
            'created_at': time.time(),
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error': None
        }
        
        self._tasks[task_id] = task_info
        self._task_queue.put(task_info)
        
        return task_id
    
    def _worker_loop(self, worker_id: int):
        """工作线程循环"""
        while self._running:
            try:
                # 获取任务
                task_info = self._task_queue.get(timeout=1.0)
                
                # 执行任务
                self._execute_task(task_info, worker_id)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
    
    def _execute_task(self, task_info: Dict, worker_id: int):
        """执行任务"""
        task_id = task_info['id']
        
        try:
            # 更新任务状态
            task_info['status'] = 'running'
            task_info['started_at'] = time.time()
            
            # 执行任务函数
            result = task_info['func'](*task_info['args'], **task_info['kwargs'])
            
            # 记录结果
            task_info['status'] = 'completed'
            task_info['completed_at'] = time.time()
            task_info['result'] = result
            
        except Exception as e:
            # 记录错误
            task_info['status'] = 'failed'
            task_info['completed_at'] = time.time()
            task_info['error'] = str(e)
            
            # 发布错误事件
            self.event_manager.publish(
                EventType.ERROR_OCCURRED,
                {
                    'task_id': task_id,
                    'error': str(e),
                    'worker_id': worker_id
                },
                source='AsyncTaskManager'
            )
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        return self._tasks.get(task_id)
    
    def get_running_tasks(self) -> List[Dict]:
        """获取正在运行的任务"""
        return [task for task in self._tasks.values() if task['status'] == 'running']
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务（仅限尚未开始的任务）"""
        task_info = self._tasks.get(task_id)
        if task_info and task_info['status'] == 'pending':
            task_info['status'] = 'cancelled'
            return True
        return False