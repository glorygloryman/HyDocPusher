#!/usr/bin/env python3
"""
端到端集成测试脚本
验证完整的消息发送和消费流程
"""

import asyncio
import json
import logging
import sys
import os
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pulsar
from hydocpusher.config.settings import get_config
from hydocpusher.transformer.data_transformer import DataTransformer
from hydocpusher.config.classification_config import ClassificationConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class EndToEndTest:
    """端到端测试类"""
    
    def __init__(self):
        self.config = get_config()
        self.client = None
        self.producer = None
        self.consumer = None
        self.sent_messages: List[Dict] = []
        self.received_messages: List[Dict] = []
        
        # 初始化数据转换器
        try:
            self.transformer = DataTransformer()
            logger.info("数据转换器初始化成功")
        except Exception as e:
            logger.warning(f"数据转换器初始化失败: {str(e)}")
            self.transformer = None
    
    async def setup(self):
        """设置测试环境"""
        try:
            logger.info("设置测试环境...")
            
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
            logger.info(f"使用Topic: {topic_name}")
            
            # 创建生产者
            self.producer = self.client.create_producer(
                topic=topic_name,
                producer_name="hydocpusher-e2e-producer",
                send_timeout_millis=30000
            )
            logger.info("生产者创建成功")
            
            # 创建消费者
            subscription_name = f"{self.config.pulsar.subscription}-e2e-test"
            self.consumer = self.client.subscribe(
                topic=topic_name,
                subscription_name=subscription_name,
                consumer_type=pulsar.ConsumerType.Shared,
                consumer_name="hydocpusher-e2e-consumer",
                initial_position=pulsar.InitialPosition.Latest
            )
            logger.info(f"消费者创建成功，订阅: {subscription_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"设置测试环境失败: {str(e)}")
            return False
    
    def create_test_messages(self) -> List[Dict]:
        """创建测试消息（使用真实的示例数据结构）"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        messages = [
            {
                "MSG": "操作成功",
                "DATA": {
                    "SITENAME": "测试推送",
                    "CRTIME": "2025-08-29 18:53:15",
                    "CHANNELID": "2240",
                    "VIEWID": "11",
                    "VIEWNAME": "GovDocNewsAPP",
                    "SITEID": "33",
                    "DOCID": f"e2e_test_news_{timestamp}",
                    "OPERTYPE": "1",
                    "CHANNELNAV": "2240",
                    "DATA": {
                        "DOCTITLE": "端到端测试新闻标题",
                        "DOCCONTENT": "这是一条端到端测试新闻内容，用于验证完整的消息处理流程。",
                        "DOCAUTHOR": "测试部门",
                        "DOCRELTIME": "2025-04-09 15:46:25",
                        "DOCPUBURL": f"https://www.cnyeig.com/csts/test_2240/202508/t{timestamp}_64941.html",
                        "ATTACHPIC": "1",
                        "THUMBFILES": "test_image.jpg",
                        "MEDIATYPE": "1",
                        "SITENAME": "测试推送",
                        "CHANNELID": "2240",
                        "SITEID": "33",
                        "PUBSTATUS": "1"
                    },
                    "CHNLDOC": {
                        "DOCSTATUS": "10",
                        "PUBSTATUS": "1",
                        "DOCID": f"e2e_test_news_{timestamp}",
                        "CHNLID": "2240",
                        "SITEID": "33"
                    },
                    "APPENDIX": [
                        {
                            "APPFILE": "test_image.jpg",
                            "APPFLAG": "20"
                        },
                        {
                            "APPFILE": "test_video.mp4",
                            "APPFLAG": "50"
                        }
                    ],
                    "ID": "84085",
                    "CHANNELDESCNAV": "数字能投推送测试",
                    "TYPE": "1"
                },
                "ISSUCCESS": "true"
            },
            {
                "MSG": "操作成功",
                "DATA": {
                    "SITENAME": "测试推送2",
                    "CRTIME": "2025-08-29 19:00:00",
                    "CHANNELID": "2241",
                    "VIEWID": "12",
                    "VIEWNAME": "GovDocNewsAPP",
                    "SITEID": "34",
                    "DOCID": f"e2e_test_notice_{timestamp}",
                    "OPERTYPE": "2",
                    "CHANNELNAV": "2241",
                    "DATA": {
                        "DOCTITLE": "端到端测试通知公告",
                        "DOCCONTENT": "这是一条端到端测试通知公告内容。",
                        "DOCAUTHOR": "行政部",
                        "DOCRELTIME": "2025-04-10 10:00:00",
                        "DOCPUBURL": f"https://www.cnyeig.com/csts/test_2241/202508/t{timestamp}_64942.html",
                        "MEDIATYPE": "1",
                        "ATTACHPIC": "1",
                        "THUMBFILES": "notice_doc.jpg",
                        "SITENAME": "测试推送2",
                        "CHANNELID": "2241",
                        "SITEID": "34",
                        "PUBSTATUS": "1"
                    },
                    "CHNLDOC": {
                        "DOCSTATUS": "10",
                        "PUBSTATUS": "1",
                        "DOCID": f"e2e_test_notice_{timestamp}",
                        "CHNLID": "2241",
                        "SITEID": "34"
                    },
                    "APPENDIX": [
                        {
                            "APPFILE": "test_document.pdf",
                            "APPFLAG": "30"
                        }
                    ]
                },
                "ISSUCCESS": "true"
            },
            {
                "MSG": "操作成功",
                "DATA": {
                    "SITENAME": "测试推送3",
                    "CRTIME": "2025-08-29 20:15:30",
                    "CHANNELID": "9999",  # 不存在的频道，测试默认分类
                    "VIEWID": "13",
                    "VIEWNAME": "GovDocNewsAPP",
                    "SITEID": "35",
                    "DOCID": f"e2e_test_unknown_{timestamp}",
                    "OPERTYPE": "3",
                    "CHANNELNAV": "9999",
                    "DATA": {
                        "DOCTITLE": "端到端测试未知分类内容",
                        "DOCCONTENT": "这是一条测试未知分类的内容，用于验证默认分类处理。",
                        "DOCAUTHOR": "测试部门",
                        "DOCRELTIME": "2025-04-11 14:30:00",
                        "DOCPUBURL": f"https://www.cnyeig.com/csts/test_9999/202508/t{timestamp}_64943.html",
                        "MEDIATYPE": "1",
                        "SITENAME": "测试推送3",
                        "CHANNELID": "9999",
                        "SITEID": "35",
                        "PUBSTATUS": "1"
                    },
                    "CHNLDOC": {
                        "DOCSTATUS": "10",
                        "PUBSTATUS": "1",
                        "DOCID": f"e2e_test_unknown_{timestamp}",
                        "CHNLID": "9999",
                        "SITEID": "35"
                    },
                    "APPENDIX": []
                },
                "ISSUCCESS": "true"
            }
        ]
        
        return messages
    
    async def send_messages(self, messages: List[Dict]) -> bool:
        """发送测试消息"""
        try:
            logger.info(f"发送 {len(messages)} 条测试消息...")
            
            for i, message in enumerate(messages):
                message_json = json.dumps(message, ensure_ascii=False)
                doc_id = message['DATA']['DOCID']
                
                logger.info(f"=== 发送消息 {i+1}/{len(messages)} ===")
                logger.info(f"文档ID: {doc_id}")
                logger.info(f"频道ID: {message['DATA']['CHANNELID']}")
                logger.info(f"操作类型: {message['DATA']['OPERTYPE']}")
                logger.info(f"消息大小: {len(message_json)} 字节")
                
                # 记录HTTP请求详情
                start_time = time.time()
                message_id = self.producer.send(
                    content=message_json.encode('utf-8'),
                    properties={
                        'message_type': 'e2e_test',
                        'doc_id': doc_id,
                        'channel_id': message['DATA']['CHANNELID'],
                        'timestamp': str(int(datetime.now().timestamp())),
                        'test_sequence': str(i)
                    }
                )
                end_time = time.time()
                
                self.sent_messages.append({
                    'message_id': str(message_id),
                    'doc_id': doc_id,
                    'data': message
                })
                
                logger.info(f"✅ 消息发送成功")
                logger.info(f"Message ID: {message_id}")
                logger.info(f"发送耗时: {end_time - start_time:.3f}秒")
                logger.info(f"=== 消息发送完成 ===")
                
                # 间隔发送
                if i < len(messages) - 1:
                    await asyncio.sleep(1)
            
            logger.info(f"所有消息发送完成，共 {len(self.sent_messages)} 条")
            return True
            
        except Exception as e:
            logger.error(f"发送消息失败: {str(e)}")
            return False
    
    async def consume_messages(self, expected_count: int, timeout_seconds: int = 30) -> bool:
        """消费测试消息"""
        try:
            logger.info(f"开始消费消息，期望接收 {expected_count} 条，超时 {timeout_seconds} 秒")
            
            start_time = time.time()
            
            while len(self.received_messages) < expected_count:
                # 检查超时
                if time.time() - start_time > timeout_seconds:
                    logger.warning(f"消费超时，已接收 {len(self.received_messages)}/{expected_count} 条消息")
                    break
                
                try:
                    # 接收消息
                    msg = self.consumer.receive(timeout_millis=5000)
                    
                    if msg:
                        logger.info(f"接收到消息: {msg.message_id()}")
                        
                        # 检查是否是测试消息
                        properties = msg.properties()
                        if properties.get('message_type') == 'e2e_test':
                            try:
                                # 解析消息内容
                                message_content = msg.data().decode('utf-8')
                                message_data = json.loads(message_content)
                                
                                doc_id = message_data['DATA']['DOCID']
                                logger.info(f"=== 处理测试消息 ===")
                                logger.info(f"文档ID: {doc_id}")
                                logger.info(f"消息大小: {len(message_content)} 字节")
                                logger.info(f"频道ID: {message_data['DATA']['CHANNELID']}")
                                logger.info(f"操作类型: {message_data['DATA']['OPERTYPE']}")
                                
                                # 验证和处理消息
                                processed_data = None
                                if self.transformer:
                                    try:
                                        transform_start = time.time()
                                        processed_data = self.transformer.transform(message_data)
                                        transform_end = time.time()
                                        logger.info(f"✅ 数据转换成功")
                                        logger.info(f"转换后标题: {processed_data.get('title', 'Unknown')}")
                                        logger.info(f"转换耗时: {transform_end - transform_start:.3f}秒")
                                    except Exception as e:
                                        logger.error(f"❌ 数据转换失败: {str(e)}")
                                        logger.error(f"异常类型: {type(e).__name__}")
                                        logger.error(f"异常堆栈: {traceback.format_exc()}")
                                
                                self.received_messages.append({
                                    'message_id': str(msg.message_id()),
                                    'doc_id': doc_id,
                                    'properties': properties,
                                    'original_data': message_data,
                                    'processed_data': processed_data
                                })
                                
                                # 确认消息
                                self.consumer.acknowledge(msg)
                                logger.info(f"✅ 消息处理完成: {doc_id}")
                                logger.info(f"=== 消息处理结束 ===")
                                
                            except Exception as e:
                                logger.error(f"❌ 处理消息时出错: {str(e)}")
                                logger.error(f"异常类型: {type(e).__name__}")
                                logger.error(f"异常详情: {str(e)}")
                                logger.error(f"异常堆栈: {traceback.format_exc()}")
                                self.consumer.negative_acknowledge(msg)
                        else:
                            # 不是测试消息，确认并跳过
                            self.consumer.acknowledge(msg)
                            logger.debug("跳过非测试消息")
                
                except pulsar.Timeout:
                    # 超时是正常的，继续循环
                    continue
                    
                except Exception as e:
                    logger.error(f"接收消息时出错: {str(e)}")
                    await asyncio.sleep(1)
            
            logger.info(f"消费完成，接收到 {len(self.received_messages)} 条消息")
            return len(self.received_messages) == expected_count
            
        except Exception as e:
            logger.error(f"消费消息失败: {str(e)}")
            return False
    
    def verify_results(self) -> bool:
        """验证测试结果"""
        try:
            logger.info("\n=== 验证测试结果 ===")
            
            sent_count = len(self.sent_messages)
            received_count = len(self.received_messages)
            
            logger.info(f"发送消息数: {sent_count}")
            logger.info(f"接收消息数: {received_count}")
            
            if sent_count != received_count:
                logger.error(f"消息数量不匹配: 发送 {sent_count}, 接收 {received_count}")
                return False
            
            # 验证每条消息
            sent_doc_ids = {msg['doc_id'] for msg in self.sent_messages}
            received_doc_ids = {msg['doc_id'] for msg in self.received_messages}
            
            missing_messages = sent_doc_ids - received_doc_ids
            extra_messages = received_doc_ids - sent_doc_ids
            
            if missing_messages:
                logger.error(f"缺少消息: {missing_messages}")
                return False
            
            if extra_messages:
                logger.error(f"多余消息: {extra_messages}")
                return False
            
            # 验证数据转换结果
            if self.transformer:
                transform_success_count = sum(
                    1 for msg in self.received_messages 
                    if msg['processed_data'] is not None
                )
                logger.info(f"数据转换成功数: {transform_success_count}/{received_count}")
                
                if transform_success_count != received_count:
                    logger.warning("部分消息数据转换失败")
            
            logger.info("测试结果验证通过")
            return True
            
        except Exception as e:
            logger.error(f"验证测试结果时出错: {str(e)}")
            return False
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.consumer:
                self.consumer.close()
                logger.info("消费者已关闭")
            
            if self.producer:
                self.producer.close()
                logger.info("生产者已关闭")
            
            if self.client:
                self.client.close()
                logger.info("客户端已关闭")
                
        except Exception as e:
            logger.error(f"清理资源时出错: {str(e)}")


async def main():
    """主函数"""
    logger.info("开始端到端集成测试")
    
    # 检查环境变量
    if not os.getenv('PULSAR_CLUSTER_URL'):
        logger.warning("未设置PULSAR_CLUSTER_URL环境变量，将使用默认配置")
    
    test = EndToEndTest()
    
    try:
        # 设置测试环境
        logger.info("\n=== 步骤1: 设置测试环境 ===")
        if not await test.setup():
            logger.error("设置测试环境失败")
            return False
        
        # 创建测试消息
        logger.info("\n=== 步骤2: 创建测试消息 ===")
        test_messages = test.create_test_messages()
        logger.info(f"创建了 {len(test_messages)} 条测试消息")
        
        # 发送消息
        logger.info("\n=== 步骤3: 发送测试消息 ===")
        if not await test.send_messages(test_messages):
            logger.error("发送测试消息失败")
            return False
        
        # 等待消息传播
        logger.info("\n=== 步骤4: 等待消息传播 ===")
        await asyncio.sleep(3)
        
        # 消费消息
        logger.info("\n=== 步骤5: 消费测试消息 ===")
        if not await test.consume_messages(len(test_messages), timeout_seconds=30):
            logger.error("消费测试消息失败")
            return False
        
        # 验证结果
        logger.info("\n=== 步骤6: 验证测试结果 ===")
        if not test.verify_results():
            logger.error("测试结果验证失败")
            return False
        
        logger.info("\n=== 端到端集成测试成功完成 ===")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中出现异常: {str(e)}")
        return False
        
    finally:
        await test.cleanup()


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    
    if success:
        logger.info("端到端集成测试通过")
        sys.exit(0)
    else:
        logger.error("端到端集成测试失败")
        sys.exit(1)