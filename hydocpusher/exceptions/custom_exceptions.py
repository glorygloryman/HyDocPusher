"""
自定义异常模块
定义HyDocPusher项目中使用的所有自定义异常类
"""


class HyDocPusherException(Exception):
    """HyDocPusher基础异常类"""
    
    def __init__(self, message: str, error_code: str = None, cause: Exception = None):
        """
        初始化异常
        
        Args:
            message: 错误信息
            error_code: 错误代码
            cause: 原始异常（用于异常链）
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.cause = cause
        
        # 设置异常链
        if cause is not None:
            self.__cause__ = cause
        
    def __str__(self) -> str:
        """返回格式化的错误信息"""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigurationException(HyDocPusherException):
    """配置相关异常"""
    
    def __init__(self, message: str, cause: Exception = None):
        super().__init__(message, "CONFIG_ERROR", cause)


class MessageProcessException(HyDocPusherException):
    """消息处理异常"""
    
    def __init__(self, message: str, cause: Exception = None):
        super().__init__(message, "MESSAGE_PROCESS_ERROR", cause)


class DataTransformException(HyDocPusherException):
    """数据转换异常"""
    
    def __init__(self, message: str, cause: Exception = None):
        super().__init__(message, "DATA_TRANSFORM_ERROR", cause)


class ArchiveClientException(HyDocPusherException):
    """档案系统客户端异常"""
    
    def __init__(self, message: str, cause: Exception = None):
        super().__init__(message, "ARCHIVE_CLIENT_ERROR", cause)


class ValidationException(HyDocPusherException):
    """数据验证异常"""
    
    def __init__(self, message: str, cause: Exception = None):
        super().__init__(message, "VALIDATION_ERROR", cause)


class RetryExhaustedException(HyDocPusherException):
    """重试次数耗尽异常"""
    
    def __init__(self, message: str, error_code: str = None, cause: Exception = None, retry_count: int = None):
        super().__init__(message, error_code or "RETRY_EXHAUSTED", cause)
        self.retry_count = retry_count


class ConnectionException(HyDocPusherException):
    """连接异常"""
    
    def __init__(self, message: str, cause: Exception = None):
        super().__init__(message, "CONNECTION_ERROR", cause)