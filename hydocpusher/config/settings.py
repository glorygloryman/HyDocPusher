"""
应用配置管理模块
使用Pydantic Settings管理所有应用配置
"""

from typing import Optional, Annotated
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class PulsarConfig(BaseSettings):
    """Pulsar连接配置"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="PULSAR_"
    )
    
    cluster_url: str = Field(default="pulsar://localhost:6650")
    topic: str = Field(default="persistent://public/default/content-publish")
    subscription: str = Field(default="hydocpusher-subscription")
    dead_letter_topic: str = Field(default="user-to-pretreat")
    
    # 认证配置
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    
    # 租户和命名空间
    tenant: str = Field(default="bigdata")
    namespace: str = Field(default="text")
    
    # 超时配置
    connection_timeout: int = Field(default=30000)
    operation_timeout: int = Field(default=30000)
    
    @field_validator('cluster_url')
    @classmethod
    def validate_cluster_url(cls, v):
        # 支持HTTP URL，自动转换为pulsar://
        if v.startswith('http://'):
            v = v.replace('http://', 'pulsar://')
        elif v.startswith('https://'):
            v = v.replace('https://', 'pulsar+ssl://')
        
        if not v or not v.startswith(('pulsar://', 'pulsar+ssl://')):
            raise ValueError("Pulsar cluster URL must start with 'pulsar://' or 'pulsar+ssl://'")
        return v
    
    @field_validator('connection_timeout', 'operation_timeout')
    @classmethod
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v
    
    def get_full_topic_name(self) -> str:
        """获取完整的Topic名称"""
        # 如果topic已经是完整格式，直接返回
        if self.topic.startswith('persistent://'):
            return self.topic
        # 否则构建完整的topic名称
        topic_name = self.topic.split('/')[-1]  # 提取最后的topic名称部分
        return f"persistent://{self.tenant}/{self.namespace}/{topic_name}"
    
    def get_full_dead_letter_topic_name(self) -> str:
        """获取完整的死信队列Topic名称"""
        if self.dead_letter_topic.startswith('persistent://'):
            return self.dead_letter_topic
        dlq_topic = self.dead_letter_topic.split('/')[-1]
        return f"persistent://{self.tenant}/{self.namespace}/{dlq_topic}"
    
    def has_authentication(self) -> bool:
        """检查是否配置了认证信息"""
        return bool(self.username and self.password)


class ArchiveConfig(BaseSettings):
    """档案系统配置"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="ARCHIVE_"
    )
    api_url: str = Field(default="http://localhost:8080")
    base_url: str = Field(default="http://localhost:8080")  # 添加base_url字段作为api_url的别名
    timeout: int = Field(default=30000)
    retry_max_attempts: int = Field(default=3)
    retry_delay: int = Field(default=60000)
    app_id: str = Field(default="NEWS")
    app_token: str = Field(default="TmV3cytJbnRlcmZhY2U=")
    company_name: str = Field(default="云南省能源投资集团有限公司")
    archive_type: str = Field(default="17")
    domain: str = Field(default="www.cnyeig.com")
    retention_period: int = Field(default=30)
    
    @field_validator('api_url')
    @classmethod
    def validate_api_url(cls, v):
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError("Archive API URL must start with 'http://' or 'https://'")
        return v
    
    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v):
        if not v or not v.strip():
            raise ValueError("Domain cannot be empty")
        # 简单的域名格式验证
        import re
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, v):
            raise ValueError(f"Invalid domain format: {v}")
        return v.strip()
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v
    
    @field_validator('retention_period')
    @classmethod
    def validate_retention_period(cls, v):
        if v <= 0:
            raise ValueError("Retention period must be positive")
        return v


class ClassificationConfig(BaseSettings):
    """分类映射配置"""
    rules_file: str = Field(default="config/classification-rules.yaml")
    default_classfyname: str = Field(default="其他")
    default_classfy: str = Field(default="QT")


class LoggingConfig(BaseSettings):
    """日志配置"""
    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    file_path: Optional[str] = Field(default=None)
    max_file_size: str = Field(default="10MB")
    backup_count: int = Field(default=5)


class AppConfig(BaseSettings):
    """应用主配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter='__'
    )
    
    # 服务器配置
    server_host: str = "0.0.0.0"
    server_port: int = 8080
    
    # 各模块配置 - 使用工厂方法创建，确保环境变量被正确读取
    pulsar: PulsarConfig = Field(default_factory=lambda: PulsarConfig())
    archive: ArchiveConfig = Field(default_factory=lambda: ArchiveConfig())
    classification: ClassificationConfig = Field(default_factory=lambda: ClassificationConfig())
    logging: LoggingConfig = Field(default_factory=lambda: LoggingConfig())
    
    # 应用配置
    app_name: str = "HyDocPusher"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 性能配置
    max_concurrent_messages: int = 100
    message_processing_timeout: int = 300000
    batch_size: int = Field(default=100)  # 添加batch_size字段
    
    @field_validator('server_port')
    @classmethod
    def validate_server_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Server port must be between 1 and 65535")
        return v
    
    @field_validator('max_concurrent_messages')
    @classmethod
    def validate_max_concurrent_messages(cls, v):
        if v <= 0:
            raise ValueError("Max concurrent messages must be positive")
        return v
    
    @field_validator('message_processing_timeout')
    @classmethod
    def validate_message_processing_timeout(cls, v):
        if v <= 0:
            raise ValueError("Message processing timeout must be positive")
        return v
    
    def get_pulsar_connection_string(self) -> str:
        """获取Pulsar连接字符串"""
        return self.pulsar.cluster_url
    
    def get_archive_headers(self) -> dict:
        """获取档案系统请求头"""
        return {
            "Content-Type": "application/json",
            "User-Agent": f"{self.app_name}/{self.app_version}"
        }
    
    def is_debug_enabled(self) -> bool:
        """检查是否启用调试模式"""
        return self.debug
    
    def get_log_level(self) -> str:
        """获取日志级别"""
        return self.logging.level.upper()
    
    @classmethod
    def create_from_env(cls) -> 'AppConfig':
        """从环境变量创建配置实例"""
        try:
            return cls()
        except Exception as e:
            from ..exceptions.custom_exceptions import ConfigurationException
            raise ConfigurationException(f"Failed to create configuration: {str(e)}", cause=e)
    
    def validate_required_configs(self) -> None:
        """验证必需的配置项"""
        required_configs = [
            ('archive.api_url', self.archive.api_url),
            ('archive.app_token', self.archive.app_token),
        ]
        
        missing_configs = []
        for config_name, config_value in required_configs:
            if not config_value:
                missing_configs.append(config_name)
        
        if missing_configs:
            from ..exceptions.custom_exceptions import ConfigurationException
            raise ConfigurationException(f"Missing required configurations: {', '.join(missing_configs)}")


# 全局配置实例
_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig.create_from_env()
        _config_instance.validate_required_configs()
    return _config_instance


def reload_config() -> AppConfig:
    """重新加载配置"""
    global _config_instance
    _config_instance = None  # 清空缓存
    _config_instance = AppConfig.create_from_env()
    _config_instance.validate_required_configs()
    return _config_instance