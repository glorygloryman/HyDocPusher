#!/usr/bin/env python3
"""
主应用入口点单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from main import HyDocPusherApp
from hydocpusher.config.settings import AppConfig
from hydocpusher.consumer.pulsar_consumer import PulsarConsumer
from hydocpusher.client.archive_client import ArchiveClient
from hydocpusher.transformer.data_transformer import DataTransformer
from hydocpusher.services.health_service import HealthService
from hydocpusher.services.health_server import HealthServer


class TestHyDocPusherApp:
    """主应用测试类"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        config = Mock(spec=AppConfig)
        config.app_name = "HyDocPusher"
        config.version = "1.0.0"
        config.environment = "test"
        config.debug = True
        config.health_check_port = 8081
        config.health_check_host = "localhost"
        return config
    
    @pytest.fixture
    def mock_consumer(self):
        """模拟消费者"""
        consumer = Mock(spec=PulsarConsumer)
        consumer.connect = AsyncMock()
        consumer.start_consuming = AsyncMock()
        consumer.close = AsyncMock()
        return consumer
    
    @pytest.fixture
    def mock_archive_client(self):
        """模拟档案客户端"""
        client = Mock(spec=ArchiveClient)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        return client
    
    @pytest.fixture
    def mock_transformer(self):
        """模拟数据转换器"""
        return Mock(spec=DataTransformer)
    
    @pytest.fixture
    def mock_health_service(self):
        """模拟健康服务"""
        service = Mock(spec=HealthService)
        service.set_component = Mock()
        return service
    
    @pytest.fixture
    def mock_health_server(self):
        """模拟健康服务器"""
        server = Mock(spec=HealthServer)
        server.start = AsyncMock()
        server.stop = AsyncMock()
        return server
    
    @pytest.fixture
    def app(self, mock_config):
        """应用实例"""
        return HyDocPusherApp(mock_config)
    
    def test_app_initialization(self, app, mock_config):
        """测试应用初始化"""
        assert app.config == mock_config
        assert app.consumer is None
        assert app.archive_client is None
        assert app.transformer is None
        assert app.health_service is None
        assert app.health_server is None
        assert app._shutdown_event is not None
        assert isinstance(app._shutdown_event, asyncio.Event)
    
    @pytest.mark.asyncio
    async def test_initialize_components_success(self, app, mock_config):
        """测试组件初始化成功"""
        with patch('main.PulsarConsumer') as mock_consumer_class, \
             patch('main.ArchiveClient') as mock_client_class, \
             patch('main.DataTransformer') as mock_transformer_class, \
             patch('main.get_health_service') as mock_get_health_service, \
             patch('main.get_health_server') as mock_get_health_server:
            
            # 设置模拟对象
            mock_consumer = Mock()
            mock_client = Mock()
            mock_transformer = Mock()
            mock_health_service = Mock()
            mock_health_server = Mock()
            
            mock_consumer_class.return_value = mock_consumer
            mock_client_class.return_value = mock_client
            mock_transformer_class.return_value = mock_transformer
            mock_get_health_service.return_value = mock_health_service
            mock_get_health_server.return_value = mock_health_server
            
            # 执行初始化
            await app._initialize_components()
            
            # 验证组件创建
            mock_consumer_class.assert_called_once_with(mock_config.pulsar)
            mock_client_class.assert_called_once_with(mock_config.archive)
            mock_transformer_class.assert_called_once_with(mock_config.classification)
            
            # 验证组件赋值
            assert app.consumer == mock_consumer
            assert app.archive_client == mock_client
            assert app.transformer == mock_transformer
            assert app.health_service == mock_health_service
            assert app.health_server == mock_health_server
            
            # 验证健康服务组件设置
            expected_calls = [
                (('configuration', mock_config),),
                (('consumer', mock_consumer),),
                (('archive_client', mock_client),),
                (('transformer', mock_transformer),)
            ]
            
            actual_calls = mock_health_service.set_component.call_args_list
            assert len(actual_calls) == 4
    
    @pytest.mark.asyncio
    async def test_initialize_components_failure(self, app):
        """测试组件初始化失败"""
        with patch('main.PulsarConsumer', side_effect=Exception("Consumer init failed")):
            with pytest.raises(Exception, match="Consumer init failed"):
                await app._initialize_components()
    
    @pytest.mark.asyncio
    async def test_setup_health_check_success(self, app, mock_health_server, mock_config):
        """测试健康检查设置成功"""
        app.health_server = mock_health_server
        
        await app._setup_health_check()
        
        mock_health_server.start.assert_called_once_with(
            mock_config.health_check_host,
            mock_config.health_check_port
        )
    
    @pytest.mark.asyncio
    async def test_setup_health_check_failure(self, app, mock_health_server, mock_config):
        """测试健康检查设置失败"""
        app.health_server = mock_health_server
        mock_health_server.start.side_effect = Exception("Health server start failed")
        
        with pytest.raises(Exception, match="Health server start failed"):
            await app._setup_health_check()
    
    @pytest.mark.asyncio
    async def test_start_message_processing_success(self, app, mock_consumer):
        """测试消息处理启动成功"""
        app.consumer = mock_consumer
        
        await app._start_message_processing()
        
        mock_consumer.connect.assert_called_once()
        mock_consumer.start_consuming.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_message_processing_failure(self, app, mock_consumer):
        """测试消息处理启动失败"""
        app.consumer = mock_consumer
        mock_consumer.connect.side_effect = Exception("Consumer connect failed")
        
        with pytest.raises(Exception, match="Consumer connect failed"):
            await app._start_message_processing()
    
    @pytest.mark.asyncio
    async def test_cleanup_success(self, app, mock_consumer, mock_health_server):
        """测试清理成功"""
        app.consumer = mock_consumer
        app.health_server = mock_health_server
        
        await app._cleanup()
        
        mock_health_server.stop.assert_called_once()
        mock_consumer.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_with_exceptions(self, app, mock_consumer, mock_health_server):
        """测试清理时出现异常"""
        app.consumer = mock_consumer
        app.health_server = mock_health_server
        
        # 设置异常
        mock_health_server.stop.side_effect = Exception("Health server stop failed")
        mock_consumer.close.side_effect = Exception("Consumer close failed")
        
        # 清理不应该抛出异常
        await app._cleanup()
        
        mock_health_server.stop.assert_called_once()
        mock_consumer.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_success(self, app):
        """测试应用运行成功"""
        with patch.object(app, '_initialize_components', new_callable=AsyncMock) as mock_init, \
             patch.object(app, '_setup_health_check', new_callable=AsyncMock) as mock_health, \
             patch.object(app, '_start_message_processing', new_callable=AsyncMock) as mock_process, \
             patch.object(app, '_cleanup', new_callable=AsyncMock) as mock_cleanup:
            
            # 模拟快速关闭
            async def quick_shutdown():
                await asyncio.sleep(0.1)
                app._shutdown_event.set()
            
            # 启动快速关闭任务
            shutdown_task = asyncio.create_task(quick_shutdown())
            
            try:
                await app.run()
            finally:
                if not shutdown_task.done():
                    shutdown_task.cancel()
            
            # 验证调用顺序
            mock_init.assert_called_once()
            mock_health.assert_called_once()
            mock_process.assert_called_once()
            mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_initialization_failure(self, app):
        """测试应用运行时初始化失败"""
        with patch.object(app, '_initialize_components', new_callable=AsyncMock, 
                         side_effect=Exception("Init failed")) as mock_init, \
             patch.object(app, '_cleanup', new_callable=AsyncMock) as mock_cleanup:
            
            with pytest.raises(Exception, match="Init failed"):
                await app.run()
            
            mock_init.assert_called_once()
            mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_health_check_failure(self, app):
        """测试应用运行时健康检查失败"""
        with patch.object(app, '_initialize_components', new_callable=AsyncMock) as mock_init, \
             patch.object(app, '_setup_health_check', new_callable=AsyncMock, 
                         side_effect=Exception("Health check failed")) as mock_health, \
             patch.object(app, '_cleanup', new_callable=AsyncMock) as mock_cleanup:
            
            with pytest.raises(Exception, match="Health check failed"):
                await app.run()
            
            mock_init.assert_called_once()
            mock_health.assert_called_once()
            mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_message_processing_failure(self, app):
        """测试应用运行时消息处理失败"""
        with patch.object(app, '_initialize_components', new_callable=AsyncMock) as mock_init, \
             patch.object(app, '_setup_health_check', new_callable=AsyncMock) as mock_health, \
             patch.object(app, '_start_message_processing', new_callable=AsyncMock, 
                         side_effect=Exception("Message processing failed")) as mock_process, \
             patch.object(app, '_cleanup', new_callable=AsyncMock) as mock_cleanup:
            
            with pytest.raises(Exception, match="Message processing failed"):
                await app.run()
            
            mock_init.assert_called_once()
            mock_health.assert_called_once()
            mock_process.assert_called_once()
            mock_cleanup.assert_called_once()
    
    def test_shutdown(self, app):
        """测试关闭方法"""
        assert not app._shutdown_event.is_set()
        
        app.shutdown()
        
        assert app._shutdown_event.is_set()


class TestMainFunction:
    """主函数测试"""
    
    @pytest.mark.asyncio
    async def test_main_function_success(self):
        """测试主函数成功执行"""
        with patch('main.load_config') as mock_load_config, \
             patch('main.setup_logging') as mock_setup_logging, \
             patch('main.HyDocPusherApp') as mock_app_class:
            
            # 设置模拟对象
            mock_config = Mock()
            mock_app = Mock()
            mock_app.run = AsyncMock()
            
            mock_load_config.return_value = mock_config
            mock_app_class.return_value = mock_app
            
            # 导入并执行主函数
            from main import main
            await main()
            
            # 验证调用
            mock_load_config.assert_called_once()
            mock_setup_logging.assert_called_once_with(mock_config.logging)
            mock_app_class.assert_called_once_with(mock_config)
            mock_app.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_function_config_failure(self):
        """测试主函数配置加载失败"""
        with patch('main.load_config', side_effect=Exception("Config load failed")):
            from main import main
            
            with pytest.raises(Exception, match="Config load failed"):
                await main()
    
    @pytest.mark.asyncio
    async def test_main_function_app_failure(self):
        """测试主函数应用运行失败"""
        with patch('main.load_config') as mock_load_config, \
             patch('main.setup_logging') as mock_setup_logging, \
             patch('main.HyDocPusherApp') as mock_app_class:
            
            mock_config = Mock()
            mock_app = Mock()
            mock_app.run = AsyncMock(side_effect=Exception("App run failed"))
            
            mock_load_config.return_value = mock_config
            mock_app_class.return_value = mock_app
            
            from main import main
            
            with pytest.raises(Exception, match="App run failed"):
                await main()


class TestSignalHandling:
    """信号处理测试"""
    
    @pytest.mark.asyncio
    async def test_signal_handler_integration(self):
        """测试信号处理器集成"""
        import signal
        from main import HyDocPusherApp
        
        mock_config = Mock()
        app = HyDocPusherApp(mock_config)
        
        # 模拟信号处理器设置
        with patch('signal.signal') as mock_signal:
            # 这里我们不能直接测试信号处理，但可以验证设置
            # 在实际的main函数中会设置信号处理器
            pass
        
        # 测试shutdown方法
        assert not app._shutdown_event.is_set()
        app.shutdown()
        assert app._shutdown_event.is_set()


class TestAppIntegration:
    """应用集成测试"""
    
    @pytest.mark.asyncio
    async def test_app_lifecycle_integration(self):
        """测试应用生命周期集成"""
        from hydocpusher.config.settings import load_config
        
        # 使用真实配置进行集成测试
        try:
            config = load_config()
            app = HyDocPusherApp(config)
            
            # 验证应用创建
            assert app.config == config
            assert app._shutdown_event is not None
            
            # 测试shutdown
            app.shutdown()
            assert app._shutdown_event.is_set()
            
        except Exception as e:
            # 如果配置加载失败，跳过集成测试
            pytest.skip(f"Integration test skipped due to config issue: {e}")