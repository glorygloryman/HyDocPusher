"""
重试处理器单元测试
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Any

from hydocpusher.client.retry_handler import RetryHandler, with_retry, RetryExhaustedException
from hydocpusher.exceptions.custom_exceptions import (
    ArchiveClientException,
    ConnectionException
)


class TestRetryHandler:
    """重试处理器测试类"""
    
    def test_init_default_values(self):
        """测试默认初始化值"""
        handler = RetryHandler()
        
        assert handler.max_attempts == 3
        assert handler.base_delay == 1.0
        assert handler.max_delay == 60.0
        assert handler.exponential_base == 2.0
        assert handler.jitter is True
        assert ConnectionException in handler.retryable_exceptions
        assert ValueError in handler.non_retryable_exceptions
    
    def test_init_custom_values(self):
        """测试自定义初始化值"""
        handler = RetryHandler(
            max_attempts=5,
            base_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=False
        )
        
        assert handler.max_attempts == 5
        assert handler.base_delay == 0.5
        assert handler.max_delay == 30.0
        assert handler.exponential_base == 3.0
        assert handler.jitter is False
    
    def test_calculate_delay_basic(self):
        """测试基础延迟计算"""
        handler = RetryHandler(base_delay=1.0, exponential_base=2.0, jitter=False)
        
        # 第一次重试：1 * 2^0 = 1.0
        assert handler._calculate_delay(1) == 1.0
        # 第二次重试：1 * 2^1 = 2.0
        assert handler._calculate_delay(2) == 2.0
        # 第三次重试：1 * 2^2 = 4.0
        assert handler._calculate_delay(3) == 4.0
    
    def test_calculate_delay_max_limit(self):
        """测试最大延迟限制"""
        handler = RetryHandler(base_delay=10.0, max_delay=15.0, exponential_base=2.0, jitter=False)
        
        # 第一次：10 * 2^0 = 10.0 (小于15)
        assert handler._calculate_delay(1) == 10.0
        # 第二次：10 * 2^1 = 20.0 (大于15，被限制为15)
        assert handler._calculate_delay(2) == 15.0
        # 第三次：10 * 2^2 = 40.0 (大于15，被限制为15)
        assert handler._calculate_delay(3) == 15.0
    
    def test_calculate_delay_with_jitter(self):
        """测试带抖动的延迟计算"""
        handler = RetryHandler(base_delay=1.0, jitter=True)
        
        delay = handler._calculate_delay(1)
        # 抖动范围：±10%，即 0.9 到 1.1
        assert 0.9 <= delay <= 1.1
    
    def test_is_retryable_exception_retryable_types(self):
        """测试可重试异常类型判断"""
        handler = RetryHandler()
        
        # 默认可重试异常
        assert handler._is_retryable_exception(ConnectionException("test")) is True
        assert handler._is_retryable_exception(ConnectionError("test")) is True
        assert handler._is_retryable_exception(TimeoutError("test")) is True
        assert handler._is_retryable_exception(ArchiveClientException("test")) is True
    
    def test_is_retryable_exception_non_retryable_types(self):
        """测试不可重试异常类型判断"""
        handler = RetryHandler()
        
        # 默认不可重试异常
        assert handler._is_retryable_exception(ValueError("test")) is False
        assert handler._is_retryable_exception(TypeError("test")) is False
        assert handler._is_retryable_exception(AttributeError("test")) is False
        assert handler._is_retryable_exception(PermissionError("test")) is False
    
    def test_is_retryable_exception_archive_client_auth_failure(self):
        """测试ArchiveClientException认证失败判断"""
        handler = RetryHandler()
        
        # 认证失败不应该重试
        auth_exception = ArchiveClientException("Authentication failed")
        assert handler._is_retryable_exception(auth_exception) is False
        
        # 权限错误不应该重试
        permission_exception = ArchiveClientException("Permission denied")
        assert handler._is_retryable_exception(permission_exception) is False
        
        # 通用ArchiveClientException应该重试
        generic_exception = ArchiveClientException("Server error")
        assert handler._is_retryable_exception(generic_exception) is True
    
    def test_execute_with_retry_sync_success_first_attempt(self):
        """测试同步重试：第一次尝试成功"""
        handler = RetryHandler()
        
        def success_func():
            return "success"
        
        result = handler.execute_with_retry_sync(success_func)
        assert result == "success"
    
    def test_execute_with_retry_sync_success_after_retries(self):
        """测试同步重试：重试后成功"""
        handler = RetryHandler(max_attempts=3, base_delay=0.1)
        
        call_count = 0
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionException(f"Attempt {call_count} failed")
            return f"success on attempt {call_count}"
        
        result = handler.execute_with_retry_sync(fail_then_succeed)
        assert result == "success on attempt 3"
        assert call_count == 3
    
    def test_execute_with_retry_sync_max_attempts_exceeded(self):
        """测试同步重试：超过最大重试次数"""
        handler = RetryHandler(max_attempts=2, base_delay=0.1)
        
        def always_fail():
            raise ConnectionException("Always fails")
        
        with pytest.raises(RetryExhaustedException) as exc_info:
            handler.execute_with_retry_sync(always_fail)
        
        assert "Function failed after 2 attempts" in str(exc_info.value)
        assert exc_info.value.retry_count == 2
    
    def test_execute_with_retry_sync_non_retryable_exception(self):
        """测试同步重试：不可重试异常"""
        handler = RetryHandler()
        
        def fail_with_value_error():
            raise ValueError("Non-retryable error")
        
        with pytest.raises(ValueError, match="Non-retryable error"):
            handler.execute_with_retry_sync(fail_with_value_error)
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_async_success_first_attempt(self):
        """测试异步重试：第一次尝试成功"""
        handler = RetryHandler()
        
        async def success_func():
            return "async success"
        
        result = await handler.execute_with_retry_async(success_func)
        assert result == "async success"
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_async_success_after_retries(self):
        """测试异步重试：重试后成功"""
        handler = RetryHandler(max_attempts=3, base_delay=0.1)
        
        call_count = 0
        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionException(f"Attempt {call_count} failed")
            return f"success on attempt {call_count}"
        
        result = await handler.execute_with_retry_async(fail_then_succeed)
        assert result == "success on attempt 3"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_async_max_attempts_exceeded(self):
        """测试异步重试：超过最大重试次数"""
        handler = RetryHandler(max_attempts=2, base_delay=0.1)
        
        async def always_fail():
            raise ConnectionException("Always fails")
        
        with pytest.raises(RetryExhaustedException) as exc_info:
            await handler.execute_with_retry_async(always_fail)
        
        assert "Function failed after 2 attempts" in str(exc_info.value)
        assert exc_info.value.retry_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_async_non_retryable_exception(self):
        """测试异步重试：不可重试异常"""
        handler = RetryHandler()
        
        async def fail_with_value_error():
            raise ValueError("Non-retryable error")
        
        with pytest.raises(ValueError, match="Non-retryable error"):
            await handler.execute_with_retry_async(fail_with_value_error)
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_async_sync_function(self):
        """测试异步重试：同步函数在异步环境中运行"""
        handler = RetryHandler()
        
        def sync_func():
            return "sync function result"
        
        result = await handler.execute_with_retry_async(sync_func)
        assert result == "sync function result"
    
    def test_decorator_sync_function(self):
        """测试装饰器模式：同步函数"""
        handler = RetryHandler(max_attempts=2, base_delay=0.1)
        
        call_count = 0
        @handler
        def decorated_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionException("First attempt fails")
            return "success"
        
        result = decorated_func()
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_decorator_async_function(self):
        """测试装饰器模式：异步函数"""
        handler = RetryHandler(max_attempts=2, base_delay=0.1)
        
        call_count = 0
        @handler
        async def decorated_async_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionException("First attempt fails")
            return "async success"
        
        result = await decorated_async_func()
        assert result == "async success"
        assert call_count == 2
    
    def test_with_retry_decorator_factory(self):
        """测试with_retry装饰器工厂函数"""
        
        @with_retry(max_attempts=2, base_delay=0.1)
        def decorated_func():
            return "factory decorator result"
        
        result = decorated_func()
        assert result == "factory decorator result"
    
    @pytest.mark.asyncio
    async def test_with_retry_decorator_factory_async(self):
        """测试with_retry装饰器工厂函数：异步版本"""
        
        @with_retry(max_attempts=2, base_delay=0.1)
        async def decorated_async_func():
            return "factory decorator async result"
        
        result = await decorated_async_func()
        assert result == "factory decorator async result"
    
    def test_delay_timing_accuracy(self):
        """测试延迟时间准确性"""
        handler = RetryHandler(base_delay=0.1, jitter=False)
        
        start_time = time.time()
        
        def failing_func():
            raise ConnectionException("Test exception")
        
        try:
            handler.execute_with_retry_sync(failing_func)
        except RetryExhaustedException:
            pass
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # 期望的延迟：第一次立即失败，第二次延迟0.1秒，第三次延迟0.2秒
        # 总延迟时间应该至少是0.3秒
        assert elapsed >= 0.3
    
    def test_custom_retryable_exceptions(self):
        """测试自定义可重试异常"""
        handler = RetryHandler(
            retryable_exceptions=(ValueError, TypeError),
            non_retryable_exceptions=(ConnectionException,)
        )
        
        # ValueError应该是可重试的
        assert handler._is_retryable_exception(ValueError("test")) is True
        # ConnectionException应该是不可重试的（自定义设置）
        assert handler._is_retryable_exception(ConnectionException("test")) is False
    
    def test_logging_during_retry(self, caplog):
        """测试重试过程中的日志记录"""
        handler = RetryHandler(max_attempts=2, base_delay=0.1)
        
        def failing_func():
            raise ConnectionException("Test failure")
        
        with caplog.at_level("DEBUG"):
            try:
                handler.execute_with_retry_sync(failing_func)
            except RetryExhaustedException:
                pass
        
        # 检查日志中是否包含重试相关信息
        log_messages = [record.message for record in caplog.records]
        assert any("Attempt 1/2 executing function" in msg for msg in log_messages)
        assert any("Attempt 1 failed with retryable exception" in msg for msg in log_messages)
        assert any("Retrying in" in msg for msg in log_messages)
        assert any("Max attempts (2) reached" in msg for msg in log_messages)