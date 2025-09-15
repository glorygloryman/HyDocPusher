#!/usr/bin/env python3
"""
健康检查HTTP服务器
提供REST API端点用于系统健康监控
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from aiohttp import web, web_request
from aiohttp.web_response import Response

from .health_service import get_health_service, HealthService
from ..config.settings import get_config

logger = logging.getLogger(__name__)


class HealthServer:
    """健康检查HTTP服务器类"""
    
    def __init__(self, health_service: Optional[HealthService] = None):
        """初始化健康检查服务器"""
        self.config = get_config()
        self.health_service = health_service or get_health_service()
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        
        logger.info("Health server initialized")
    
    def create_app(self) -> web.Application:
        """创建aiohttp应用"""
        app = web.Application()
        
        # 添加路由
        app.router.add_get('/health', self.health_check_handler)
        app.router.add_get('/health/detailed', self.detailed_health_handler)
        app.router.add_get('/health/components', self.components_health_handler)
        app.router.add_get('/ready', self.readiness_handler)
        app.router.add_get('/live', self.liveness_handler)
        app.router.add_get('/info', self.info_handler)
        app.router.add_get('/', self.root_handler)
        
        # 添加中间件
        app.middlewares.append(self.logging_middleware)
        app.middlewares.append(self.cors_middleware)
        
        self.app = app
        return app
    
    async def start(self, host: str = None, port: int = None) -> None:
        """启动健康检查服务器"""
        host = host or self.config.server_host
        port = port or (self.config.server_port + 1)  # 健康检查端口比主端口+1
        
        try:
            logger.info(f"Starting health server on {host}:{port}")
            
            # 创建应用
            if not self.app:
                self.create_app()
            
            # 创建runner
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            # 创建站点
            self.site = web.TCPSite(self.runner, host, port)
            await self.site.start()
            
            logger.info(f"Health server started successfully on http://{host}:{port}")
            
        except Exception as e:
            logger.error(f"Failed to start health server: {str(e)}")
            raise
    
    async def stop(self) -> None:
        """停止健康检查服务器"""
        logger.info("Stopping health server...")
        
        if self.site:
            await self.site.stop()
            self.site = None
        
        if self.runner:
            await self.runner.cleanup()
            self.runner = None
        
        self.app = None
        logger.info("Health server stopped")
    
    async def health_check_handler(self, request: web_request.Request) -> Response:
        """基本健康检查端点"""
        try:
            health = await self.health_service.check_system_health()
            
            status_code = 200
            if health.status.value == 'unhealthy':
                status_code = 503
            elif health.status.value == 'degraded':
                status_code = 200  # 降级状态仍返回200，但在响应体中标明
            
            response_data = {
                'status': health.status.value,
                'timestamp': health.timestamp.isoformat(),
                'uptime_seconds': health.uptime_seconds,
                'message': f"System is {health.status.value}"
            }
            
            return web.json_response(response_data, status=status_code)
            
        except Exception as e:
            logger.error(f"Health check handler error: {str(e)}")
            return web.json_response(
                {
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'message': f'Health check failed: {str(e)}'
                },
                status=500
            )
    
    async def detailed_health_handler(self, request: web_request.Request) -> Response:
        """详细健康检查端点"""
        try:
            health = await self.health_service.check_system_health()
            response_data = self.health_service.to_dict(health)
            
            status_code = 200
            if health.status.value == 'unhealthy':
                status_code = 503
            
            return web.json_response(response_data, status=status_code)
            
        except Exception as e:
            logger.error(f"Detailed health check handler error: {str(e)}")
            return web.json_response(
                {
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'message': f'Detailed health check failed: {str(e)}'
                },
                status=500
            )
    
    async def components_health_handler(self, request: web_request.Request) -> Response:
        """组件健康状态端点"""
        try:
            health = await self.health_service.check_system_health()
            
            components_data = [
                {
                    'name': comp.name,
                    'status': comp.status.value,
                    'message': comp.message,
                    'response_time_ms': comp.response_time_ms,
                    'last_check': comp.last_check.isoformat()
                }
                for comp in health.components
            ]
            
            return web.json_response({
                'components': components_data,
                'total_components': len(components_data),
                'timestamp': health.timestamp.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Components health handler error: {str(e)}")
            return web.json_response(
                {
                    'error': f'Components health check failed: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                },
                status=500
            )
    
    async def readiness_handler(self, request: web_request.Request) -> Response:
        """就绪检查端点（Kubernetes readiness probe）"""
        try:
            health = await self.health_service.check_system_health()
            
            # 就绪检查：所有关键组件都必须健康
            critical_components = ['configuration', 'archive_system', 'pulsar_connection']
            critical_unhealthy = [
                comp for comp in health.components 
                if comp.name in critical_components and comp.status.value == 'unhealthy'
            ]
            
            if critical_unhealthy:
                return web.json_response(
                    {
                        'ready': False,
                        'message': f"Critical components unhealthy: {[c.name for c in critical_unhealthy]}",
                        'timestamp': datetime.now().isoformat()
                    },
                    status=503
                )
            
            return web.json_response(
                {
                    'ready': True,
                    'message': 'Service is ready to accept traffic',
                    'timestamp': datetime.now().isoformat()
                },
                status=200
            )
            
        except Exception as e:
            logger.error(f"Readiness handler error: {str(e)}")
            return web.json_response(
                {
                    'ready': False,
                    'message': f'Readiness check failed: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                },
                status=503
            )
    
    async def liveness_handler(self, request: web_request.Request) -> Response:
        """存活检查端点（Kubernetes liveness probe）"""
        try:
            # 存活检查：只要服务能响应就认为存活
            return web.json_response(
                {
                    'alive': True,
                    'message': 'Service is alive',
                    'timestamp': datetime.now().isoformat(),
                    'uptime_seconds': (datetime.now() - self.health_service.start_time).total_seconds()
                },
                status=200
            )
            
        except Exception as e:
            logger.error(f"Liveness handler error: {str(e)}")
            return web.json_response(
                {
                    'alive': False,
                    'message': f'Liveness check failed: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                },
                status=500
            )
    
    async def info_handler(self, request: web_request.Request) -> Response:
        """应用信息端点"""
        try:
            return web.json_response(
                {
                    'name': self.config.app_name,
                    'version': self.config.app_version,
                    'description': 'HyDocPusher - 档案推送服务',
                    'start_time': self.health_service.start_time.isoformat(),
                    'uptime_seconds': (datetime.now() - self.health_service.start_time).total_seconds(),
                    'config': {
                        'pulsar_topic': self.config.pulsar.topic,
                        'archive_url': self.config.archive.api_url,
                        'debug_mode': self.config.debug
                    },
                    'endpoints': {
                        'health': '/health',
                        'detailed_health': '/health/detailed',
                        'components': '/health/components',
                        'readiness': '/ready',
                        'liveness': '/live',
                        'info': '/info'
                    }
                },
                status=200
            )
            
        except Exception as e:
            logger.error(f"Info handler error: {str(e)}")
            return web.json_response(
                {
                    'error': f'Info endpoint failed: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                },
                status=500
            )
    
    async def root_handler(self, request: web_request.Request) -> Response:
        """根路径处理器"""
        return web.json_response(
            {
                'service': self.config.app_name,
                'version': self.config.app_version,
                'message': 'Health monitoring service is running',
                'endpoints': {
                    'health': '/health',
                    'detailed_health': '/health/detailed',
                    'components': '/health/components',
                    'readiness': '/ready',
                    'liveness': '/live',
                    'info': '/info'
                },
                'timestamp': datetime.now().isoformat()
            },
            status=200
        )
    
    @web.middleware
    async def logging_middleware(self, request: web_request.Request, handler) -> Response:
        """请求日志中间件"""
        start_time = datetime.now()
        
        try:
            response = await handler(request)
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(
                f"Health API: {request.method} {request.path} -> {response.status} ({duration:.2f}ms)"
            )
            
            return response
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(
                f"Health API: {request.method} {request.path} -> ERROR ({duration:.2f}ms): {str(e)}"
            )
            raise
    
    @web.middleware
    async def cors_middleware(self, request: web_request.Request, handler) -> Response:
        """CORS中间件"""
        response = await handler(request)
        
        # 添加CORS头
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response


# 全局健康服务器实例
_health_server_instance: Optional[HealthServer] = None


def get_health_server() -> HealthServer:
    """获取健康服务器实例"""
    global _health_server_instance
    if _health_server_instance is None:
        _health_server_instance = HealthServer()
    return _health_server_instance


async def start_health_server(
    host: str = None,
    port: int = None,
    health_service: Optional[HealthService] = None
) -> HealthServer:
    """启动健康检查服务器"""
    server = HealthServer(health_service)
    await server.start(host, port)
    return server