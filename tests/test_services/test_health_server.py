#!/usr/bin/env python3
"""
健康服务器单元测试
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from hydocpusher.services.health_server import HealthServer, get_health_server
from hydocpusher.services.health_service import (
    HealthService,
    HealthStatus,
    ComponentHealth,
    SystemHealth
)


class TestHealthServer(AioHTTPTestCase):
    """健康服务器测试类"""
    
    async def get_application(self):
        """创建测试应用"""
        # 创建模拟的健康服务
        self.mock_health_service = Mock(spec=HealthService)
        self.mock_health_service.start_time = datetime.now()
        
        # 创建健康服务器
        self.health_server = HealthServer(self.mock_health_service)
        return self.health_server.create_app()
    
    def create_mock_system_health(self, status=HealthStatus.HEALTHY):
        """创建模拟的系统健康状态"""
        components = [
            ComponentHealth(
                name="configuration",
                status=HealthStatus.HEALTHY,
                message="Configuration is valid",
                last_check=datetime.now(),
                response_time_ms=5.0
            ),
            ComponentHealth(
                name="archive_system",
                status=status,
                message="Archive system status",
                last_check=datetime.now(),
                response_time_ms=10.0
            )
        ]
        
        return SystemHealth(
            status=status,
            timestamp=datetime.now(),
            uptime_seconds=3600,
            components=components,
            summary={
                'total_components': 2,
                'status_counts': {'healthy': 2 if status == HealthStatus.HEALTHY else 1},
                'uptime_hours': 1.0
            }
        )
    
    @unittest_run_loop
    async def test_root_handler(self):
        """测试根路径处理器"""
        resp = await self.client.request("GET", "/")
        assert resp.status == 200
        
        data = await resp.json()
        assert 'service' in data
        assert 'version' in data
        assert 'endpoints' in data
        assert data['endpoints']['health'] == '/health'
    
    @unittest_run_loop
    async def test_health_check_handler_healthy(self):
        """测试健康检查处理器 - 健康状态"""
        mock_health = self.create_mock_system_health(HealthStatus.HEALTHY)
        self.mock_health_service.check_system_health = AsyncMock(return_value=mock_health)
        
        resp = await self.client.request("GET", "/health")
        assert resp.status == 200
        
        data = await resp.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'uptime_seconds' in data
        assert data['message'] == 'System is healthy'
    
    @unittest_run_loop
    async def test_health_check_handler_unhealthy(self):
        """测试健康检查处理器 - 不健康状态"""
        mock_health = self.create_mock_system_health(HealthStatus.UNHEALTHY)
        self.mock_health_service.check_system_health = AsyncMock(return_value=mock_health)
        
        resp = await self.client.request("GET", "/health")
        assert resp.status == 503
        
        data = await resp.json()
        assert data['status'] == 'unhealthy'
        assert data['message'] == 'System is unhealthy'
    
    @unittest_run_loop
    async def test_health_check_handler_degraded(self):
        """测试健康检查处理器 - 降级状态"""
        mock_health = self.create_mock_system_health(HealthStatus.DEGRADED)
        self.mock_health_service.check_system_health = AsyncMock(return_value=mock_health)
        
        resp = await self.client.request("GET", "/health")
        assert resp.status == 200  # 降级状态仍返回200
        
        data = await resp.json()
        assert data['status'] == 'degraded'
        assert data['message'] == 'System is degraded'
    
    @unittest_run_loop
    async def test_health_check_handler_error(self):
        """测试健康检查处理器 - 错误情况"""
        self.mock_health_service.check_system_health = AsyncMock(
            side_effect=Exception("Health check failed")
        )
        
        resp = await self.client.request("GET", "/health")
        assert resp.status == 500
        
        data = await resp.json()
        assert data['status'] == 'error'
        assert 'Health check failed' in data['message']
    
    @unittest_run_loop
    async def test_detailed_health_handler(self):
        """测试详细健康检查处理器"""
        mock_health = self.create_mock_system_health(HealthStatus.HEALTHY)
        self.mock_health_service.check_system_health = AsyncMock(return_value=mock_health)
        self.mock_health_service.to_dict = Mock(return_value={
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': [],
            'summary': {}
        })
        
        resp = await self.client.request("GET", "/health/detailed")
        assert resp.status == 200
        
        data = await resp.json()
        assert data['status'] == 'healthy'
        assert 'components' in data
        assert 'summary' in data
        self.mock_health_service.to_dict.assert_called_once()
    
    @unittest_run_loop
    async def test_components_health_handler(self):
        """测试组件健康状态处理器"""
        mock_health = self.create_mock_system_health(HealthStatus.HEALTHY)
        self.mock_health_service.check_system_health = AsyncMock(return_value=mock_health)
        
        resp = await self.client.request("GET", "/health/components")
        assert resp.status == 200
        
        data = await resp.json()
        assert 'components' in data
        assert 'total_components' in data
        assert data['total_components'] == 2
        assert len(data['components']) == 2
        
        # 检查组件数据结构
        component = data['components'][0]
        assert 'name' in component
        assert 'status' in component
        assert 'message' in component
        assert 'response_time_ms' in component
        assert 'last_check' in component
    
    @unittest_run_loop
    async def test_readiness_handler_ready(self):
        """测试就绪检查处理器 - 就绪状态"""
        mock_health = self.create_mock_system_health(HealthStatus.HEALTHY)
        self.mock_health_service.check_system_health = AsyncMock(return_value=mock_health)
        
        resp = await self.client.request("GET", "/ready")
        assert resp.status == 200
        
        data = await resp.json()
        assert data['ready'] is True
        assert 'ready to accept traffic' in data['message']
    
    @unittest_run_loop
    async def test_readiness_handler_not_ready(self):
        """测试就绪检查处理器 - 未就绪状态"""
        # 创建包含不健康关键组件的健康状态
        components = [
            ComponentHealth(
                name="configuration",
                status=HealthStatus.HEALTHY,
                message="OK",
                last_check=datetime.now()
            ),
            ComponentHealth(
                name="archive_system",
                status=HealthStatus.UNHEALTHY,
                message="Archive system down",
                last_check=datetime.now()
            )
        ]
        
        mock_health = SystemHealth(
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.now(),
            uptime_seconds=3600,
            components=components,
            summary={}
        )
        
        self.mock_health_service.check_system_health = AsyncMock(return_value=mock_health)
        
        resp = await self.client.request("GET", "/ready")
        assert resp.status == 503
        
        data = await resp.json()
        assert data['ready'] is False
        assert 'Critical components unhealthy' in data['message']
    
    @unittest_run_loop
    async def test_liveness_handler(self):
        """测试存活检查处理器"""
        resp = await self.client.request("GET", "/live")
        assert resp.status == 200
        
        data = await resp.json()
        assert data['alive'] is True
        assert data['message'] == 'Service is alive'
        assert 'uptime_seconds' in data
    
    @unittest_run_loop
    async def test_info_handler(self):
        """测试应用信息处理器"""
        resp = await self.client.request("GET", "/info")
        assert resp.status == 200
        
        data = await resp.json()
        assert 'name' in data
        assert 'version' in data
        assert 'description' in data
        assert 'start_time' in data
        assert 'uptime_seconds' in data
        assert 'config' in data
        assert 'endpoints' in data
    
    @unittest_run_loop
    async def test_cors_middleware(self):
        """测试CORS中间件"""
        resp = await self.client.request("GET", "/health")
        
        assert 'Access-Control-Allow-Origin' in resp.headers
        assert resp.headers['Access-Control-Allow-Origin'] == '*'
        assert 'Access-Control-Allow-Methods' in resp.headers
        assert 'Access-Control-Allow-Headers' in resp.headers


class TestHealthServerLifecycle:
    """健康服务器生命周期测试"""
    
    @pytest.fixture
    def mock_health_service(self):
        """模拟健康服务"""
        service = Mock(spec=HealthService)
        service.start_time = datetime.now()
        return service
    
    @pytest.fixture
    def health_server(self, mock_health_service):
        """健康服务器实例"""
        return HealthServer(mock_health_service)
    
    def test_health_server_initialization(self, health_server, mock_health_service):
        """测试健康服务器初始化"""
        assert health_server.health_service == mock_health_service
        assert health_server.app is None
        assert health_server.runner is None
        assert health_server.site is None
    
    def test_create_app(self, health_server):
        """测试创建应用"""
        app = health_server.create_app()
        
        assert isinstance(app, web.Application)
        assert health_server.app == app
        
        # 检查路由是否正确添加
        routes = [route.resource.canonical for route in app.router.routes()]
        expected_routes = ['/', '/health', '/health/detailed', '/health/components', '/ready', '/live', '/info']
        
        for expected_route in expected_routes:
            assert expected_route in routes
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self, health_server):
        """测试启动和停止服务器"""
        with patch('aiohttp.web.AppRunner') as mock_runner_class, \
             patch('aiohttp.web.TCPSite') as mock_site_class:
            
            mock_runner = AsyncMock()
            mock_site = AsyncMock()
            mock_runner_class.return_value = mock_runner
            mock_site_class.return_value = mock_site
            
            # 测试启动
            await health_server.start('localhost', 8081)
            
            assert health_server.runner == mock_runner
            assert health_server.site == mock_site
            mock_runner.setup.assert_called_once()
            mock_site.start.assert_called_once()
            
            # 测试停止
            await health_server.stop()
            
            mock_site.stop.assert_called_once()
            mock_runner.cleanup.assert_called_once()
            assert health_server.site is None
            assert health_server.runner is None
            assert health_server.app is None
    
    @pytest.mark.asyncio
    async def test_start_failure(self, health_server):
        """测试启动失败"""
        with patch('aiohttp.web.AppRunner', side_effect=Exception("Start failed")):
            with pytest.raises(Exception, match="Start failed"):
                await health_server.start('localhost', 8081)


class TestHealthServerSingleton:
    """健康服务器单例测试"""
    
    def test_get_health_server_singleton(self):
        """测试健康服务器单例模式"""
        server1 = get_health_server()
        server2 = get_health_server()
        
        assert server1 is server2
        assert isinstance(server1, HealthServer)


class TestHealthServerIntegration:
    """健康服务器集成测试"""
    
    @pytest.mark.asyncio
    async def test_health_server_with_real_health_service(self):
        """测试健康服务器与真实健康服务的集成"""
        from hydocpusher.services.health_service import HealthService
        
        # 创建真实的健康服务
        health_service = HealthService()
        health_server = HealthServer(health_service)
        
        # 创建应用
        app = health_server.create_app()
        assert app is not None
        
        # 验证健康服务被正确设置
        assert health_server.health_service == health_service
    
    @pytest.mark.asyncio
    async def test_start_health_server_function(self):
        """测试启动健康服务器函数"""
        from hydocpusher.services.health_server import start_health_server
        from hydocpusher.services.health_service import HealthService
        
        health_service = HealthService()
        
        with patch.object(HealthServer, 'start', new_callable=AsyncMock) as mock_start:
            server = await start_health_server(
                host='localhost',
                port=8081,
                health_service=health_service
            )
            
            assert isinstance(server, HealthServer)
            assert server.health_service == health_service
            mock_start.assert_called_once_with('localhost', 8081)