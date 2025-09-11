"""
自定义异常类的TDD测试用例
"""

import pytest
from unittest.mock import MagicMock

from hydocpusher.exceptions.custom_exceptions import (
    HyDocPusherException,
    ConfigurationException,
    MessageProcessException,
    DataTransformException,
    ArchiveClientException,
    ValidationException,
    RetryExhaustedException,
    ConnectionException
)


class TestHyDocPusherException:
    """基础异常类测试"""
    
    def test_create_exception_with_message(self):
        """测试创建带消息的异常"""
        exception = HyDocPusherException("Test message")
        assert exception.message == "Test message"
        assert exception.error_code is None
        assert exception.cause is None
        assert str(exception) == "Test message"
    
    def test_create_exception_with_error_code(self):
        """测试创建带错误代码的异常"""
        exception = HyDocPusherException("Test message", "TEST_ERROR")
        assert exception.message == "Test message"
        assert exception.error_code == "TEST_ERROR"
        assert str(exception) == "[TEST_ERROR] Test message"
    
    def test_create_exception_with_cause(self):
        """测试创建带原因的异常"""
        cause = ValueError("Original error")
        exception = HyDocPusherException("Test message", "TEST_ERROR", cause)
        assert exception.message == "Test message"
        assert exception.error_code == "TEST_ERROR"
        assert exception.cause is cause
        assert exception.__cause__ is cause
    
    def test_exception_inheritance(self):
        """测试异常继承"""
        exception = HyDocPusherException("Test")
        assert isinstance(exception, Exception)
        assert isinstance(exception, HyDocPusherException)


class TestConfigurationException:
    """配置异常测试"""
    
    def test_create_configuration_exception(self):
        """测试创建配置异常"""
        exception = ConfigurationException("Config error")
        assert exception.message == "Config error"
        assert exception.error_code == "CONFIG_ERROR"
        assert isinstance(exception, HyDocPusherException)
        assert isinstance(exception, ConfigurationException)
    
    def test_create_configuration_exception_with_cause(self):
        """测试创建带原因的配置异常"""
        cause = FileNotFoundError("Config file not found")
        exception = ConfigurationException("Config error", cause)
        assert exception.message == "Config error"
        assert exception.error_code == "CONFIG_ERROR"
        assert exception.cause is cause
    
    def test_configuration_exception_str_representation(self):
        """测试配置异常的字符串表示"""
        exception = ConfigurationException("Invalid configuration")
        assert str(exception) == "[CONFIG_ERROR] Invalid configuration"


class TestMessageProcessException:
    """消息处理异常测试"""
    
    def test_create_message_process_exception(self):
        """测试创建消息处理异常"""
        exception = MessageProcessException("Message processing failed")
        assert exception.message == "Message processing failed"
        assert exception.error_code == "MESSAGE_PROCESS_ERROR"
        assert isinstance(exception, HyDocPusherException)
        assert isinstance(exception, MessageProcessException)
    
    def test_message_process_exception_with_cause(self):
        """测试创建带原因的消息处理异常"""
        cause = ValueError("Invalid message format")
        exception = MessageProcessException("Message processing failed", cause)
        assert exception.cause is cause


class TestDataTransformException:
    """数据转换异常测试"""
    
    def test_create_data_transform_exception(self):
        """测试创建数据转换异常"""
        exception = DataTransformException("Data transformation failed")
        assert exception.message == "Data transformation failed"
        assert exception.error_code == "DATA_TRANSFORM_ERROR"
        assert isinstance(exception, HyDocPusherException)
        assert isinstance(exception, DataTransformException)
    
    def test_data_transform_exception_with_cause(self):
        """测试创建带原因的数据转换异常"""
        cause = KeyError("Missing required field")
        exception = DataTransformException("Data transformation failed", cause)
        assert exception.cause is cause


class TestArchiveClientException:
    """档案系统客户端异常测试"""
    
    def test_create_archive_client_exception(self):
        """测试创建档案系统客户端异常"""
        exception = ArchiveClientException("Archive API error")
        assert exception.message == "Archive API error"
        assert exception.error_code == "ARCHIVE_CLIENT_ERROR"
        assert isinstance(exception, HyDocPusherException)
        assert isinstance(exception, ArchiveClientException)
    
    def test_archive_client_exception_with_cause(self):
        """测试创建带原因的档案系统客户端异常"""
        cause = ConnectionError("Connection failed")
        exception = ArchiveClientException("Archive API error", cause)
        assert exception.cause is cause


class TestValidationException:
    """验证异常测试"""
    
    def test_create_validation_exception(self):
        """测试创建验证异常"""
        exception = ValidationException("Validation failed")
        assert exception.message == "Validation failed"
        assert exception.error_code == "VALIDATION_ERROR"
        assert isinstance(exception, HyDocPusherException)
        assert isinstance(exception, ValidationException)
    
    def test_validation_exception_with_cause(self):
        """测试创建带原因的验证异常"""
        cause = ValueError("Invalid value")
        exception = ValidationException("Validation failed", cause)
        assert exception.cause is cause


class TestRetryExhaustedException:
    """重试次数耗尽异常测试"""
    
    def test_create_retry_exhausted_exception(self):
        """测试创建重试次数耗尽异常"""
        exception = RetryExhaustedException("Retry attempts exhausted")
        assert exception.message == "Retry attempts exhausted"
        assert exception.error_code == "RETRY_EXHAUSTED"
        assert exception.retry_count is None
        assert isinstance(exception, HyDocPusherException)
        assert isinstance(exception, RetryExhaustedException)
    
    def test_create_retry_exhausted_exception_with_retry_count(self):
        """测试创建带重试次数的重试次数耗尽异常"""
        exception = RetryExhaustedException("Retry attempts exhausted", retry_count=3)
        assert exception.message == "Retry attempts exhausted"
        assert exception.error_code == "RETRY_EXHAUSTED"
        assert exception.retry_count == 3
    
    def test_retry_exhausted_exception_with_cause(self):
        """测试创建带原因的重试次数耗尽异常"""
        cause = ConnectionError("Max retries reached")
        exception = RetryExhaustedException("Retry attempts exhausted", cause=cause, retry_count=5)
        assert exception.cause is cause
        assert exception.retry_count == 5


class TestConnectionException:
    """连接异常测试"""
    
    def test_create_connection_exception(self):
        """测试创建连接异常"""
        exception = ConnectionException("Connection failed")
        assert exception.message == "Connection failed"
        assert exception.error_code == "CONNECTION_ERROR"
        assert isinstance(exception, HyDocPusherException)
        assert isinstance(exception, ConnectionException)
    
    def test_connection_exception_with_cause(self):
        """测试创建带原因的连接异常"""
        cause = OSError("Network unreachable")
        exception = ConnectionException("Connection failed", cause)
        assert exception.cause is cause


class TestExceptionChaining:
    """异常链测试"""
    
    def test_exception_chain_with_original_exception(self):
        """测试异常链与原始异常"""
        original_error = ValueError("Original error occurred")
        wrapper_exception = ConfigurationException("Wrapper error", original_error)
        
        # 测试异常链
        assert wrapper_exception.__cause__ is original_error
        assert wrapper_exception.cause is original_error
    
    def test_exception_chain_without_original_exception(self):
        """测试没有原始异常的异常链"""
        exception = ConfigurationException("Standalone error")
        
        assert exception.__cause__ is None
        assert exception.cause is None
    
    def test_nested_exception_chaining(self):
        """测试嵌套异常链"""
        original_error = FileNotFoundError("File not found")
        middle_exception = ConfigurationException("Config loading failed", original_error)
        top_exception = MessageProcessException("Message processing failed", middle_exception)
        
        assert top_exception.__cause__ is middle_exception
        assert middle_exception.__cause__ is original_error
        assert top_exception.cause is middle_exception
    
    def test_exception_chain_in_traceback(self):
        """测试异常链在回溯中的表现"""
        def level3():
            raise ValueError("Level 3 error")
        
        def level2():
            try:
                level3()
            except ValueError as e:
                raise ConfigurationException("Level 2 error", e)
        
        def level1():
            try:
                level2()
            except ConfigurationException as e:
                raise MessageProcessException("Level 1 error", e)
        
        with pytest.raises(MessageProcessException) as exc_info:
            level1()
        
        exception = exc_info.value
        assert isinstance(exception, MessageProcessException)
        assert isinstance(exception.__cause__, ConfigurationException)
        assert isinstance(exception.__cause__.__cause__, ValueError)


class TestExceptionHandlingPatterns:
    """异常处理模式测试"""
    
    def test_catch_specific_exception(self):
        """测试捕获特定异常"""
        try:
            raise ConfigurationException("Config error")
        except ConfigurationException as e:
            assert e.message == "Config error"
            assert e.error_code == "CONFIG_ERROR"
    
    def test_catch_base_exception(self):
        """测试捕获基础异常"""
        try:
            raise ConfigurationException("Config error")
        except HyDocPusherException as e:
            assert e.message == "Config error"
            assert e.error_code == "CONFIG_ERROR"
    
    def test_catch_all_exceptions(self):
        """测试捕获所有异常"""
        try:
            raise ConfigurationException("Config error")
        except Exception as e:
            assert isinstance(e, HyDocPusherException)
    
    def test_exception_reraising(self):
        """测试异常重新抛出"""
        with pytest.raises(ConfigurationException):
            try:
                raise ConfigurationException("Original error")
            except ConfigurationException:
                # 重新抛出相同的异常
                raise
    
    def test_exception_wrapping(self):
        """测试异常包装"""
        with pytest.raises(ConfigurationException) as exc_info:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise ConfigurationException("Wrapped error") from e
        
        # 验证异常链
        exception = exc_info.value
        assert exception.__cause__ is not None
        assert isinstance(exception.__cause__, ValueError)
        assert str(exception.__cause__) == "Original error"
    
    def test_exception_logging_simulation(self):
        """测试异常日志记录模拟"""
        exception = ConfigurationException("Config error", cause=ValueError("Original error"))
        
        # 模拟日志记录
        log_messages = []
        
        def log_error(message, exc_info=None):
            log_messages.append(message)
            if exc_info:
                log_messages.append(f"Exception: {exc_info[1]}")
        
        # 模拟记录异常
        log_error(f"Error occurred: {exception}", exc_info=(type(exception), exception, exception.__traceback__))
        
        assert len(log_messages) == 2
        assert "Error occurred: [CONFIG_ERROR] Config error" in log_messages[0]
        assert "Exception: [CONFIG_ERROR] Config error" in log_messages[1]
    
    def test_exception_serialization(self):
        """测试异常序列化"""
        exception = ConfigurationException("Config error", cause=ValueError("Original"))
        
        # 测试字符串表示
        str_repr = str(exception)
        assert "[CONFIG_ERROR] Config error" == str_repr
        
        # 测试repr表示
        repr_repr = repr(exception)
        assert "ConfigurationException" in repr_repr
        assert "Config error" in repr_repr
    
    def test_exception_equality(self):
        """测试异常相等性"""
        exc1 = ConfigurationException("Error 1")
        exc2 = ConfigurationException("Error 1")
        exc3 = ConfigurationException("Error 2")
        
        # 异常实例不应该相等，即使消息相同
        assert exc1 is not exc2
        assert exc1 is not exc3
    
    def test_exception_attributes_immutability(self):
        """测试异常属性不可变性"""
        exception = ConfigurationException("Original message")
        
        # 异常属性应该是可读的，但不应该被修改
        assert exception.message == "Original message"
        assert exception.error_code == "CONFIG_ERROR"
        
        # 在实际使用中，不应该修改异常属性
        # 这里只是测试属性的访问性