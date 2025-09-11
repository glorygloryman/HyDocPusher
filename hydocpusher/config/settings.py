"""
应用配置管理模块
使用Pydantic Settings管理所有应用配置
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
import os


class PulsarConfig(BaseModel):
    """Pulsar连接配置"""
    cluster_url: str = Field(default="pulsar://localhost:6650", env="PULSAR_CLUSTER_URL")
    topic: str = Field(default="persistent://public/default/content-publish", env="PULSAR_TOPIC")
    subscription: str = Field(default="hydocpusher-subscription", env="PULSAR_SUBSCRIPTION")
    dead_letter_topic: str = Field(
        default="persistent://public/default/hydocpusher-dlq", 
        env="PULSAR_DEAD_LETTER_TOPIC"
    )
    
    @field_validator('cluster_url')
    @classmethod
    def validate_cluster_url(cls, v):
        if not v or not v.startswith(('pulsar://', 'pulsar+ssl://')):
            raise ValueError("Pulsar cluster URL must start with 'pulsar://' or 'pulsar+ssl://'")
        return v


class ArchiveConfig(BaseModel):
    """档案系统配置"""
    api_url: str = Field(default="http://localhost:8080", env="ARCHIVE_API_URL")
    timeout: int = Field(default=30000, env="ARCHIVE_TIMEOUT")
    retry_max_attempts: int = Field(default=3, env="ARCHIVE_RETRY_MAX_ATTEMPTS")
    retry_delay: int = Field(default=60000, env="ARCHIVE_RETRY_DELAY")
    app_id: str = Field(default="NEWS", env="ARCHIVE_APP_ID")
    app_token: str = Field(default="TmV3cytJbnRlcmZhY2U=", env="ARCHIVE_APP_TOKEN")
    company_name: str = Field(default="云南省能源投资集团有限公司", env="ARCHIVE_COMPANY_NAME")
    archive_type: str = Field(default="17", env="ARCHIVE_TYPE")
    domain: str = Field(default="www.cnyeig.com", env="DOMAIN")
    retention_period: int = Field(default=30, env="ARCHIVE_RETENTION_PERIOD")
    
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


class ClassificationConfig(BaseModel):
    """分类映射配置"""
    rules_file: str = Field(default="config/classification-rules.yaml", env="CLASSIFICATION_RULES_FILE")
    default_classfyname: str = Field(default="其他", env="DEFAULT_CLASSFYNAME")
    default_classfy: str = Field(default="QT", env="DEFAULT_CLASSFY")


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(
        default="%(asctime)s [%(levelname)s] %(name)s: %(message)s", 
        env="LOG_FORMAT"
    )
    file_path: Optional[str] = Field(default=None, env="LOG_FILE_PATH")
    max_file_size: str = Field(default="10MB", env="LOG_MAX_FILE_SIZE")
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")


class AppConfig(BaseSettings):
    """应用主配置类"""
    
    # 服务配置
    server_host: str = Field(default="0.0.0.0", env="SERVER_HOST")
    server_port: int = Field(default=8080, env="SERVER_PORT")
    
    # 子配置
    pulsar: PulsarConfig = Field(default_factory=PulsarConfig)
    archive: ArchiveConfig = Field(default_factory=ArchiveConfig, description="Archive system configuration")
    classification: ClassificationConfig = Field(default_factory=ClassificationConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # 应用配置
    app_name: str = Field(default="HyDocPusher", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # 性能配置
    max_concurrent_messages: int = Field(default=100, env="MAX_CONCURRENT_MESSAGES")
    message_processing_timeout: int = Field(default=300000, env="MESSAGE_PROCESSING_TIMEOUT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
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
    _config_instance = AppConfig.create_from_env()
    _config_instance.validate_required_configs()
    return _config_instance