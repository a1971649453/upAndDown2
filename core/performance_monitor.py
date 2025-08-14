# core/performance_monitor.py
"""
性能监控和优化模块 - 监控应用性能并进行优化
"""

import time
import threading
import psutil
import os
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from collections import deque

@dataclass
class PerformanceMetrics:
    """性能指标数据结构"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    thread_count: int
    response_time_ms: float
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'cpu_percent': self.cpu_percent,
            'memory_mb': self.memory_mb,
            'memory_percent': self.memory_percent,
            'thread_count': self.thread_count,
            'response_time_ms': self.response_time_ms
        }

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.process = psutil.Process(os.getpid())
        
        # 监控状态
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_interval = 5.0  # 5秒采样一次
        
        # 性能阈值
        self.thresholds = {
            'cpu_percent': 80.0,      # CPU使用率阈值
            'memory_mb': 200.0,       # 内存使用量阈值(MB)
            'memory_percent': 70.0,   # 内存使用率阈值
            'response_time_ms': 1000.0  # 响应时间阈值(ms)
        }
        
        # 回调函数
        self.callbacks = {
            'threshold_exceeded': None,  # 阈值超出回调
            'metrics_updated': None      # 指标更新回调
        }
    
    def set_callback(self, event_type: str, callback: Callable):
        """设置回调函数"""
        if event_type in self.callbacks:
            self.callbacks[event_type] = callback
    
    def start_monitoring(self):
        """开始性能监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # 检查阈值
                self._check_thresholds(metrics)
                
                # 触发更新回调
                if self.callbacks['metrics_updated']:
                    self.callbacks['metrics_updated'](metrics)
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                print(f"性能监控出错: {e}")
                time.sleep(self.monitor_interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        try:
            # CPU和内存信息
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024  # 转换为MB
            memory_percent = self.process.memory_percent()
            
            # 线程数
            thread_count = self.process.num_threads()
            
            # 响应时间（这里使用一个简单的测试）
            start_time = time.time()
            # 简单的响应时间测试
            _ = len(self.metrics_history)
            response_time_ms = (time.time() - start_time) * 1000
            
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                thread_count=thread_count,
                response_time_ms=response_time_ms
            )
            
        except Exception as e:
            # 返回默认值
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0,
                thread_count=0,
                response_time_ms=0.0
            )
    
    def _check_thresholds(self, metrics: PerformanceMetrics):
        """检查性能阈值"""
        exceeded = []
        
        if metrics.cpu_percent > self.thresholds['cpu_percent']:
            exceeded.append(('cpu_percent', metrics.cpu_percent, self.thresholds['cpu_percent']))
        
        if metrics.memory_mb > self.thresholds['memory_mb']:
            exceeded.append(('memory_mb', metrics.memory_mb, self.thresholds['memory_mb']))
        
        if metrics.memory_percent > self.thresholds['memory_percent']:
            exceeded.append(('memory_percent', metrics.memory_percent, self.thresholds['memory_percent']))
        
        if metrics.response_time_ms > self.thresholds['response_time_ms']:
            exceeded.append(('response_time_ms', metrics.response_time_ms, self.thresholds['response_time_ms']))
        
        if exceeded and self.callbacks['threshold_exceeded']:
            self.callbacks['threshold_exceeded'](exceeded)
    
    def get_latest_metrics(self) -> Optional[PerformanceMetrics]:
        """获取最新的性能指标"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_average_metrics(self, minutes: int = 5) -> Optional[Dict]:
        """获取指定时间内的平均指标"""
        if not self.metrics_history:
            return None
        
        cutoff_time = time.time() - (minutes * 60)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return None
        
        count = len(recent_metrics)
        return {
            'cpu_percent': sum(m.cpu_percent for m in recent_metrics) / count,
            'memory_mb': sum(m.memory_mb for m in recent_metrics) / count,
            'memory_percent': sum(m.memory_percent for m in recent_metrics) / count,
            'thread_count': sum(m.thread_count for m in recent_metrics) / count,
            'response_time_ms': sum(m.response_time_ms for m in recent_metrics) / count,
            'sample_count': count
        }
    
    def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        if not self.metrics_history:
            return {'status': 'no_data'}
        
        latest = self.get_latest_metrics()
        avg_5min = self.get_average_metrics(5)
        
        # 判断性能状态
        status = 'good'
        if latest.cpu_percent > self.thresholds['cpu_percent'] * 0.8:
            status = 'warning'
        if (latest.cpu_percent > self.thresholds['cpu_percent'] or 
            latest.memory_mb > self.thresholds['memory_mb']):
            status = 'critical'
        
        return {
            'status': status,
            'latest': latest.to_dict() if latest else None,
            'average_5min': avg_5min,
            'monitoring': self.monitoring,
            'sample_count': len(self.metrics_history)
        }

class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, max_errors: int = 50):
        self.max_errors = max_errors
        self.error_history: deque = deque(maxlen=max_errors)
        self.error_callbacks: List[Callable] = []
        
        # 错误计数
        self.error_counts = {
            'critical': 0,
            'error': 0,
            'warning': 0,
            'info': 0
        }
    
    def add_error_callback(self, callback: Callable):
        """添加错误回调"""
        if callback not in self.error_callbacks:
            self.error_callbacks.append(callback)
    
    def handle_error(self, error: Exception, context: str = "", level: str = "error"):
        """处理错误"""
        error_info = {
            'timestamp': time.time(),
            'type': type(error).__name__,
            'message': str(error),
            'context': context,
            'level': level
        }
        
        # 添加到历史记录
        self.error_history.append(error_info)
        
        # 更新计数
        if level in self.error_counts:
            self.error_counts[level] += 1
        
        # 触发回调
        for callback in self.error_callbacks:
            try:
                callback(error_info)
            except Exception:
                pass  # 避免回调本身出错
        
        # 打印错误（可选）
        print(f"[{level.upper()}] {context}: {error}")
    
    def get_error_summary(self) -> Dict:
        """获取错误摘要"""
        recent_errors = [e for e in self.error_history 
                        if time.time() - e['timestamp'] < 3600]  # 最近1小时
        
        return {
            'total_errors': len(self.error_history),
            'recent_errors': len(recent_errors),
            'error_counts': self.error_counts.copy(),
            'latest_errors': list(self.error_history)[-5:] if self.error_history else []
        }
    
    def clear_errors(self):
        """清空错误历史"""
        self.error_history.clear()
        self.error_counts = {k: 0 for k in self.error_counts}

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self, performance_monitor: PerformanceMonitor):
        self.monitor = performance_monitor
        self.optimization_rules = []
        
        # 添加默认优化规则
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """设置默认优化规则"""
        # 内存使用过高时的优化
        def memory_optimization():
            import gc
            gc.collect()  # 强制垃圾回收
            return "执行内存垃圾回收"
        
        # CPU使用过高时的优化
        def cpu_optimization():
            return "建议减少并发任务"
        
        self.optimization_rules = [
            {
                'condition': lambda m: m.memory_mb > 150,
                'action': memory_optimization,
                'description': '内存使用优化'
            },
            {
                'condition': lambda m: m.cpu_percent > 70,
                'action': cpu_optimization,
                'description': 'CPU使用优化'
            }
        ]
    
    def optimize(self) -> List[str]:
        """执行性能优化"""
        latest_metrics = self.monitor.get_latest_metrics()
        if not latest_metrics:
            return []
        
        optimization_results = []
        
        for rule in self.optimization_rules:
            try:
                if rule['condition'](latest_metrics):
                    result = rule['action']()
                    optimization_results.append(f"{rule['description']}: {result}")
            except Exception as e:
                optimization_results.append(f"{rule['description']}: 优化失败 - {e}")
        
        return optimization_results
    
    def add_optimization_rule(self, condition: Callable, action: Callable, description: str):
        """添加优化规则"""
        self.optimization_rules.append({
            'condition': condition,
            'action': action,
            'description': description
        })

class ApplicationHealthMonitor:
    """应用健康监控器"""
    
    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.error_handler = ErrorHandler()
        self.optimizer = PerformanceOptimizer(self.performance_monitor)
        
        # 健康状态
        self.health_status = 'unknown'
        
        # 设置回调
        self.performance_monitor.set_callback('threshold_exceeded', self._on_performance_issue)
        self.error_handler.add_error_callback(self._on_error)
    
    def start(self):
        """启动健康监控"""
        self.performance_monitor.start_monitoring()
    
    def stop(self):
        """停止健康监控"""
        self.performance_monitor.stop_monitoring()
    
    def _on_performance_issue(self, exceeded_thresholds):
        """性能问题处理"""
        # 尝试自动优化
        optimization_results = self.optimizer.optimize()
        
        # 记录问题
        for metric, value, threshold in exceeded_thresholds:
            self.error_handler.handle_error(
                Exception(f"{metric}超出阈值: {value:.2f} > {threshold:.2f}"),
                "性能监控",
                "warning"
            )
    
    def _on_error(self, error_info):
        """错误处理"""
        # 根据错误级别更新健康状态
        if error_info['level'] == 'critical':
            self.health_status = 'critical'
        elif error_info['level'] == 'error' and self.health_status != 'critical':
            self.health_status = 'degraded'
    
    def get_health_report(self) -> Dict:
        """获取健康报告"""
        perf_summary = self.performance_monitor.get_performance_summary()
        error_summary = self.error_handler.get_error_summary()
        
        # 综合判断健康状态
        overall_status = 'healthy'
        
        if perf_summary.get('status') == 'critical' or error_summary['error_counts']['critical'] > 0:
            overall_status = 'critical'
        elif (perf_summary.get('status') == 'warning' or 
              error_summary['error_counts']['error'] > 5 or
              error_summary['recent_errors'] > 10):
            overall_status = 'degraded'
        
        return {
            'overall_status': overall_status,
            'performance': perf_summary,
            'errors': error_summary,
            'recommendations': self._get_recommendations(perf_summary, error_summary)
        }
    
    def _get_recommendations(self, perf_summary: Dict, error_summary: Dict) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if perf_summary.get('status') == 'critical':
            recommendations.append("建议重启应用以释放资源")
        
        if error_summary['recent_errors'] > 5:
            recommendations.append("检测到频繁错误，建议检查日志")
        
        latest_metrics = perf_summary.get('latest')
        if latest_metrics and latest_metrics['memory_mb'] > 100:
            recommendations.append("内存使用较高，建议关闭不必要的功能")
        
        if not recommendations:
            recommendations.append("应用运行正常")
        
        return recommendations