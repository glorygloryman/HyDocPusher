#!/usr/bin/env python3
"""
主应用入口点
集成所有模块，启动消息处理循环
"""

import asyncio
import logging
import signal
import sys
from typing import Optional
from contextlib import asynccontextmanager

from hydocpusher.config.settings import get_config
from hydocpusher.consumer.pulsar_consumer import PulsarConsumer
from hydocpusher.consumer.message_handler import MessageHandler
from hydocpusher.transformer.data_transformer import DataTransformer
from hydocpusher.client.archive_client import ArchiveClient
from hydocpusher.services.health_service import get_health_service
from hydocpusher.services.health_server import start_health_server
from hydocpusher.exceptions.custom_exceptions import (
    ConnectionException,
    ConfigurationException,
    MessageProcessException
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/hydocpusher.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


class HyDocPusherApp:
    """主应用类"""
    
    def __init__(self):
        """初始化应用"""
        self.config = get_config()
        self.running = False
        self.shutdown_event = asyncio.Event()
        
        # 核心组件
        self.data_transformer: Optional[DataTransformer] = None
        self.archive_client: Optional[ArchiveClient] = None
        self.message_handler: Optional[MessageHandler] = None
        self.pulsar_consumer: Optional[PulsarConsumer] = None
        
        # 健康检查组件
        self.health_service = get_health_service()
        self.health_server = None
        
        logger.info(f"Initializing {self.config.app_name} v{self.config.app_version}")
    
    async def initialize(self) -> None:
        """初始化所有组件"""
        try:
            logger.info("Initializing application components...")
            
            # 验证配置
            self.config.validate_required_configs()
            
            # 初始化数据转换器
            self.data_transformer = DataTransformer()
            logger.info("Data transformer initialized")
            
            # 初始化档案客户端
            self.archive_client = ArchiveClient()
            logger.info("Archive client initialized")
            
            # 初始化消息处理器
            self.message_handler = MessageHandler(
                data_transformer=self.data_transformer,
                archive_client=self.archive_client
            )
            logger.info("Message handler initialized")
            
            # 初始化Pulsar消费者
            self.pulsar_consumer = PulsarConsumer(
                config=self.config,
                message_handler=self.message_handler.handle_message
            )
            logger.info("Pulsar consumer initialized")
            
            # 配置健康检查服务
            self.health_service.set_components(
                archive_client=self.archive_client,
                pulsar_consumer=self.pulsar_consumer
            )
            logger.info("Health service configured")
            
            # 启动健康检查服务器
            self.health_server = await start_health_server(
                health_service=self.health_service
            )
            logger.info("Health server started")
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}")
            raise
    
    async def start(self) -> None:
        """启动应用"""
        try:
            logger.info("Starting HyDocPusher application...")
            
            # 连接到Pulsar
            await self.pulsar_consumer.connect()
            logger.info("Connected to Pulsar successfully")
            
            # 启动消息消费
            self.running = True
            await self.pulsar_consumer.start_consuming()
            
            logger.info("HyDocPusher application started successfully")
            
            # 等待关闭信号
            await self.shutdown_event.wait()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """关闭应用"""
        logger.info("Shutting down HyDocPusher application...")
        
        self.running = False
        
        # 关闭Pulsar消费者
        if self.pulsar_consumer:
            await self.pulsar_consumer.close()
            logger.info("Pulsar consumer closed")
        
        # 关闭档案客户端
        if self.archive_client:
            await self.archive_client.close_async()
            logger.info("Archive client closed")
        
        # 关闭健康检查服务器
        if self.health_server:
            await self.health_server.stop()
            logger.info("Health server stopped")
        
        logger.info("Application shutdown completed")
    
    def setup_signal_handlers(self) -> None:
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, signal_handler)
    
    def get_application_info(self) -> dict:
        """获取应用信息"""
        return {
            'name': self.config.app_name,
            'version': self.config.app_version,
            'running': self.running,
            'config': {
                'pulsar_url': self.config.pulsar.cluster_url,
                'pulsar_topic': self.config.pulsar.topic,
                'archive_url': self.config.archive.api_url,
                'debug_mode': self.config.debug
            }
        }


async def main() -> None:
    """主函数"""
    app = None
    
    try:
        # 创建应用实例
        app = HyDocPusherApp()
        
        # 设置信号处理器
        app.setup_signal_handlers()
        
        # 初始化应用
        await app.initialize()
        
        # 启动应用
        await app.start()
        
    except ConfigurationException as e:
        logger.error(f"Configuration error: {str(e)}")
        sys.exit(1)
    except ConnectionException as e:
        logger.error(f"Connection error: {str(e)}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(3)
    finally:
        if app:
            await app.shutdown()


if __name__ == "__main__":
    # 创建logs目录
    import os
    os.makedirs('logs', exist_ok=True)
    
    # 运行应用
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)