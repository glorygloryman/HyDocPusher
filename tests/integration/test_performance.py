#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试套件

测试系统在高负载情况下的性能表现，包括：
- 高并发消息处理
- 内存使用情况
- 响应时间统计
- 吞吐量测试
- 资源泄漏检测
"""

import asyncio
import json
import logging
import psutil
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hydocpusher.client.archive_client import ArchiveClient
from hydocpusher.config.settings import AppConfig
from hydocpusher.consumer.pulsar_consumer import PulsarConsumer
from hydocpusher.exceptions.custom_exceptions import (
    ArchiveClientException,
    ConfigurationException,
    MessageProcessException,
)
from hydocpusher.models.message_models import SourceMessageSchema
from hydocpusher.transformer.data_transformer import DataTransformer
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceTest:
    """性能测试类"""
    
    def __init__(self):
        self.config = AppConfig()
        self.logger = logging.getLogger("performance_test")
        logging.basicConfig(level=logging.INFO)
        self.transformer = DataTransformer()
        self.performance_metrics = {
            'message_count': 0,
            'success_count': 0,
            'error_count': 0,
            'total_time': 0,
            'avg_response_time': 0,
            'max_response_time': 0,
            'min_response_time': float('inf'),
            'memory_usage': [],
            'cpu_usage': [],
            'throughput': 0
        }
        
    def setup(self):
        """设置测试环境"""
        self.logger.info("=== 性能测试环境设置 ===")
        
        # 记录初始系统资源
        process = psutil.Process()
        self.initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        self.initial_cpu = process.cpu_percent()
        
        self.logger.info(f"初始内存使用: {self.initial_memory:.2f} MB")
        self.logger.info(f"初始CPU使用: {self.initial_cpu:.2f}%")
        
    def teardown(self):
        """清理测试环境"""
        self.logger.info("=== 性能测试环境清理 ===")
        
        # 记录最终系统资源
        process = psutil.Process()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()
        
        memory_diff = final_memory - self.initial_memory
        cpu_diff = final_cpu - self.initial_cpu
        
        self.logger.info(f"最终内存使用: {final_memory:.2f} MB (变化: {memory_diff:+.2f} MB)")
        self.logger.info(f"最终CPU使用: {final_cpu:.2f}% (变化: {cpu_diff:+.2f}%)")
        
        # 检查内存泄漏
        if memory_diff > 100:  # 超过100MB认为可能有内存泄漏
            self.logger.warning(f"⚠️ 可能存在内存泄漏，内存增长: {memory_diff:.2f} MB")
        
    def create_test_message(self, doc_id: str) -> Dict:
        """创建测试消息"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return {
            "MSG": "操作成功",
            "DATA": {
                "SITENAME": "性能测试站点",
                "CRTIME": timestamp,
                "CHANNELID": "2240",
                "VIEWID": "11",
                "VIEWNAME": "PerformanceTest",
                "SITEID": "33",
                "DOCID": doc_id,
                "OPERTYPE": "1",
                "CHANNELNAV": "2240",
                "DATA": {
                    "DOCTITLE": f"性能测试文档 {doc_id}",
                    "DOCCONTENT": "这是一个性能测试文档，用于验证系统在高负载下的表现。" * 10,
                    "DOCAUTHOR": "性能测试",
                    "DOCRELTIME": timestamp,
                    "DOCPUBURL": f"https://test.com/perf/{doc_id}.html",
                    "ATTACHPIC": "1",
                    "THUMBFILES": "perf_test.jpg",
                    "MEDIATYPE": "1",
                    "SITENAME": "性能测试站点",
                    "CHANNELID": "2240",
                    "SITEID": "33",
                    "PUBSTATUS": "1"
                },
                "CHNLDOC": {
                    "DOCSTATUS": "10",
                    "PUBSTATUS": "1",
                    "DOCID": doc_id,
                    "CHNLID": "2240",
                    "SITEID": "33"
                },
                "APPENDIX": [
                    {
                        "APPFILE": "perf_test.jpg",
                        "APPFLAG": "20"
                    }
                ]
            },
            "ISSUCCESS": "true"
        }
    
    async def process_single_message(self, message: Dict) -> Dict:
        """处理单个消息并记录性能指标"""
        start_time = time.time()
        
        try:
            # 记录处理前的资源使用
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024
            cpu_before = process.cpu_percent()
            
            # 数据转换
            transform_start = time.time()
            processed_data = self.transformer.transform(message)
            transform_end = time.time()
            
            # 模拟档案客户端发送（使用Mock避免实际网络请求）
            with patch('hydocpusher.client.archive_client.ArchiveClient') as mock_client:
                mock_instance = AsyncMock()
                mock_instance.send_data_async.return_value = True
                mock_client.return_value.__aenter__.return_value = mock_instance
                
                async with ArchiveClient(
                    base_url="http://test.com",
                    timeout=30,
                    max_retries=3
                ) as client:
                    success = await client.send_data_async(processed_data)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # 记录处理后的资源使用
            memory_after = process.memory_info().rss / 1024 / 1024
            cpu_after = process.cpu_percent()
            
            # 更新性能指标
            self.performance_metrics['message_count'] += 1
            if success:
                self.performance_metrics['success_count'] += 1
            else:
                self.performance_metrics['error_count'] += 1
            
            self.performance_metrics['total_time'] += response_time
            self.performance_metrics['max_response_time'] = max(
                self.performance_metrics['max_response_time'], response_time
            )
            self.performance_metrics['min_response_time'] = min(
                self.performance_metrics['min_response_time'], response_time
            )
            
            self.performance_metrics['memory_usage'].append(memory_after)
            self.performance_metrics['cpu_usage'].append(cpu_after)
            
            return {
                'success': success,
                'response_time': response_time,
                'transform_time': transform_end - transform_start,
                'memory_usage': memory_after - memory_before,
                'cpu_usage': cpu_after - cpu_before,
                'doc_id': message['DATA']['DOCID']
            }
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            self.performance_metrics['message_count'] += 1
            self.performance_metrics['error_count'] += 1
            self.performance_metrics['total_time'] += response_time
            
            self.logger.error(f"处理消息时发生异常: {str(e)}")
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")
            
            return {
                'success': False,
                'response_time': response_time,
                'error': str(e),
                'doc_id': message['DATA']['DOCID']
            }
    
    async def test_concurrent_processing(self, message_count: int = 100, concurrency: int = 10):
        """测试并发消息处理性能"""
        self.logger.info(f"=== 开始并发处理测试 ===")
        self.logger.info(f"消息数量: {message_count}")
        self.logger.info(f"并发数: {concurrency}")
        
        # 创建测试消息
        messages = [
            self.create_test_message(f"perf_test_{i:06d}")
            for i in range(message_count)
        ]
        
        start_time = time.time()
        
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(concurrency)
        
        async def process_with_semaphore(message):
            async with semaphore:
                return await self.process_single_message(message)
        
        # 并发处理所有消息
        tasks = [process_with_semaphore(msg) for msg in messages]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 计算性能指标
        self.performance_metrics['avg_response_time'] = (
            self.performance_metrics['total_time'] / self.performance_metrics['message_count']
            if self.performance_metrics['message_count'] > 0 else 0
        )
        self.performance_metrics['throughput'] = message_count / total_time
        
        # 统计结果
        successful_results = [r for r in results if isinstance(r, dict) and r.get('success', False)]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get('success', False)]
        exception_results = [r for r in results if isinstance(r, Exception)]
        
        self.logger.info(f"=== 并发处理测试结果 ===")
        self.logger.info(f"总消息数: {message_count}")
        self.logger.info(f"成功处理: {len(successful_results)}")
        self.logger.info(f"处理失败: {len(failed_results)}")
        self.logger.info(f"异常数量: {len(exception_results)}")
        self.logger.info(f"总耗时: {total_time:.3f}秒")
        self.logger.info(f"平均响应时间: {self.performance_metrics['avg_response_time']:.3f}秒")
        self.logger.info(f"最大响应时间: {self.performance_metrics['max_response_time']:.3f}秒")
        self.logger.info(f"最小响应时间: {self.performance_metrics['min_response_time']:.3f}秒")
        self.logger.info(f"吞吐量: {self.performance_metrics['throughput']:.2f} 消息/秒")
        
        # 内存和CPU统计
        if self.performance_metrics['memory_usage']:
            avg_memory = sum(self.performance_metrics['memory_usage']) / len(self.performance_metrics['memory_usage'])
            max_memory = max(self.performance_metrics['memory_usage'])
            self.logger.info(f"平均内存使用: {avg_memory:.2f} MB")
            self.logger.info(f"峰值内存使用: {max_memory:.2f} MB")
        
        if self.performance_metrics['cpu_usage']:
            avg_cpu = sum(self.performance_metrics['cpu_usage']) / len(self.performance_metrics['cpu_usage'])
            max_cpu = max(self.performance_metrics['cpu_usage'])
            self.logger.info(f"平均CPU使用: {avg_cpu:.2f}%")
            self.logger.info(f"峰值CPU使用: {max_cpu:.2f}%")
        
        return {
            'total_messages': message_count,
            'successful': len(successful_results),
            'failed': len(failed_results),
            'exceptions': len(exception_results),
            'total_time': total_time,
            'throughput': self.performance_metrics['throughput'],
            'avg_response_time': self.performance_metrics['avg_response_time'],
            'max_response_time': self.performance_metrics['max_response_time'],
            'min_response_time': self.performance_metrics['min_response_time']
        }
    
    async def test_memory_leak(self, iterations: int = 50):
        """测试内存泄漏"""
        self.logger.info(f"=== 开始内存泄漏测试 ===")
        self.logger.info(f"迭代次数: {iterations}")
        
        memory_snapshots = []
        
        for i in range(iterations):
            # 处理一批消息
            messages = [
                self.create_test_message(f"leak_test_{i}_{j}")
                for j in range(10)
            ]
            
            for message in messages:
                await self.process_single_message(message)
            
            # 记录内存使用
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            memory_snapshots.append(memory_mb)
            
            if i % 10 == 0:
                self.logger.info(f"迭代 {i}/{iterations}, 内存使用: {memory_mb:.2f} MB")
        
        # 分析内存趋势
        initial_memory = memory_snapshots[0]
        final_memory = memory_snapshots[-1]
        memory_growth = final_memory - initial_memory
        
        # 计算内存增长趋势
        memory_trend = []
        for i in range(1, len(memory_snapshots)):
            trend = memory_snapshots[i] - memory_snapshots[i-1]
            memory_trend.append(trend)
        
        avg_growth = sum(memory_trend) / len(memory_trend) if memory_trend else 0
        
        self.logger.info(f"=== 内存泄漏测试结果 ===")
        self.logger.info(f"初始内存: {initial_memory:.2f} MB")
        self.logger.info(f"最终内存: {final_memory:.2f} MB")
        self.logger.info(f"总内存增长: {memory_growth:.2f} MB")
        self.logger.info(f"平均增长趋势: {avg_growth:.4f} MB/迭代")
        
        # 判断是否存在内存泄漏
        leak_threshold = 1.0  # MB per iteration
        if avg_growth > leak_threshold:
            self.logger.warning(f"⚠️ 检测到可能的内存泄漏，平均增长: {avg_growth:.4f} MB/迭代")
        else:
            self.logger.info(f"✅ 未检测到明显的内存泄漏")
        
        return {
            'initial_memory': initial_memory,
            'final_memory': final_memory,
            'memory_growth': memory_growth,
            'avg_growth_per_iteration': avg_growth,
            'potential_leak': avg_growth > leak_threshold
        }
    
    def generate_performance_report(self) -> str:
        """生成性能测试报告"""
        report = []
        report.append("=== 性能测试报告 ===")
        report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("## 消息处理统计")
        report.append(f"总消息数: {self.performance_metrics['message_count']}")
        report.append(f"成功处理: {self.performance_metrics['success_count']}")
        report.append(f"处理失败: {self.performance_metrics['error_count']}")
        report.append(f"成功率: {(self.performance_metrics['success_count'] / self.performance_metrics['message_count'] * 100):.2f}%" if self.performance_metrics['message_count'] > 0 else "成功率: 0%")
        report.append("")
        
        report.append("## 性能指标")
        report.append(f"平均响应时间: {self.performance_metrics['avg_response_time']:.3f}秒")
        report.append(f"最大响应时间: {self.performance_metrics['max_response_time']:.3f}秒")
        report.append(f"最小响应时间: {self.performance_metrics['min_response_time']:.3f}秒")
        report.append(f"吞吐量: {self.performance_metrics['throughput']:.2f} 消息/秒")
        report.append("")
        
        if self.performance_metrics['memory_usage']:
            avg_memory = sum(self.performance_metrics['memory_usage']) / len(self.performance_metrics['memory_usage'])
            max_memory = max(self.performance_metrics['memory_usage'])
            report.append("## 资源使用")
            report.append(f"平均内存使用: {avg_memory:.2f} MB")
            report.append(f"峰值内存使用: {max_memory:.2f} MB")
        
        if self.performance_metrics['cpu_usage']:
            avg_cpu = sum(self.performance_metrics['cpu_usage']) / len(self.performance_metrics['cpu_usage'])
            max_cpu = max(self.performance_metrics['cpu_usage'])
            report.append(f"平均CPU使用: {avg_cpu:.2f}%")
            report.append(f"峰值CPU使用: {max_cpu:.2f}%")
        
        return "\n".join(report)


async def main():
    """主函数 - 运行性能测试"""
    perf_test = PerformanceTest()
    
    try:
        perf_test.setup()
        
        # 测试1: 并发处理测试
        logger.info("开始并发处理测试...")
        concurrent_result = await perf_test.test_concurrent_processing(
            message_count=100,
            concurrency=10
        )
        
        # 测试2: 内存泄漏测试
        logger.info("开始内存泄漏测试...")
        leak_result = await perf_test.test_memory_leak(iterations=30)
        
        # 生成报告
        report = perf_test.generate_performance_report()
        logger.info("\n" + report)
        
        # 保存报告到文件
        report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"性能测试报告已保存到: {report_file}")
        
    except Exception as e:
        logger.error(f"性能测试过程中发生异常: {str(e)}")
        logger.error(f"异常堆栈: {traceback.format_exc()}")
    finally:
        perf_test.teardown()


if __name__ == "__main__":
    asyncio.run(main())