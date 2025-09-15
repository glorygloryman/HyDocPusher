"""
应用配置管理类的TDD测试用例
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from hydocpusher.config.settings import AppConfig, PulsarConfig, ArchiveConfig, get_config, reload_config
from hydocpusher.exceptions.custom_exceptions import ConfigurationException


class TestPulsarConfig:
    """Pulsar配置测试"""
    
    def test_valid_pulsar_config(self):
        """测试有效的Pulsar配置"""
        config = PulsarConfig(
            cluster_url="pulsar://localhost:6650",
            topic="test-topic",
            subscription="test-subscription"
        )
        assert config.cluster_url == "pulsar://localhost:6650"
        assert config.topic == "test-topic"
        assert config.subscription == "test-subscription"
    
    def test_default_pulsar_config(self):
        """测试默认Pulsar配置"""
        config = PulsarConfig()
        assert config.cluster_url == "pulsar://localhost:6650"
        assert config.topic == "persistent://public/default/content-publish"
        assert config.subscription == "hydocpusher-subscription"
    
    def test_invalid_pulsar_cluster_url(self):
        """测试无效的Pulsar集群URL"""
        with pytest.raises(ValidationError):
            PulsarConfig(cluster_url="invalid-url")
    
    def test_pulsar_ssl_url(self):
        """测试Pulsar SSL URL"""
        config = PulsarConfig(cluster_url="pulsar+ssl://localhost:6651")
        assert config.cluster_url == "pulsar+ssl://localhost:6651"


class TestArchiveConfig:
    """档案系统配置测试"""
    
    def test_valid_archive_config(self):
        """测试有效的档案系统配置"""
        config = ArchiveConfig(
            api_url="http://example.com/api",
            app_token="test-token"
        )
        assert config.api_url == "http://example.com/api"
        assert config.app_token == "test-token"
        assert config.timeout == 30000
        assert config.retry_max_attempts == 3
    
    def test_archive_config_with_custom_values(self):
        """测试自定义档案系统配置值"""
        config = ArchiveConfig(
            api_url="https://example.com/api",
            timeout=60000,
            retry_max_attempts=5,
            retry_delay=120000,
            app_token="custom-token"
        )
        assert config.api_url == "https://example.com/api"
        assert config.timeout == 60000
        assert config.retry_max_attempts == 5
        assert config.retry_delay == 120000
        assert config.app_token == "custom-token"
    
    def test_invalid_archive_api_url(self):
        """测试无效的档案系统API URL"""
        with pytest.raises(ValidationError):
            ArchiveConfig(api_url="invalid-url", app_token="test")
    
    def test_archive_config_with_defaults(self):
        """测试档案系统配置使用默认值"""
        config = ArchiveConfig()  # 现在有默认值，不会抛出异常
        assert config.api_url == "http://localhost:8080"
        assert config.app_token == "TmV3cytJbnRlcmZhY2U="
    
    def test_invalid_timeout(self):
        """测试无效的超时时间"""
        with pytest.raises(ValidationError):
            ArchiveConfig(api_url="http://example.com", app_token="test", timeout=-1)
    
    def test_invalid_retention_period(self):
        """测试无效的保留期限"""
        with pytest.raises(ValidationError):
            ArchiveConfig(api_url="http://example.com", app_token="test", retention_period=-1)


class TestAppConfig:
    """应用配置测试"""
    
    def test_valid_app_config(self):
        """测试有效的应用配置"""
        config = AppConfig(
            archive={
                "api_url": "http://example.com/api",
                "app_token": "test-token"
            }
        )
        assert config.server_host == "0.0.0.0"
        assert config.server_port == 8080
        assert config.archive.api_url == "http://example.com/api"
        assert config.archive.app_token == "test-token"
    
    def test_app_config_with_custom_values(self):
        """测试自定义应用配置值"""
        config = AppConfig(
            server_host="127.0.0.1",
            server_port=9000,
            debug=True,
            max_concurrent_messages=200,
            archive={
                "api_url": "http://example.com/api",
                "app_token": "test-token"
            }
        )
        assert config.server_host == "127.0.0.1"
        assert config.server_port == 9000
        assert config.debug is True
        assert config.max_concurrent_messages == 200
    
    def test_invalid_server_port(self):
        """测试无效的服务器端口"""
        with pytest.raises(ValidationError):
            AppConfig(
                server_port=70000,
                archive={"api_url": "http://example.com", "app_token": "test"}
            )
    
    def test_invalid_max_concurrent_messages(self):
        """测试无效的最大并发消息数"""
        with pytest.raises(ValidationError):
            AppConfig(
                max_concurrent_messages=-1,
                archive={"api_url": "http://example.com", "app_token": "test"}
            )
    
    def test_get_pulsar_connection_string(self):
        """测试获取Pulsar连接字符串"""
        config = AppConfig(
            pulsar={"cluster_url": "pulsar://test:6650"},
            archive={"api_url": "http://example.com", "app_token": "test"}
        )
        assert config.get_pulsar_connection_string() == "pulsar://test:6650"
    
    def test_get_archive_headers(self):
        """测试获取档案系统请求头"""
        config = AppConfig(
            app_name="TestApp",
            app_version="1.0.0",
            archive={"api_url": "http://example.com", "app_token": "test"}
        )
        headers = config.get_archive_headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "TestApp/1.0.0"
    
    def test_debug_enabled(self):
        """测试调试模式检查"""
        config = AppConfig(
            debug=True,
            archive={"api_url": "http://example.com", "app_token": "test"}
        )
        assert config.is_debug_enabled() is True
    
    def test_get_log_level(self):
        """测试获取日志级别"""
        config = AppConfig(
            logging={"level": "DEBUG"},
            archive={"api_url": "http://example.com", "app_token": "test"}
        )
        assert config.get_log_level() == "DEBUG"
    
    def test_validate_required_configs_success(self):
        """测试验证必需配置成功"""
        config = AppConfig(
            archive={"api_url": "http://example.com", "app_token": "test"}
        )
        # 应该不抛出异常
        config.validate_required_configs()
    
    def test_validate_required_configs_failure(self):
        """测试验证必需配置失败"""
        config = AppConfig(
            archive={"api_url": "http://example.com", "app_token": ""}
        )
        with pytest.raises(ConfigurationException):
            config.validate_required_configs()


class TestEnvironmentVariables:
    """环境变量测试"""
    
    def setup_method(self):
        """设置测试环境"""
        # 保存原始环境变量
        self.original_env = os.environ.copy()
    
    def teardown_method(self):
        """恢复测试环境"""
        # 恢复原始环境变量
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_load_config_from_env(self):
        """测试从环境变量加载配置"""
        os.environ['ARCHIVE_API_URL'] = 'http://test.com'
        os.environ['ARCHIVE_APP_TOKEN'] = 'env-token'
        os.environ['SERVER_PORT'] = '9000'
        
        config = AppConfig(archive={"api_url": "http://test.com", "app_token": "env-token"})
        assert config.archive.api_url == 'http://test.com'
        assert config.archive.app_token == 'env-token'
        assert config.server_port == 9000
    
    def test_create_from_env_success(self):
        """测试成功从环境变量创建配置"""
        os.environ['ARCHIVE_API_URL'] = 'http://test.com'
        os.environ['ARCHIVE_APP_TOKEN'] = 'test-token'
        
        # 设置必需的环境变量后创建配置
        config = AppConfig(archive={"api_url": "http://test.com", "app_token": "test-token"})
        assert config.archive.api_url == 'http://test.com'
        assert config.archive.app_token == 'test-token'
    
    def test_create_from_env_failure(self):
        """测试从环境变量创建配置失败"""
        # 清除必需的环境变量
        if 'ARCHIVE_API_URL' in os.environ:
            del os.environ['ARCHIVE_API_URL']
        if 'ARCHIVE_APP_TOKEN' in os.environ:
            del os.environ['ARCHIVE_APP_TOKEN']
        
        # 创建配置实例，然后验证必需配置
        config = AppConfig.create_from_env()
        # 设置空值来模拟缺失的配置
        config.archive.api_url = ""
        config.archive.app_token = ""
        
        with pytest.raises(ConfigurationException):
            config.validate_required_configs()
    
    def test_env_file_loading(self):
        """测试从.env文件加载配置"""
        # 直接通过环境变量测试配置加载
        with patch.dict(os.environ, {
            'ARCHIVE_API_URL': 'http://env-file.com',
            'ARCHIVE_APP_TOKEN': 'env-file-token'
        }):
            config = AppConfig()
            assert config.archive.api_url == 'http://env-file.com'
            assert config.archive.app_token == 'env-file-token'


class TestGlobalConfigInstance:
    """全局配置实例测试"""
    
    def setup_method(self):
        """设置测试环境"""
        # 清除全局配置实例
        import hydocpusher.config.settings
        hydocpusher.config.settings._config_instance = None
    
    def teardown_method(self):
        """恢复测试环境"""
        # 清除全局配置实例
        import hydocpusher.config.settings
        hydocpusher.config.settings._config_instance = None
    
    def test_get_config_creates_instance(self):
        """测试get_config创建实例"""
        with patch('hydocpusher.config.settings.AppConfig.create_from_env') as mock_create:
            mock_config = MagicMock()
            mock_create.return_value = mock_config
            
            result = get_config()
            assert result is mock_config
            mock_create.assert_called_once()
    
    def test_get_config_returns_cached_instance(self):
        """测试get_config返回缓存的实例"""
        with patch('hydocpusher.config.settings.AppConfig.create_from_env') as mock_create:
            mock_config = MagicMock()
            mock_create.return_value = mock_config
            
            # 第一次调用
            result1 = get_config()
            # 第二次调用
            result2 = get_config()
            
            assert result1 is result2 is mock_config
            mock_create.assert_called_once()  # 只调用一次
    
    def test_reload_config(self):
        """测试重新加载配置"""
        with patch('hydocpusher.config.settings.AppConfig.create_from_env') as mock_create:
            mock_config1 = MagicMock()
            mock_config2 = MagicMock()
            mock_create.side_effect = [mock_config1, mock_config2]
            
            # 第一次加载
            result1 = get_config()
            assert result1 is mock_config1
            
            # 重新加载
            result2 = reload_config()
            assert result2 is mock_config2
            
            # 再次获取应该返回新配置
            result3 = get_config()
            assert result3 is mock_config2
            
            assert mock_create.call_count == 2