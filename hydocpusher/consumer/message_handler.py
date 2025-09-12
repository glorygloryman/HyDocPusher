"""
消息处理器类
负责验证、解析接收到的Pulsar消息，并调用数据转换器进行处理
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime

from ..models.message_models import SourceMessageSchema
from ..transformer.data_transformer import DataTransformer
from ..config.settings import AppConfig
from ..config.classification_config import ClassificationConfig
from ..exceptions.custom_exceptions import (
    ValidationException, MessageProcessException, DataTransformException
)

logger = logging.getLogger(__name__)


class MessageHandler:
    """消息处理器类"""
    
    def __init__(
        self,
        config: AppConfig,
        data_transformer: Optional[DataTransformer] = None,
        classification_config: Optional[ClassificationConfig] = None
    ):
        """
        初始化消息处理器
        
        Args:
            config: 应用配置
            data_transformer: 数据转换器实例
            classification_config: 分类配置实例
        """
        self.config = config
        self.data_transformer = data_transformer or DataTransformer()
        self.classification_config = classification_config
        self._processing_stats = {
            "processed": 0,
            "failed": 0,
            "retried": 0
        }
        
    async def handle_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理消息
        
        Args:
            message_data: 原始消息数据
            
        Returns:
            处理结果
            
        Raises:
            MessageProcessException: 消息处理失败时抛出异常
        """
        start_time = datetime.now()
        message_id = None
        
        try:
            logger.info(f"Starting message processing at {start_time}")
            
            # 1. 验证消息格式
            validated_message = await self._validate_message(message_data)
            message_id = validated_message.document_id
            
            logger.info(f"Processing message: {message_id}")
            
            # 2. 检查消息是否可以处理
            validated_message.validate_for_processing()
            
            # 3. 数据转换
            archive_data = await self._transform_data(validated_message)
            
            # 4. 记录成功统计
            self._processing_stats["processed"] += 1
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Message processed successfully: {message_id}, time: {processing_time:.2f}s")
            
            return {
                "success": True,
                "message_id": message_id,
                "processing_time": processing_time,
                "archive_data": archive_data
            }
            
        except ValidationException as e:
            # 验证异常，不重试
            self._processing_stats["failed"] += 1
            logger.error(f"Message validation failed: {message_id}, error: {str(e)}")
            raise MessageProcessException(f"Message validation failed: {str(e)}", cause=e)
            
        except DataTransformException as e:
            # 数据转换异常，可以重试
            self._processing_stats["failed"] += 1
            logger.error(f"Data transformation failed: {message_id}, error: {str(e)}")
            raise MessageProcessException(f"Data transformation failed: {str(e)}", cause=e)
            
        except Exception as e:
            # 其他未预期的异常
            self._processing_stats["failed"] += 1
            logger.error(f"Unexpected error processing message: {message_id}, error: {str(e)}")
            raise MessageProcessException(f"Unexpected error processing message: {str(e)}", cause=e)
    
    async def _validate_message(self, message_data: Dict[str, Any]) -> SourceMessageSchema:
        """
        验证消息格式
        
        Args:
            message_data: 原始消息数据
            
        Returns:
            验证后的消息模型
            
        Raises:
            ValidationException: 验证失败时抛出异常
        """
        try:
            logger.debug("Validating message format")
            
            # 检查必需字段
            required_fields = ["MSG", "DATA", "ISSUCCESS"]
            missing_fields = []
            
            for field in required_fields:
                if field not in message_data:
                    missing_fields.append(field)
            
            if missing_fields:
                raise ValidationException(f"Missing required fields: {', '.join(missing_fields)}")
            
            # 创建消息模型
            message_schema = SourceMessageSchema(**message_data)
            
            logger.debug(f"Message validation successful: {message_schema.document_id}")
            return message_schema
            
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Message validation failed: {str(e)}", cause=e)
    
    async def _transform_data(self, message: SourceMessageSchema) -> Dict[str, Any]:
        """
        转换数据
        
        Args:
            message: 验证后的消息
            
        Returns:
            转换后的档案数据
            
        Raises:
            DataTransformException: 转换失败时抛出异常
        """
        try:
            logger.debug(f"Transforming data for message: {message.document_id}")
            
            # 使用数据转换器进行转换
            archive_data = self.data_transformer.transform_message(message)
            
            logger.debug(f"Data transformation successful: {message.document_id}")
            return archive_data
            
        except DataTransformException:
            raise
        except Exception as e:
            raise DataTransformException(f"Data transformation failed: {str(e)}", cause=e)
    
    def set_data_transformer(self, transformer: DataTransformer) -> None:
        """
        设置数据转换器
        
        Args:
            transformer: 数据转换器实例
        """
        self.data_transformer = transformer
        logger.info("Data transformer updated")
    
    def set_classification_config(self, config: ClassificationConfig) -> None:
        """
        设置分类配置
        
        Args:
            config: 分类配置实例
        """
        self.classification_config = config
        logger.info("Classification config updated")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        Returns:
            处理统计信息
        """
        return self._processing_stats.copy()
    
    def reset_stats(self) -> None:
        """
        重置处理统计信息
        """
        self._processing_stats = {
            "processed": 0,
            "failed": 0,
            "retried": 0
        }
        logger.info("Processing stats reset")


class MessageProcessor:
    """消息处理器（兼容旧版本）"""
    
    def __init__(self, config: AppConfig):
        """
        初始化消息处理器
        
        Args:
            config: 应用配置
        """
        self.config = config
        self.handler = MessageHandler(config)
        
    async def process_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理消息（兼容接口）
        
        Args:
            message_data: 消息数据
            
        Returns:
            处理结果
        """
        return await self.handler.handle_message(message_data)
    
    @property
    def stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息
        """
        return self.handler.get_processing_stats()