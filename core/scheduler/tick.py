"""
调度系统Tick组件
提供定时触发和周期性任务调度功能
"""

import asyncio
import time
from typing import Callable, Optional, Dict, Any, List, Awaitable
from dataclasses import dataclass
from enum import Enum
# 使用项目自定义日志管理器
from core.logger import info, warning, error, debug
# 使用事件系统
from core.event.events.scheduler_events import TickEvent
from core.event.event_bus import EventBus
# 依赖注入容器
from core.di.app_container import get_app_container # type: ignore


class TickState(Enum):
    """Tick状态枚举"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class TickConfig:
    """Tick配置数据类"""
    interval: float = 1.0  # tick间隔（秒）
    max_ticks: int = -1   # 最大tick次数，-1表示无限
    auto_start: bool = False  # 是否自动启动
    enable_logging: bool = True  # 是否启用日志


class TickComponent:
    """Tick组件类"""
    
    def __init__(self, config: Optional[TickConfig] = None, event_bus: Optional[EventBus] = None):
        """
        初始化Tick组件
        
        Args:
            config: Tick配置，如果为None则使用默认配置
            event_bus: 事件总线实例，如果为None则需要稍后设置
        """
        self.config = config or TickConfig()
        self._state = TickState.STOPPED
        self._current_tick = 0
        self._start_time = 0.0
        self._last_tick_time = 0.0
        self._tick_callbacks: List[Callable[[int, float], None]] = []
        self._async_tick_callbacks: List[Callable[[int, float], Awaitable[None]]] = []
        self._task: Optional[asyncio.Task[None]] = None
        self._event_bus = event_bus
        # 移除标准logging，使用项目日志管理器
    
    @property
    def state(self) -> TickState:
        """获取当前状态"""
        return self._state
    
    @property
    def current_tick(self) -> int:
        """获取当前tick计数"""
        return self._current_tick
    
    @property
    def elapsed_time(self) -> float:
        """获取已运行时间（秒）"""
        if self._state == TickState.STOPPED:
            return 0.0
        return time.time() - self._start_time
    
    @property
    def has_event_bus(self) -> bool:
        """检查是否已设置事件总线"""
        return self._event_bus is not None
    
    def add_tick_callback(self, callback: Callable[[int, float], None]) -> None:
        """
        添加同步tick回调函数
        
        Args:
            callback: 回调函数，接收(tick_count, elapsed_time)参数
        """
        if not callable(callback):
            raise ValueError("Callback must be callable")
        self._tick_callbacks.append(callback)
    
    def add_async_tick_callback(self, callback: Callable[[int, float], Awaitable[None]]) -> None:
        """
        添加异步tick回调函数
        
        Args:
            callback: 异步回调函数，接收(tick_count, elapsed_time)参数
        """
        if not callable(callback):
            raise ValueError("Callback must be callable")
        self._async_tick_callbacks.append(callback)
    
    def remove_tick_callback(self, callback: Callable[..., Any]) -> bool:
        """
        移除tick回调函数
        
        Args:
            callback: 要移除的回调函数
            
        Returns:
            是否成功移除
        """
        # 尝试从同步回调列表中移除
        for i, cb in enumerate(self._tick_callbacks):
            if cb is callback:
                del self._tick_callbacks[i]
                return True
        
        # 尝试从异步回调列表中移除
        for i, cb in enumerate(self._async_tick_callbacks):
            if cb is callback:
                del self._async_tick_callbacks[i]
                return True
        
        return False
    
    def start(self) -> None:
        """启动tick组件"""
        if self._state == TickState.RUNNING:
            if self.config.enable_logging:
                warning("Tick component is already running")
            return
        
        if self._state == TickState.PAUSED:
            # 从暂停状态恢复
            self._state = TickState.RUNNING
            if self.config.enable_logging:
                info("Tick component resumed")
            return
        
        # 重置状态
        self._current_tick = 0
        self._start_time = time.time()
        self._last_tick_time = self._start_time
        self._state = TickState.RUNNING
        
        # 创建并启动异步任务
        self._task = asyncio.create_task(self._tick_loop())
        
        if self.config.enable_logging:
            info(f"Tick component started with interval={self.config.interval}s")
    
    def stop(self) -> None:
        """停止tick组件"""
        if self._state == TickState.STOPPED:
            return
        
        self._state = TickState.STOPPED
        
        # 取消任务
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None
        
        if self.config.enable_logging:
            info(f"Tick component stopped after {self._current_tick} ticks")
    
    def pause(self) -> None:
        """暂停tick组件"""
        if self._state != TickState.RUNNING:
            return
        
        self._state = TickState.PAUSED
        if self.config.enable_logging:
            info(f"Tick component paused at tick {self._current_tick}")
    
    async def _tick_loop(self) -> None:
        """内部tick循环"""
        try:
            while self._state == TickState.RUNNING:
                # 检查是否达到最大tick次数
                if self.config.max_ticks > 0 and self._current_tick >= self.config.max_ticks:
                    break
                
                # 等待tick间隔
                await asyncio.sleep(self.config.interval)
                
                # 执行tick
                await self._execute_tick()
                
        except asyncio.CancelledError:
            if self.config.enable_logging:
                info("Tick loop cancelled")
        except Exception as e:
            error(f"Error in tick loop: {e}")
            self._state = TickState.STOPPED
        finally:
            self._state = TickState.STOPPED
    
    async def _execute_tick(self) -> None:
        """执行单个tick"""
        self._current_tick += 1
        current_time = time.time()
        elapsed_time = current_time - self._start_time
        
        # 记录tick时间
        self._last_tick_time = current_time
        
        # 发布Tick事件（如果事件总线可用）
        if self._event_bus is not None:
            tick_data: Dict[str, Any] = {
                "interval": self.config.interval,
                "max_ticks": self.config.max_ticks,
                "callback_count": len(self._tick_callbacks) + len(self._async_tick_callbacks)
            }
            self._event_bus.publish(TickEvent(self._current_tick, elapsed_time, tick_data))
        
        if self.config.enable_logging:
            debug(f"Tick {self._current_tick} executed, elapsed={elapsed_time:.3f}s")
        
        # 执行同步回调
        for callback in self._tick_callbacks[:]:  # 使用切片避免修改列表时的问题
            try:
                callback(self._current_tick, elapsed_time)
            except Exception as e:
                error(f"Error in sync tick callback: {e}")
        
        # 执行异步回调
        async_callbacks: List[Awaitable[None]] = []
        for callback in self._async_tick_callbacks[:]:
            try:
                result = callback(self._current_tick, elapsed_time)
                if asyncio.iscoroutine(result):
                    async_callbacks.append(result)
            except Exception as e:
                error(f"Error in async tick callback setup: {e}")
        
        # 并发执行异步回调
        if async_callbacks:
            try:
                await asyncio.gather(*async_callbacks, return_exceptions=True)
            except Exception as e:
                error(f"Error in async tick callbacks: {e}")
    
    def set_event_bus(self, event_bus: EventBus) -> None:
        """设置事件总线实例"""
        self._event_bus = event_bus
    
    def get_stats(self) -> Dict[str, Any]:
        """获取tick组件统计信息"""
        return {
            'state': self._state.value,
            'current_tick': self._current_tick,
            'elapsed_time': self.elapsed_time,
            'interval': self.config.interval,
            'max_ticks': self.config.max_ticks,
            'callback_count': len(self._tick_callbacks) + len(self._async_tick_callbacks),
            'sync_callbacks': len(self._tick_callbacks),
            'async_callbacks': len(self._async_tick_callbacks)
        }
    
    def reset(self) -> None:
        """重置tick组件"""
        self.stop()
        self._current_tick = 0
        self._start_time = 0.0
        self._last_tick_time = 0.0
        if self.config.enable_logging:
            info("Tick component reset")