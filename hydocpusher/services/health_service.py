#!/usr/bin/env python3
"""
健康检查服务模块
提供系统状态监控和健康检查API端点
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict

from ..config.settings import get_config
from ..client.archive_client import ArchiveClient
from ..consumer.pulsar_consumer import PulsarConsumer
from ..exceptions.custom_exceptions import HealthCheckException

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """组件健康状态"""
    name: str
    status: HealthStatus
    message: str
    last_check: datetime
    response_time_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class SystemHealth:
    """系统整体健康状态"""
    status: HealthStatus
    timestamp: datetime
    uptime_seconds: float
    components: List[ComponentHealth]
    summary: Dict[str, Any]


class HealthService:
    """健康检查服务类"""
    
    def __init__(self):
        """初始化健康检查服务"""
        self.config = get_config()
        self.start_time = datetime.now()
        self._last_health_check: Optional[SystemHealth] = None
        self._health_check_interval = 30  # 秒
        self._health_check_timeout = 10   # 秒
        
        # 组件引用
        self._archive_client: Optional[ArchiveClient] = None
        self._pulsar_consumer: Optional[PulsarConsumer] = None
        
        logger.info("Health service initialized")
    
    def set_components(
        self,
        archive_client: Optional[ArchiveClient] = None,
        pulsar_consumer: Optional[PulsarConsumer] = None
    ) -> None:
        """设置要监控的组件"""
        self._archive_client = archive_client
        self._pulsar_consumer = pulsar_consumer
        logger.info("Health service components configured")
    
    async def check_system_health(self) -> SystemHealth:
        """检查系统整体健康状态"""
        start_time = time.time()
        
        try:
            logger.debug("Starting system health check")
            
            # 检查各个组件
            components = []
            
            # 检查配置
            config_health = await self._check_configuration_health()
            components.append(config_health)
            
            # 检查档案系统连接
            if self._archive_client:
                archive_health = await self._check_archive_health()
                components.append(archive_health)
            
            # 检查Pulsar连接
            if self._pulsar_consumer:
                pulsar_health = await self._check_pulsar_health()
                components.append(pulsar_health)
            
            # 检查内存和资源
            resource_health = await self._check_resource_health()
            components.append(resource_health)
            
            # 计算整体状态
            overall_status = self._calculate_overall_status(components)
            
            # 计算运行时间
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            # 生成摘要
            summary = self._generate_health_summary(components, uptime)
            
            # 创建系统健康状态
            system_health = SystemHealth(
                status=overall_status,
                timestamp=datetime.now(),
                uptime_seconds=uptime,
                components=components,
                summary=summary
            )
            
            self._last_health_check = system_health
            
            check_duration = (time.time() - start_time) * 1000
            logger.info(f"System health check completed in {check_duration:.2f}ms, status: {overall_status.value}")
            
            return system_health
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return SystemHealth(
                status=HealthStatus.UNKNOWN,
                timestamp=datetime.now(),
                uptime_seconds=(datetime.now() - self.start_time).total_seconds(),
                components=[],
                summary={'error': str(e)}
            )
    
    async def _check_configuration_health(self) -> ComponentHealth:
        """检查配置健康状态"""
        start_time = time.time()
        
        try:
            # 验证关键配置
            self.config.validate_required_configs()
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name="configuration",
                status=HealthStatus.HEALTHY,
                message="Configuration is valid",
                last_check=datetime.now(),
                response_time_ms=response_time,
                details={
                    'app_name': self.config.app_name,
                    'app_version': self.config.app_version,
                    'debug_mode': self.config.debug
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="configuration",
                status=HealthStatus.UNHEALTHY,
                message=f"Configuration error: {str(e)}",
                last_check=datetime.now(),
                response_time_ms=response_time
            )
    
    async def _check_archive_health(self) -> ComponentHealth:
        """检查档案系统健康状态"""
        start_time = time.time()
        
        try:
            if not self._archive_client:
                return ComponentHealth(
                    name="archive_system",
                    status=HealthStatus.UNKNOWN,
                    message="Archive client not configured",
                    last_check=datetime.now()
                )
            
            # 执行健康检查
            health_result = await asyncio.wait_for(
                self._archive_client.health_check_async(),
                timeout=self._health_check_timeout
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if health_result.get('status') == 'healthy':
                return ComponentHealth(
                    name="archive_system",
                    status=HealthStatus.HEALTHY,
                    message="Archive system is accessible",
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    details=health_result
                )
            else:
                return ComponentHealth(
                    name="archive_system",
                    status=HealthStatus.DEGRADED,
                    message="Archive system responded but may have issues",
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    details=health_result
                )
                
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="archive_system",
                status=HealthStatus.UNHEALTHY,
                message="Archive system health check timed out",
                last_check=datetime.now(),
                response_time_ms=response_time
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="archive_system",
                status=HealthStatus.UNHEALTHY,
                message=f"Archive system error: {str(e)}",
                last_check=datetime.now(),
                response_time_ms=response_time
            )
    
    async def _check_pulsar_health(self) -> ComponentHealth:
        """检查Pulsar连接健康状态"""
        start_time = time.time()
        
        try:
            if not self._pulsar_consumer:
                return ComponentHealth(
                    name="pulsar_connection",
                    status=HealthStatus.UNKNOWN,
                    message="Pulsar consumer not configured",
                    last_check=datetime.now()
                )
            
            # 检查连接状态
            is_connected = self._pulsar_consumer.is_connected
            is_running = self._pulsar_consumer.is_running
            
            response_time = (time.time() - start_time) * 1000
            
            if is_connected and is_running:
                stats = self._pulsar_consumer.get_consumer_stats()
                return ComponentHealth(
                    name="pulsar_connection",
                    status=HealthStatus.HEALTHY,
                    message="Pulsar connection is active",
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    details=stats
                )
            elif is_connected:
                return ComponentHealth(
                    name="pulsar_connection",
                    status=HealthStatus.DEGRADED,
                    message="Pulsar connected but not consuming",
                    last_check=datetime.now(),
                    response_time_ms=response_time
                )
            else:
                return ComponentHealth(
                    name="pulsar_connection",
                    status=HealthStatus.UNHEALTHY,
                    message="Pulsar connection is down",
                    last_check=datetime.now(),
                    response_time_ms=response_time
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="pulsar_connection",
                status=HealthStatus.UNHEALTHY,
                message=f"Pulsar health check error: {str(e)}",
                last_check=datetime.now(),
                response_time_ms=response_time
            )
    
    async def _check_resource_health(self) -> ComponentHealth:
        """检查系统资源健康状态"""
        start_time = time.time()
        
        try:
            import psutil
            
            # 获取系统资源信息
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            response_time = (time.time() - start_time) * 1000
            
            # 判断资源状态
            status = HealthStatus.HEALTHY
            messages = []
            
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                messages.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 70:
                status = HealthStatus.DEGRADED
                messages.append(f"Elevated CPU usage: {cpu_percent:.1f}%")
            
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
                messages.append(f"High memory usage: {memory.percent:.1f}%")
            elif memory.percent > 70:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
                messages.append(f"Elevated memory usage: {memory.percent:.1f}%")
            
            if disk.percent > 95:
                status = HealthStatus.UNHEALTHY
                messages.append(f"High disk usage: {disk.percent:.1f}%")
            elif disk.percent > 80:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
                messages.append(f"Elevated disk usage: {disk.percent:.1f}%")
            
            message = "; ".join(messages) if messages else "System resources are normal"
            
            return ComponentHealth(
                name="system_resources",
                status=status,
                message=message,
                last_check=datetime.now(),
                response_time_ms=response_time,
                details={
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_percent': disk.percent,
                    'disk_free_gb': disk.free / (1024**3)
                }
            )
            
        except ImportError:
            # psutil不可用时的降级处理
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message="Resource monitoring not available (psutil not installed)",
                last_check=datetime.now(),
                response_time_ms=response_time
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message=f"Resource check error: {str(e)}",
                last_check=datetime.now(),
                response_time_ms=response_time
            )
    
    def _calculate_overall_status(self, components: List[ComponentHealth]) -> HealthStatus:
        """计算整体健康状态"""
        if not components:
            return HealthStatus.UNKNOWN
        
        statuses = [comp.status for comp in components]
        
        # 如果有任何组件不健康，整体状态为不健康
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        
        # 如果有任何组件降级，整体状态为降级
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        
        # 如果有未知状态，整体状态为降级
        if HealthStatus.UNKNOWN in statuses:
            return HealthStatus.DEGRADED
        
        # 所有组件都健康
        return HealthStatus.HEALTHY
    
    def _generate_health_summary(self, components: List[ComponentHealth], uptime: float) -> Dict[str, Any]:
        """生成健康状态摘要"""
        status_counts = {}
        for status in HealthStatus:
            status_counts[status.value] = sum(1 for comp in components if comp.status == status)
        
        avg_response_time = None
        response_times = [comp.response_time_ms for comp in components if comp.response_time_ms is not None]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
        
        return {
            'total_components': len(components),
            'status_counts': status_counts,
            'uptime_hours': uptime / 3600,
            'average_response_time_ms': avg_response_time,
            'last_check': datetime.now().isoformat()
        }
    
    def get_last_health_check(self) -> Optional[SystemHealth]:
        """获取最后一次健康检查结果"""
        return self._last_health_check
    
    def to_dict(self, system_health: SystemHealth) -> Dict[str, Any]:
        """将健康状态转换为字典"""
        return {
            'status': system_health.status.value,
            'timestamp': system_health.timestamp.isoformat(),
            'uptime_seconds': system_health.uptime_seconds,
            'components': [
                {
                    'name': comp.name,
                    'status': comp.status.value,
                    'message': comp.message,
                    'last_check': comp.last_check.isoformat(),
                    'response_time_ms': comp.response_time_ms,
                    'details': comp.details
                }
                for comp in system_health.components
            ],
            'summary': system_health.summary
        }


# 全局健康服务实例
_health_service_instance: Optional[HealthService] = None


def get_health_service() -> HealthService:
    """获取健康服务实例"""
    global _health_service_instance
    if _health_service_instance is None:
        _health_service_instance = HealthService()
    return _health_service_instance