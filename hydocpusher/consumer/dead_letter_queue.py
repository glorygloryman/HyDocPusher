"""
死信队列管理类
负责处理失败消息，将其发送到死信队列以便后续处理
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import pulsar
from pulsar import Producer as PulsarProducer

from ..config.settings import AppConfig
from ..exceptions.custom_exceptions import MessageProcessException

logger = logging.getLogger(__name__)


class DeadLetterQueue:
    """死信队列管理类"""
    
    def __init__(
        self,
        config: AppConfig,
        client: Optional[pulsar.Client] = None
    ):
        """
        初始化死信队列管理器
        
        Args:
            config: 应用配置
            client: Pulsar客户端实例（可选）
        """
        self.config = config
        self._client = client
        self._producer: Optional[PulsarProducer] = None
        self._own_client = client is None
        
    async def initialize(self) -> None:
        """
        初始化死信队列
        
        Raises:
            Exception: 初始化失败时抛出异常
        """
        try:
            logger.info(f"Initializing dead letter queue: {self.config.pulsar.dead_letter_topic}")
            
            # 如果未提供客户端，创建自己的客户端
            if self._own_client and not self._client:
                self._client = pulsar.Client(
                    service_url=self.config.pulsar.cluster_url,
                    operation_timeout_seconds=30,
                    connection_timeout_ms=10000
                )
            
            # 创建生产者
            if self._client:
                self._producer = self._client.create_producer(
                    topic=self.config.pulsar.dead_letter_topic,
                    producer_name=f"{self.config.app_name}-dlq-producer",
                    batching_enabled=True,
                    batching_max_publish_delay_ms=10,
                    compression_type=pulsar.CompressionType.LZ4
                )
                
            logger.info("Dead letter queue initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize dead letter queue: {str(e)}")
            raise
    
    async def send_to_dlq(
        self,
        original_message: Dict[str, Any],
        error: Exception,
        retry_count: int = 0,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        将失败消息发送到死信队列
        
        Args:
            original_message: 原始消息数据
            error: 错误信息
            retry_count: 重试次数
            additional_context: 额外上下文信息
            
        Raises:
            MessageProcessException: 发送到死信队列失败时抛出异常
        """
        try:
            if not self._producer:
                logger.warning("Dead letter queue producer not initialized, skipping DLQ send")
                return
            
            # 构建死信消息
            dlq_message = self._build_dlq_message(
                original_message, error, retry_count, additional_context
            )
            
            # 序列化消息
            message_json = json.dumps(dlq_message, ensure_ascii=False, default=str)
            
            # 发送到死信队列
            self._producer.send(
                message_json.encode('utf-8'),
                properties={
                    "original_topic": self.config.pulsar.topic,
                    "error_type": type(error).__name__,
                    "retry_count": str(retry_count),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            logger.info(f"Message sent to dead letter queue: {dlq_message.get('message_id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to send message to dead letter queue: {str(e)}")
            raise MessageProcessException(
                f"Failed to send message to dead letter queue: {str(e)}",
                cause=e
            )
    
    def _build_dlq_message(
        self,
        original_message: Dict[str, Any],
        error: Exception,
        retry_count: int,
        additional_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        构建死信消息
        
        Args:
            original_message: 原始消息数据
            error: 错误信息
            retry_count: 重试次数
            additional_context: 额外上下文信息
            
        Returns:
            死信消息数据
        """
        # 获取消息ID
        message_id = "unknown"
        if isinstance(original_message, dict):
            data = original_message.get("DATA", {})
            if isinstance(data, dict):
                message_id = data.get("DOCID", "unknown")
        
        # 构建错误信息
        error_info = {
            "type": type(error).__name__,
            "message": str(error),
            "timestamp": datetime.now().isoformat()
        }
        
        # 如果异常有错误码，添加错误码
        if hasattr(error, 'error_code'):
            error_info["error_code"] = error.error_code
        
        # 构建完整的死信消息
        dlq_message = {
            "message_id": message_id,
            "original_message": original_message,
            "error": error_info,
            "retry_count": retry_count,
            "dlq_timestamp": datetime.now().isoformat(),
            "application": {
                "name": self.config.app_name,
                "version": self.config.app_version
            }
        }
        
        # 添加额外上下文
        if additional_context:
            dlq_message["context"] = additional_context
        
        return dlq_message
    
    async def get_dlq_stats(self) -> Dict[str, Any]:
        """
        获取死信队列统计信息
        
        Returns:
            统计信息
        """
        return {
            "topic": self.config.pulsar.dead_letter_topic,
            "initialized": self._producer is not None,
            "producer_connected": self._producer is not None
        }
    
    async def close(self) -> None:
        """
        优雅关闭死信队列管理器
        """
        logger.info("Closing dead letter queue manager...")
        
        try:
            # 关闭生产者
            if self._producer:
                self._producer.close()
                self._producer = None
                logger.info("Dead letter queue producer closed")
            
            # 如果拥有自己的客户端，关闭客户端
            if self._own_client and self._client:
                self._client.close()
                self._client = None
                logger.info("Dead letter queue client closed")
                
        except Exception as e:
            logger.error(f"Error closing dead letter queue manager: {str(e)}")


class DeadLetterMessage:
    """死信消息模型"""
    
    def __init__(
        self,
        message_id: str,
        original_message: Dict[str, Any],
        error_type: str,
        error_message: str,
        retry_count: int = 0,
        timestamp: Optional[datetime] = None
    ):
        """
        初始化死信消息
        
        Args:
            message_id: 消息ID
            original_message: 原始消息
            error_type: 错误类型
            error_message: 错误消息
            retry_count: 重试次数
            timestamp: 时间戳
        """
        self.message_id = message_id
        self.original_message = original_message
        self.error_type = error_type
        self.error_message = error_message
        self.retry_count = retry_count
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            字典格式数据
        """
        return {
            "message_id": self.message_id,
            "original_message": self.original_message,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp.isoformat()
        }