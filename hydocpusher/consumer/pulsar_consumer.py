"""
Pulsar消费者类
负责连接到Pulsar集群，订阅Topic，接收和处理消息
"""

import asyncio
import json
import logging
from typing import Optional, Callable, Dict, Any, Awaitable
from contextlib import asynccontextmanager
import pulsar
from pulsar import Consumer as PulsarConsumerClient, Message as PulsarMessage

from ..config.settings import AppConfig
from ..exceptions.custom_exceptions import ConnectionException, MessageProcessException

logger = logging.getLogger(__name__)


class PulsarConsumer:
    """Pulsar消息消费者类"""
    
    def __init__(
        self,
        config: AppConfig,
        message_handler: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    ):
        """
        初始化Pulsar消费者
        
        Args:
            config: 应用配置
            message_handler: 消息处理回调函数
        """
        self.config = config
        self.message_handler = message_handler
        self._client: Optional[pulsar.Client] = None
        self._consumer: Optional[PulsarConsumerClient] = None
        self._running = False
        self._connection_retry_count = 0
        self._max_connection_retries = 3
        self._connection_retry_delay = 5  # 秒
        
    async def connect(self) -> None:
        """
        连接到Pulsar集群并订阅Topic
        
        Raises:
            ConnectionException: 连接失败时抛出异常
        """
        try:
            logger.info(f"Connecting to Pulsar cluster: {self.config.pulsar.cluster_url}")
            
            # 创建Pulsar客户端
            self._client = pulsar.Client(
                service_url=self.config.pulsar.cluster_url,
                operation_timeout_seconds=30,
                connection_timeout_ms=10000,
                authentication=None,
                logger=logger
            )
            
            # 创建消费者
            self._consumer = self._client.subscribe(
                topic=self.config.pulsar.topic,
                subscription_name=self.config.pulsar.subscription,
                consumer_type=pulsar.ConsumerType.Shared,
                initial_position=pulsar.InitialPosition.Earliest,
                negative_ack_redelivery_delay_ms=60000,  # 60秒后重新投递
                ack_timeout_ms=300000,  # 5分钟确认超时
                max_total_receiver_queue_size_across_partitions=50000
            )
            
            self._connection_retry_count = 0
            logger.info(f"Successfully connected to Pulsar and subscribed to topic: {self.config.pulsar.topic}")
            
        except Exception as e:
            self._connection_retry_count += 1
            logger.error(f"Failed to connect to Pulsar (attempt {self._connection_retry_count}): {str(e)}")
            
            if self._connection_retry_count >= self._max_connection_retries:
                raise ConnectionException(
                    f"Failed to connect to Pulsar after {self._max_connection_retries} attempts",
                    cause=e
                )
            
            # 等待后重试
            logger.info(f"Retrying connection in {self._connection_retry_delay} seconds...")
            await asyncio.sleep(self._connection_retry_delay)
            await self.connect()  # 递归重试
    
    async def start_consuming(self) -> None:
        """
        开始消费消息
        
        Raises:
            ConnectionException: 如果未连接到Pulsar
        """
        if not self._consumer:
            raise ConnectionException("Not connected to Pulsar. Call connect() first.")
        
        self._running = True
        logger.info("Starting message consumption...")
        
        try:
            while self._running:
                try:
                    # 接收消息（非阻塞方式）
                    message = self._consumer.receive(timeout_millis=1000)
                    
                    if message:
                        await self._process_message(message)
                        
                except pulsar.Timeout:
                    # 超时是正常情况，继续循环
                    await asyncio.sleep(0.1)
                    continue
                    
                except Exception as e:
                    logger.error(f"Error receiving message: {str(e)}")
                    await asyncio.sleep(1)  # 出错后等待1秒
                    
        except asyncio.CancelledError:
            logger.info("Message consumption cancelled")
            raise
        except Exception as e:
            logger.error(f"Fatal error in message consumption: {str(e)}")
            raise
    
    async def _process_message(self, message: PulsarMessage) -> None:
        """
        处理单个消息
        
        Args:
            message: Pulsar消息
        """
        message_id = message.message_id()
        
        try:
            logger.debug(f"Processing message: {message_id}")
            
            # 解析消息内容
            message_data = self._parse_message(message)
            if not message_data:
                return
            
            # 调用消息处理器
            if self.message_handler:
                await self.message_handler(message_data)
            
            # 确认消息
            self._consumer.acknowledge(message)
            logger.debug(f"Message processed successfully: {message_id}")
            
        except MessageProcessException as e:
            # 消息处理异常，发送到死信队列或否定确认
            logger.error(f"Message processing failed: {message_id}, error: {str(e)}")
            self._handle_processing_error(message, e)
            
        except Exception as e:
            # 其他异常
            logger.error(f"Unexpected error processing message: {message_id}, error: {str(e)}")
            self._handle_processing_error(message, e)
    
    def _parse_message(self, message: PulsarMessage) -> Optional[Dict[str, Any]]:
        """
        解析消息内容
        
        Args:
            message: Pulsar消息
            
        Returns:
            解析后的消息数据，如果解析失败返回None
        """
        try:
            # 获取消息数据
            data = message.data()
            if not data:
                logger.warning(f"Empty message data: {message.message_id()}")
                return None
            
            # 解析JSON
            json_str = data.decode('utf-8')
            message_data = json.loads(json_str)
            
            logger.debug(f"Successfully parsed message: {message.message_id()}")
            return message_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message JSON: {message.message_id()}, error: {str(e)}")
            return None
            
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode message data: {message.message_id()}, error: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error parsing message: {message.message_id()}, error: {str(e)}")
            return None
    
    def _handle_processing_error(self, message: PulsarMessage, error: Exception) -> None:
        """
        处理消息处理错误
        
        Args:
            message: Pulsar消息
            error: 异常信息
        """
        try:
            # 否定确认消息，使其重新投递
            self._consumer.negative_acknowledge(message)
            logger.info(f"Message negatively acknowledged for redelivery: {message.message_id()}")
            
        except Exception as e:
            logger.error(f"Failed to handle processing error: {message.message_id()}, error: {str(e)}")
    
    async def close(self) -> None:
        """
        优雅关闭消费者
        """
        logger.info("Closing Pulsar consumer...")
        self._running = False
        
        try:
            # 关闭消费者
            if self._consumer:
                self._consumer.close()
                self._consumer = None
                logger.info("Pulsar consumer closed")
            
            # 关闭客户端
            if self._client:
                self._client.close()
                self._client = None
                logger.info("Pulsar client closed")
                
        except Exception as e:
            logger.error(f"Error closing Pulsar consumer: {str(e)}")
    
    @property
    def is_connected(self) -> bool:
        """
        检查是否已连接
        
        Returns:
            True如果已连接，否则False
        """
        return self._consumer is not None and self._client is not None
    
    @property
    def is_running(self) -> bool:
        """
        检查是否正在运行
        
        Returns:
            True如果正在运行，否则False
        """
        return self._running
    
    def set_message_handler(self, handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """
        设置消息处理器
        
        Args:
            handler: 消息处理回调函数
        """
        self.message_handler = handler
    
    def get_consumer_stats(self) -> Dict[str, Any]:
        """
        获取消费者统计信息
        
        Returns:
            消费者统计信息
        """
        return {
            "connected": self.is_connected,
            "running": self.is_running,
            "connection_retries": self._connection_retry_count,
            "topic": self.config.pulsar.topic,
            "subscription": self.config.pulsar.subscription
        }