#!/usr/bin/env python3
"""
真实Pulsar消息发送测试脚本
用于验证与真实Pulsar环境的连接和消息发送功能
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pulsar
from hydocpusher.config.settings import get_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class PulsarProducerTest:
    """Pulsar生产者测试类"""
    
    def __init__(self):
        self.config = get_config()
        self.client = None
        self.producer = None
    
    async def connect(self):
        """连接到Pulsar集群"""
        try:
            logger.info(f"正在连接到Pulsar集群: {self.config.pulsar.cluster_url}")
            
            # 构建客户端配置
            client_config = {
                'service_url': self.config.pulsar.cluster_url,
                'connection_timeout_ms': self.config.pulsar.connection_timeout,
                'operation_timeout_seconds': self.config.pulsar.operation_timeout // 1000
            }
            
            # 如果配置了认证信息，添加认证配置
            if self.config.pulsar.has_authentication():
                logger.info(f"使用认证信息: {self.config.pulsar.username}")
                client_config['authentication'] = pulsar.AuthenticationBasic(
                    self.config.pulsar.username,
                    self.config.pulsar.password
                )
            
            # 创建客户端
            self.client = pulsar.Client(**client_config)
            
            # 获取完整的Topic名称
            topic_name = self.config.pulsar.get_full_topic_name()
            logger.info(f"创建生产者，Topic: {topic_name}")
            
            # 创建生产者
            self.producer = self.client.create_producer(
                topic=topic_name,
                producer_name="hydocpusher-test-producer",
                send_timeout_millis=30000
            )
            
            logger.info("成功连接到Pulsar集群并创建生产者")
            return True
            
        except Exception as e:
            logger.error(f"连接Pulsar失败: {str(e)}")
            return False
    
    def create_test_message(self, message_id: str = None) -> dict:
        """创建测试消息"""
        if message_id is None:
            message_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            "MSG": "SUCCESS",
            "DATA": {
                "SITENAME": "云南省能源投资集团有限公司",
                "CRTIME": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "CHANNELID": "2240",
                "VIEWID": "123456",
                "DOCID": message_id,
                "OPERTYPE": "ADD",
                "DOCTITLE": "测试消息标题",
                "DOCCONTENT": "这是一条测试消息内容",
                "DOCPUBURL": f"http://www.cnyeig.com/news/{message_id}.html",
                "CHNLDOC": {
                    "CHANNELNAME": "新闻头条",
                    "CHANNELID": "2240"
                },
                "APPENDIX": [
                    {
                        "APPNAME": "测试图片.jpg",
                        "APPURL": "/upload/images/test.jpg",
                        "APPFLAG": "40"
                    }
                ]
            },
            "ISSUCCESS": True
        }
    
    async def send_message(self, message: dict) -> bool:
        """发送消息"""
        try:
            if not self.producer:
                logger.error("生产者未初始化")
                return False
            
            # 将消息转换为JSON字符串
            message_json = json.dumps(message, ensure_ascii=False, indent=2)
            logger.info(f"发送消息: {message['DATA']['DOCID']}")
            logger.debug(f"消息内容: {message_json}")
            
            # 发送消息
            message_id = self.producer.send(
                content=message_json.encode('utf-8'),
                properties={
                    'message_type': 'content_publish',
                    'doc_id': message['DATA']['DOCID'],
                    'channel_id': message['DATA']['CHANNELID'],
                    'timestamp': str(int(datetime.now().timestamp()))
                }
            )
            
            logger.info(f"消息发送成功，Message ID: {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"发送消息失败: {str(e)}")
            return False
    
    async def send_batch_messages(self, count: int = 5) -> int:
        """批量发送测试消息"""
        success_count = 0
        
        for i in range(count):
            message = self.create_test_message(f"batch_test_{i+1}")
            if await self.send_message(message):
                success_count += 1
            
            # 间隔1秒发送下一条消息
            if i < count - 1:
                await asyncio.sleep(1)
        
        logger.info(f"批量发送完成，成功: {success_count}/{count}")
        return success_count
    
    async def close(self):
        """关闭连接"""
        try:
            if self.producer:
                self.producer.close()
                logger.info("生产者已关闭")
            
            if self.client:
                self.client.close()
                logger.info("客户端已关闭")
                
        except Exception as e:
            logger.error(f"关闭连接时出错: {str(e)}")


async def main():
    """主函数"""
    logger.info("开始Pulsar生产者测试")
    
    # 检查环境变量
    if not os.getenv('PULSAR_CLUSTER_URL'):
        logger.warning("未设置PULSAR_CLUSTER_URL环境变量，将使用默认配置")
    
    producer_test = PulsarProducerTest()
    
    try:
        # 连接到Pulsar
        if not await producer_test.connect():
            logger.error("无法连接到Pulsar，测试终止")
            return False
        
        # 发送单条测试消息
        logger.info("\n=== 发送单条测试消息 ===")
        test_message = producer_test.create_test_message("single_test")
        success = await producer_test.send_message(test_message)
        
        if success:
            logger.info("单条消息发送测试通过")
        else:
            logger.error("单条消息发送测试失败")
            return False
        
        # 批量发送测试消息
        logger.info("\n=== 批量发送测试消息 ===")
        success_count = await producer_test.send_batch_messages(3)
        
        if success_count == 3:
            logger.info("批量消息发送测试通过")
        else:
            logger.warning(f"批量消息发送部分成功: {success_count}/3")
        
        logger.info("\n=== Pulsar生产者测试完成 ===")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中出现异常: {str(e)}")
        return False
        
    finally:
        await producer_test.close()


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    
    if success:
        logger.info("所有测试通过")
        sys.exit(0)
    else:
        logger.error("测试失败")
        sys.exit(1)