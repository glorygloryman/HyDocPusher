"""
重试处理器模块
实现指数退避重试逻辑，用于HTTP请求失败后的自动重试
"""

import asyncio
import logging
import time
from typing import Any, Callable, Optional, Type, Union
from functools import wraps

from ..exceptions.custom_exceptions import (
    ArchiveClientException,
    RetryExhaustedException,
    ConnectionException
)

logger = logging.getLogger(__name__)


class RetryHandler:
    """重试处理器类，实现指数退避重试逻辑"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[tuple[Type[Exception], ...]] = None,
        non_retryable_exceptions: Optional[tuple[Type[Exception], ...]] = None
    ):
        """
        初始化重试处理器
        
        Args:
            max_attempts: 最大重试次数，默认为3次（首次尝试+2次重试）
            base_delay: 基础延迟时间（秒），默认为1.0秒
            max_delay: 最大延迟时间（秒），默认为60.0秒
            exponential_base: 指数退避基数，默认为2.0
            jitter: 是否添加随机抖动，默认为True
            retryable_exceptions: 可重试的异常类型元组
            non_retryable_exceptions: 不可重试的异常类型元组
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        
        # 设置默认的可重试异常
        self.retryable_exceptions = retryable_exceptions or (
            ConnectionException,
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
            ArchiveClientException
        )
        
        # 设置默认的不可重试异常
        self.non_retryable_exceptions = non_retryable_exceptions or (
            ValueError,
            TypeError,
            AttributeError,
            PermissionError
        )
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        计算重试延迟时间
        
        Args:
            attempt: 当前尝试次数（从1开始）
            
        Returns:
            延迟时间（秒）
        """
        # 指数退避计算：base_delay * (exponential_base ^ (attempt - 1))
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        
        # 限制最大延迟时间
        delay = min(delay, self.max_delay)
        
        # 添加随机抖动（±10%）以避免惊群效应
        if self.jitter:
            import random
            jitter_range = delay * 0.1
            delay = delay + random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)  # 确保延迟时间不为负数
    
    def _is_retryable_exception(self, exception: Exception) -> bool:
        """
        判断异常是否可重试
        
        Args:
            exception: 异常实例
            
        Returns:
            是否可重试
        """
        # 首先检查是否在不可重试异常列表中
        if isinstance(exception, self.non_retryable_exceptions):
            return False
        
        # 对于ArchiveClientException，需要根据具体情况判断
        if isinstance(exception, ArchiveClientException):
            # 通常认证失败、权限错误等不应该重试
            error_message = str(exception).lower()
            non_retryable_keywords = [
                'authentication', 'auth', 'unauthorized', 'forbidden',
                'permission', 'invalid', 'validation', 'malformed', 'bad request'
            ]
            # 如果错误消息中包含不可重试的关键词，则返回False（不可重试）
            has_non_retryable_keyword = any(keyword in error_message for keyword in non_retryable_keywords)
            if has_non_retryable_keyword:
                return False
            # 如果没有不可重试的关键词，则继续检查是否在可重试列表中
            return isinstance(exception, self.retryable_exceptions)
        
        # 然后检查其他可重试异常
        if isinstance(exception, self.retryable_exceptions):
            return True
        
        return False  # 默认不可重试
    
    async def execute_with_retry_async(
        self,
        func: Callable[[], Any],
        *args,
        **kwargs
    ) -> Any:
        """
        异步执行函数并应用重试逻辑
        
        Args:
            func: 要执行的异步函数
            *args: 函数位置参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            RetryExhaustedException: 重试次数耗尽后的最后一个异常
        """
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.debug(f"Attempt {attempt}/{self.max_attempts} executing function")
                
                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    # 如果函数不是异步的，在事件循环中运行它
                    import concurrent.futures
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, func, *args, **kwargs)
                
                # 如果执行成功，记录成功信息并返回结果
                if attempt > 1:
                    logger.info(f"Function succeeded on attempt {attempt}/{self.max_attempts}")
                else:
                    logger.debug(f"Function succeeded on first attempt")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # 检查是否可重试
                if not self._is_retryable_exception(e):
                    logger.warning(f"Non-retryable exception on attempt {attempt}: {e}")
                    raise e
                
                # 如果这是最后一次尝试，不再重试
                if attempt >= self.max_attempts:
                    logger.error(f"Max attempts ({self.max_attempts}) reached. Last exception: {e}")
                    break
                
                # 计算延迟时间并等待
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"Attempt {attempt} failed with retryable exception: {e}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                
                await asyncio.sleep(delay)
        
        # 所有重试都失败，抛出重试耗尽异常
        raise RetryExhaustedException(
            f"Function failed after {self.max_attempts} attempts. Last error: {last_exception}",
            cause=last_exception,
            retry_count=self.max_attempts
        )
    
    def execute_with_retry_sync(
        self,
        func: Callable[[], Any],
        *args,
        **kwargs
    ) -> Any:
        """
        同步执行函数并应用重试逻辑
        
        Args:
            func: 要执行的同步函数
            *args: 函数位置参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            RetryExhaustedException: 重试次数耗尽后的最后一个异常
        """
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.debug(f"Attempt {attempt}/{self.max_attempts} executing function")
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 如果执行成功，记录成功信息并返回结果
                if attempt > 1:
                    logger.info(f"Function succeeded on attempt {attempt}/{self.max_attempts}")
                else:
                    logger.debug(f"Function succeeded on first attempt")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # 检查是否可重试
                if not self._is_retryable_exception(e):
                    logger.warning(f"Non-retryable exception on attempt {attempt}: {e}")
                    raise e
                
                # 如果这是最后一次尝试，不再重试
                if attempt >= self.max_attempts:
                    logger.error(f"Max attempts ({self.max_attempts}) reached. Last exception: {e}")
                    break
                
                # 计算延迟时间并等待
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"Attempt {attempt} failed with retryable exception: {e}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                
                time.sleep(delay)
        
        # 所有重试都失败，抛出重试耗尽异常
        raise RetryExhaustedException(
            f"Function failed after {self.max_attempts} attempts. Last error: {last_exception}",
            cause=last_exception,
            retry_count=self.max_attempts
        )
    
    def __call__(self, func: Callable) -> Callable:
        """
        装饰器模式，将重试逻辑应用到函数上
        
        Args:
            func: 要装饰的函数
            
        Returns:
            装饰后的函数
        """
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self.execute_with_retry_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self.execute_with_retry_sync(func, *args, **kwargs)
            return sync_wrapper


# 便捷函数，用于快速使用重试逻辑
def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Optional[tuple[Type[Exception], ...]] = None,
    non_retryable_exceptions: Optional[tuple[Type[Exception], ...]] = None
):
    """
    重试装饰器工厂函数
    
    Args:
        max_attempts: 最大重试次数
        base_delay: 基础延迟时间
        max_delay: 最大延迟时间
        retryable_exceptions: 可重试的异常类型
        non_retryable_exceptions: 不可重试的异常类型
        
    Returns:
        装饰器函数
    """
    retry_handler = RetryHandler(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        retryable_exceptions=retryable_exceptions,
        non_retryable_exceptions=non_retryable_exceptions
    )
    
    return retry_handler