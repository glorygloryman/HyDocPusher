#!/usr/bin/env python3
"""
健康服务单元测试
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from hydocpusher.services.health_service import (
    HealthService,
    HealthStatus,
    ComponentHealth,
    SystemHealth,
    get_health_service
)
from hydocpusher.client.archive_client import ArchiveClient
from hydocpusher.consumer.pulsar_consumer import PulsarConsumer


class TestHealthService:
    """健康服务测试类"""
    
    @pytest.fixture
    def health_service(self):
        """创建健康服务实例"""
        with patch('hydocpusher.services.health_service.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.validate_required_configs = Mock()
            mock_get_config.return_value = mock_config
            service = HealthService()
            return service
    
    @pytest.fixture
    def mock_archive_client(self):
        """模拟档案客户端"""
        client = Mock(spec=ArchiveClient)
        client.health_check_async = AsyncMock()
        return client
    
    @pytest.fixture
    def mock_pulsar_consumer(self):
        """模拟Pulsar消费者"""
        consumer = Mock(spec=PulsarConsumer)
        consumer.is_connected = True
        consumer.is_running = True
        consumer.get_consumer_stats = Mock(return_value={
            'messages_received': 100,
            'messages_processed': 95,
            'last_message_time': datetime.now().isoformat()
        })
        return consumer
    
    def test_health_service_initialization(self, health_service):
        """测试健康服务初始化"""
        assert health_service is not None
        assert health_service.config is not None
        assert health_service.start_time is not None
        assert isinstance(health_service.start_time, datetime)
        assert health_service._last_health_check is None
    
    def test_set_components(self, health_service, mock_archive_client, mock_pulsar_consumer):
        """测试设置组件"""
        health_service.set_components(
            archive_client=mock_archive_client,
            pulsar_consumer=mock_pulsar_consumer
        )
        
        assert health_service._archive_client == mock_archive_client
        assert health_service._pulsar_consumer == mock_pulsar_consumer
    
    @pytest.mark.asyncio
    async def test_check_configuration_health_success(self, health_service):
        """测试配置健康检查成功"""
        with patch.object(health_service.config, 'validate_required_configs'):
            component_health = await health_service._check_configuration_health()
            
            assert component_health.name == "configuration"
            assert component_health.status == HealthStatus.HEALTHY
            assert "Configuration is valid" in component_health.message
            assert component_health.response_time_ms is not None
            assert component_health.response_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_check_configuration_health_failure(self, health_service):
        """测试配置健康检查失败"""
        with patch.object(health_service.config, 'validate_required_configs', 
                         side_effect=Exception("Config error")):
            component_health = await health_service._check_configuration_health()
            
            assert component_health.name == "configuration"
            assert component_health.status == HealthStatus.UNHEALTHY
            assert "Configuration error" in component_health.message
    
    @pytest.mark.asyncio
    async def test_check_archive_health_success(self, health_service, mock_archive_client):
        """测试档案系统健康检查成功"""
        mock_archive_client.health_check_async.return_value = {'status': 'healthy'}
        health_service.set_components(archive_client=mock_archive_client)
        
        component_health = await health_service._check_archive_health()
        
        assert component_health.name == "archive_system"
        assert component_health.status == HealthStatus.HEALTHY
        assert "Archive system is accessible" in component_health.message
        assert component_health.response_time_ms is not None
        mock_archive_client.health_check_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_archive_health_degraded(self, health_service, mock_archive_client):
        """测试档案系统健康检查降级"""
        mock_archive_client.health_check_async.return_value = {'status': 'degraded'}
        health_service.set_components(archive_client=mock_archive_client)
        
        component_health = await health_service._check_archive_health()
        
        assert component_health.name == "archive_system"
        assert component_health.status == HealthStatus.DEGRADED
        assert "may have issues" in component_health.message
    
    @pytest.mark.asyncio
    async def test_check_archive_health_timeout(self, health_service, mock_archive_client):
        """测试档案系统健康检查超时"""
        mock_archive_client.health_check_async.side_effect = asyncio.TimeoutError()
        health_service.set_components(archive_client=mock_archive_client)
        
        component_health = await health_service._check_archive_health()
        
        assert component_health.name == "archive_system"
        assert component_health.status == HealthStatus.UNHEALTHY
        assert "timed out" in component_health.message
    
    @pytest.mark.asyncio
    async def test_check_archive_health_no_client(self, health_service):
        """测试没有档案客户端时的健康检查"""
        component_health = await health_service._check_archive_health()
        
        assert component_health.name == "archive_system"
        assert component_health.status == HealthStatus.UNKNOWN
        assert "not configured" in component_health.message
    
    @pytest.mark.asyncio
    async def test_check_pulsar_health_success(self, health_service, mock_pulsar_consumer):
        """测试Pulsar健康检查成功"""
        health_service.set_components(pulsar_consumer=mock_pulsar_consumer)
        
        component_health = await health_service._check_pulsar_health()
        
        assert component_health.name == "pulsar_connection"
        assert component_health.status == HealthStatus.HEALTHY
        assert "Pulsar connection is active" in component_health.message
        assert component_health.details is not None
        mock_pulsar_consumer.get_consumer_stats.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_pulsar_health_connected_not_running(self, health_service, mock_pulsar_consumer):
        """测试Pulsar连接但未运行"""
        mock_pulsar_consumer.is_connected = True
        mock_pulsar_consumer.is_running = False
        health_service.set_components(pulsar_consumer=mock_pulsar_consumer)
        
        component_health = await health_service._check_pulsar_health()
        
        assert component_health.name == "pulsar_connection"
        assert component_health.status == HealthStatus.DEGRADED
        assert "connected but not consuming" in component_health.message
    
    @pytest.mark.asyncio
    async def test_check_pulsar_health_disconnected(self, health_service, mock_pulsar_consumer):
        """测试Pulsar连接断开"""
        mock_pulsar_consumer.is_connected = False
        mock_pulsar_consumer.is_running = False
        health_service.set_components(pulsar_consumer=mock_pulsar_consumer)
        
        component_health = await health_service._check_pulsar_health()
        
        assert component_health.name == "pulsar_connection"
        assert component_health.status == HealthStatus.UNHEALTHY
        assert "connection is down" in component_health.message
    
    @pytest.mark.asyncio
    async def test_check_resource_health_normal(self, health_service):
        """测试系统资源健康检查正常"""
        with patch('psutil.cpu_percent', return_value=30.0), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            mock_memory.return_value.percent = 50.0
            mock_memory.return_value.available = 8 * 1024**3  # 8GB
            mock_disk.return_value.percent = 60.0
            mock_disk.return_value.free = 100 * 1024**3  # 100GB
            
            component_health = await health_service._check_resource_health()
            
            assert component_health.name == "system_resources"
            assert component_health.status == HealthStatus.HEALTHY
            assert "resources are normal" in component_health.message
    
    @pytest.mark.asyncio
    async def test_check_resource_health_high_usage(self, health_service):
        """测试系统资源使用率高"""
        with patch('psutil.cpu_percent', return_value=95.0), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            mock_memory.return_value.percent = 95.0
            mock_memory.return_value.available = 1 * 1024**3  # 1GB
            mock_disk.return_value.percent = 98.0
            mock_disk.return_value.free = 2 * 1024**3  # 2GB
            
            component_health = await health_service._check_resource_health()
            
            assert component_health.name == "system_resources"
            assert component_health.status == HealthStatus.UNHEALTHY
            assert "High CPU usage" in component_health.message
            assert "High memory usage" in component_health.message
            assert "High disk usage" in component_health.message
    
    @pytest.mark.asyncio
    async def test_check_resource_health_no_psutil(self, health_service):
        """测试没有psutil时的资源检查"""
        with patch('psutil.cpu_percent', side_effect=ImportError()):
            component_health = await health_service._check_resource_health()
            
            assert component_health.name == "system_resources"
            assert component_health.status == HealthStatus.UNKNOWN
            assert "not available" in component_health.message
    
    def test_calculate_overall_status_healthy(self, health_service):
        """测试计算整体状态 - 健康"""
        components = [
            ComponentHealth("comp1", HealthStatus.HEALTHY, "OK", datetime.now()),
            ComponentHealth("comp2", HealthStatus.HEALTHY, "OK", datetime.now())
        ]
        
        status = health_service._calculate_overall_status(components)
        assert status == HealthStatus.HEALTHY
    
    def test_calculate_overall_status_degraded(self, health_service):
        """测试计算整体状态 - 降级"""
        components = [
            ComponentHealth("comp1", HealthStatus.HEALTHY, "OK", datetime.now()),
            ComponentHealth("comp2", HealthStatus.DEGRADED, "Warning", datetime.now())
        ]
        
        status = health_service._calculate_overall_status(components)
        assert status == HealthStatus.DEGRADED
    
    def test_calculate_overall_status_unhealthy(self, health_service):
        """测试计算整体状态 - 不健康"""
        components = [
            ComponentHealth("comp1", HealthStatus.HEALTHY, "OK", datetime.now()),
            ComponentHealth("comp2", HealthStatus.UNHEALTHY, "Error", datetime.now())
        ]
        
        status = health_service._calculate_overall_status(components)
        assert status == HealthStatus.UNHEALTHY
    
    def test_calculate_overall_status_unknown(self, health_service):
        """测试计算整体状态 - 未知"""
        components = [
            ComponentHealth("comp1", HealthStatus.HEALTHY, "OK", datetime.now()),
            ComponentHealth("comp2", HealthStatus.UNKNOWN, "Unknown", datetime.now())
        ]
        
        status = health_service._calculate_overall_status(components)
        assert status == HealthStatus.DEGRADED
    
    def test_calculate_overall_status_empty(self, health_service):
        """测试计算整体状态 - 空组件列表"""
        status = health_service._calculate_overall_status([])
        assert status == HealthStatus.UNKNOWN
    
    def test_generate_health_summary(self, health_service):
        """测试生成健康状态摘要"""
        components = [
            ComponentHealth("comp1", HealthStatus.HEALTHY, "OK", datetime.now(), 10.0),
            ComponentHealth("comp2", HealthStatus.DEGRADED, "Warning", datetime.now(), 20.0),
            ComponentHealth("comp3", HealthStatus.UNHEALTHY, "Error", datetime.now(), 30.0)
        ]
        
        summary = health_service._generate_health_summary(components, 3600)
        
        assert summary['total_components'] == 3
        assert summary['status_counts']['healthy'] == 1
        assert summary['status_counts']['degraded'] == 1
        assert summary['status_counts']['unhealthy'] == 1
        assert summary['uptime_hours'] == 1.0
        assert summary['average_response_time_ms'] == 20.0
        assert 'last_check' in summary
    
    @pytest.mark.asyncio
    async def test_check_system_health_integration(self, health_service, mock_archive_client, mock_pulsar_consumer):
        """测试系统健康检查集成"""
        mock_archive_client.health_check_async.return_value = {'status': 'healthy'}
        health_service.set_components(
            archive_client=mock_archive_client,
            pulsar_consumer=mock_pulsar_consumer
        )
        
        with patch.object(health_service.config, 'validate_required_configs'):
            system_health = await health_service.check_system_health()
            
            assert isinstance(system_health, SystemHealth)
            assert system_health.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
            assert len(system_health.components) >= 3  # config, archive, pulsar, resources
            assert system_health.uptime_seconds >= 0
            assert system_health.summary is not None
            assert health_service._last_health_check == system_health
    
    def test_get_last_health_check(self, health_service):
        """测试获取最后一次健康检查结果"""
        assert health_service.get_last_health_check() is None
        
        # 设置一个模拟的健康检查结果
        mock_health = SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now(),
            uptime_seconds=100,
            components=[],
            summary={}
        )
        health_service._last_health_check = mock_health
        
        assert health_service.get_last_health_check() == mock_health
    
    def test_to_dict(self, health_service):
        """测试转换为字典"""
        system_health = SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now(),
            uptime_seconds=100,
            components=[
                ComponentHealth("test", HealthStatus.HEALTHY, "OK", datetime.now(), 10.0, {'key': 'value'})
            ],
            summary={'total': 1}
        )
        
        result = health_service.to_dict(system_health)
        
        assert result['status'] == 'healthy'
        assert 'timestamp' in result
        assert result['uptime_seconds'] == 100
        assert len(result['components']) == 1
        assert result['components'][0]['name'] == 'test'
        assert result['components'][0]['status'] == 'healthy'
        assert result['components'][0]['response_time_ms'] == 10.0
        assert result['components'][0]['details'] == {'key': 'value'}
        assert result['summary'] == {'total': 1}


class TestHealthServiceSingleton:
    """健康服务单例测试"""
    
    def test_get_health_service_singleton(self):
        """测试健康服务单例模式"""
        service1 = get_health_service()
        service2 = get_health_service()
        
        assert service1 is service2
        assert isinstance(service1, HealthService)


class TestComponentHealth:
    """组件健康状态测试"""
    
    def test_component_health_creation(self):
        """测试组件健康状态创建"""
        now = datetime.now()
        component = ComponentHealth(
            name="test_component",
            status=HealthStatus.HEALTHY,
            message="All good",
            last_check=now,
            response_time_ms=15.5,
            details={'key': 'value'}
        )
        
        assert component.name == "test_component"
        assert component.status == HealthStatus.HEALTHY
        assert component.message == "All good"
        assert component.last_check == now
        assert component.response_time_ms == 15.5
        assert component.details == {'key': 'value'}


class TestSystemHealth:
    """系统健康状态测试"""
    
    def test_system_health_creation(self):
        """测试系统健康状态创建"""
        now = datetime.now()
        components = [
            ComponentHealth("comp1", HealthStatus.HEALTHY, "OK", now)
        ]
        
        system_health = SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=now,
            uptime_seconds=3600,
            components=components,
            summary={'total': 1}
        )
        
        assert system_health.status == HealthStatus.HEALTHY
        assert system_health.timestamp == now
        assert system_health.uptime_seconds == 3600
        assert len(system_health.components) == 1
        assert system_health.summary == {'total': 1}