"""
分类映射配置管理的TDD测试用例
"""

import pytest
import tempfile
import os
import yaml
from unittest.mock import patch, mock_open
from pathlib import Path

from hydocpusher.config.classification_config import (
    ClassificationConfig, 
    ClassificationRule, 
    get_classification_config, 
    reload_classification_config
)
from hydocpusher.exceptions.custom_exceptions import ConfigurationException


class TestClassificationRule:
    """分类规则测试"""
    
    def test_create_classification_rule(self):
        """测试创建分类规则"""
        rule = ClassificationRule(
            channel_id="2240",
            classfyname="新闻头条",
            classfy="XWTT"
        )
        assert rule.channel_id == "2240"
        assert rule.classfyname == "新闻头条"
        assert rule.classfy == "XWTT"
    
    def test_classification_rule_with_defaults(self):
        """测试带默认值的分类规则"""
        rule = ClassificationRule(
            channel_id="2241",
            classfyname="集团要闻",
            classfy="JTYW"
        )
        assert rule.channel_id == "2241"
        assert rule.classfyname == "集团要闻"
        assert rule.classfy == "JTYW"


class TestClassificationConfig:
    """分类配置测试"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "classification-rules.yaml")
        
        # 创建测试配置数据
        self.test_config_data = {
            'classification_rules': [
                {
                    'channel_id': '2240',
                    'classfyname': '新闻头条',
                    'classfy': 'XWTT'
                },
                {
                    'channel_id': '2241',
                    'classfyname': '集团要闻',
                    'classfy': 'JTYW'
                }
            ],
            'default': {
                'classfyname': '其他',
                'classfy': 'QT'
            }
        }
        
        # 写入测试配置文件
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.test_config_data, f, default_flow_style=False, allow_unicode=True)
    
    def teardown_method(self):
        """清理测试环境"""
        # 删除临时文件和目录
        if os.path.exists(self.config_file):
            os.unlink(self.config_file)
        os.rmdir(self.temp_dir)
    
    def test_load_config_success(self):
        """测试成功加载配置"""
        config = ClassificationConfig(self.config_file)
        
        assert len(config.rules) == 2
        assert '2240' in config.rules
        assert '2241' in config.rules
        
        rule_2240 = config.rules['2240']
        assert rule_2240.classfyname == '新闻头条'
        assert rule_2240.classfy == 'XWTT'
        
        assert config.default_rule.classfyname == '其他'
        assert config.default_rule.classfy == 'QT'
    
    def test_load_config_file_not_found(self):
        """测试配置文件不存在"""
        with pytest.raises(ConfigurationException) as exc_info:
            ClassificationConfig('/nonexistent/file.yaml')
        
        assert 'Classification rules file not found' in str(exc_info.value)
    
    def test_load_config_invalid_yaml(self):
        """测试无效的YAML格式"""
        # 创建无效的YAML文件
        with open(self.config_file, 'w') as f:
            f.write('invalid: yaml: content: [')
        
        with pytest.raises(ConfigurationException) as exc_info:
            ClassificationConfig(self.config_file)
        
        assert 'Failed to parse classification rules file' in str(exc_info.value)
    
    def test_load_config_missing_classification_rules(self):
        """测试缺少classification_rules字段"""
        # 创建缺少classification_rules的配置
        invalid_config = {
            'default': {
                'classfyname': '其他',
                'classfy': 'QT'
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(invalid_config, f)
        
        with pytest.raises(ConfigurationException) as exc_info:
            ClassificationConfig(self.config_file)
        
        assert 'Invalid classification rules file format' in str(exc_info.value)
    
    def test_load_config_missing_channel_id(self):
        """测试规则缺少channel_id"""
        # 创建缺少channel_id的规则
        invalid_config = {
            'classification_rules': [
                {
                    'classfyname': '新闻头条',
                    'classfy': 'XWTT'
                }
            ],
            'default': {
                'classfyname': '其他',
                'classfy': 'QT'
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(invalid_config, f)
        
        with pytest.raises(ConfigurationException) as exc_info:
            ClassificationConfig(self.config_file)
        
        assert "Missing 'channel_id' in classification rule" in str(exc_info.value)
    
    def test_get_classification_existing_channel(self):
        """测试获取存在的频道的分类信息"""
        config = ClassificationConfig(self.config_file)
        
        classfyname, classfy = config.get_classification('2240')
        assert classfyname == '新闻头条'
        assert classfy == 'XWTT'
    
    def test_get_classification_nonexistent_channel(self):
        """测试获取不存在的频道的分类信息"""
        config = ClassificationConfig(self.config_file)
        
        classfyname, classfy = config.get_classification('9999')
        assert classfyname == '其他'
        assert classfy == 'QT'
    
    def test_get_classification_rule_existing(self):
        """测试获取存在的频道的分类规则对象"""
        config = ClassificationConfig(self.config_file)
        
        rule = config.get_classification_rule('2240')
        assert isinstance(rule, ClassificationRule)
        assert rule.channel_id == '2240'
        assert rule.classfyname == '新闻头条'
        assert rule.classfy == 'XWTT'
    
    def test_get_classification_rule_default(self):
        """测试获取默认分类规则对象"""
        config = ClassificationConfig(self.config_file)
        
        rule = config.get_classification_rule('9999')
        assert isinstance(rule, ClassificationRule)
        assert rule.channel_id == 'default'
        assert rule.classfyname == '其他'
        assert rule.classfy == 'QT'
    
    def test_get_all_rules(self):
        """测试获取所有分类规则"""
        config = ClassificationConfig(self.config_file)
        
        rules = config.get_all_rules()
        assert len(rules) == 2
        
        # 检查所有规则都是ClassificationRule实例
        for rule in rules:
            assert isinstance(rule, ClassificationRule)
    
    def test_get_channel_ids(self):
        """测试获取所有频道ID"""
        config = ClassificationConfig(self.config_file)
        
        channel_ids = config.get_channel_ids()
        assert len(channel_ids) == 2
        assert '2240' in channel_ids
        assert '2241' in channel_ids
    
    def test_add_rule(self):
        """测试添加分类规则"""
        config = ClassificationConfig(self.config_file)
        
        config.add_rule('2242', '通知公告', 'TZGG')
        
        assert '2242' in config.rules
        rule = config.rules['2242']
        assert rule.classfyname == '通知公告'
        assert rule.classfy == 'TZGG'
    
    def test_remove_rule(self):
        """测试移除分类规则"""
        config = ClassificationConfig(self.config_file)
        
        result = config.remove_rule('2240')
        assert result is True
        assert '2240' not in config.rules
        
        # 测试移除不存在的规则
        result = config.remove_rule('9999')
        assert result is False
    
    def test_save_config(self):
        """测试保存配置"""
        config = ClassificationConfig(self.config_file)
        
        # 添加新规则
        config.add_rule('2242', '通知公告', 'TZGG')
        
        # 保存配置
        config.save_config()
        
        # 重新加载配置
        new_config = ClassificationConfig(self.config_file)
        
        assert '2242' in new_config.rules
        rule = new_config.rules['2242']
        assert rule.classfyname == '通知公告'
        assert rule.classfy == 'TZGG'
    
    def test_reload_config(self):
        """测试重新加载配置"""
        config = ClassificationConfig(self.config_file)
        
        # 修改配置文件
        new_config_data = {
            'classification_rules': [
                {
                    'channel_id': '2240',
                    'classfyname': '新闻头条',
                    'classfy': 'XWTT'
                },
                {
                    'channel_id': '2243',
                    'classfyname': '政策法规',
                    'classfy': 'ZCFG'
                }
            ],
            'default': {
                'classfyname': '其他',
                'classfy': 'QT'
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(new_config_data, f, default_flow_style=False, allow_unicode=True)
        
        # 重新加载配置
        config.reload()
        
        assert '2243' in config.rules
        assert '2241' not in config.rules  # 旧规则应该不存在
    
    def test_validate_config_success(self):
        """测试验证配置成功"""
        config = ClassificationConfig(self.config_file)
        # 应该不抛出异常
        config.validate_config()
    
    def test_validate_config_missing_default(self):
        """测试验证缺少默认配置"""
        config = ClassificationConfig(self.config_file)
        config.default_rule = None
        
        with pytest.raises(ConfigurationException) as exc_info:
            config.validate_config()
        
        assert 'Default classification rule is required' in str(exc_info.value)
    
    def test_validate_config_invalid_default(self):
        """测试验证无效的默认配置"""
        config = ClassificationConfig(self.config_file)
        config.default_rule.classfyname = ''
        
        with pytest.raises(ConfigurationException) as exc_info:
            config.validate_config()
        
        assert 'Default classification rule must have classfyname and classfy' in str(exc_info.value)
    
    def test_validate_config_invalid_rule(self):
        """测试验证无效的规则"""
        config = ClassificationConfig(self.config_file)
        config.rules['2240'].classfyname = ''
        
        with pytest.raises(ConfigurationException) as exc_info:
            config.validate_config()
        
        assert 'Classification rule for channel 2240 must have classfyname and classfy' in str(exc_info.value)
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        config = ClassificationConfig(self.config_file)
        
        stats = config.get_statistics()
        assert stats['total_rules'] == 2
        assert stats['unique_channels'] == 2
        assert stats['unique_classfy'] == 2  # XWTT, JTYW
        assert stats['unique_classfyname'] == 2  # 新闻头条, 集团要闻
    
    def test_file_reload_on_change(self):
        """测试文件变更时的自动重载"""
        config = ClassificationConfig(self.config_file)
        
        # 修改配置文件
        new_config_data = {
            'classification_rules': [
                {
                    'channel_id': '2240',
                    'classfyname': '新闻头条',
                    'classfy': 'XWTT'
                },
                {
                    'channel_id': '2244',
                    'classfyname': '党建工作',
                    'classfy': 'DJGZ'
                }
            ],
            'default': {
                'classfyname': '其他',
                'classfy': 'QT'
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(new_config_data, f, default_flow_style=False, allow_unicode=True)
        
        # 等待文件系统更新
        import time
        time.sleep(0.1)
        
        # 触发重载检查
        classfyname, classfy = config.get_classification('2244')
        assert classfyname == '党建工作'
        assert classfy == 'DJGZ'


class TestGlobalClassificationConfig:
    """全局分类配置测试"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "classification-rules.yaml")
        
        # 创建测试配置数据
        test_config_data = {
            'classification_rules': [
                {
                    'channel_id': '2240',
                    'classfyname': '新闻头条',
                    'classfy': 'XWTT'
                }
            ],
            'default': {
                'classfyname': '其他',
                'classfy': 'QT'
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_config_data, f, default_flow_style=False, allow_unicode=True)
        
        # 清除全局配置实例
        import hydocpusher.config.classification_config
        hydocpusher.config.classification_config._classification_config = None
    
    def teardown_method(self):
        """清理测试环境"""
        # 删除临时文件和目录
        if os.path.exists(self.config_file):
            os.unlink(self.config_file)
        os.rmdir(self.temp_dir)
        
        # 清除全局配置实例
        import hydocpusher.config.classification_config
        hydocpusher.config.classification_config._classification_config = None
    
    def test_get_classification_config_creates_instance(self):
        """测试get_classification_config创建实例"""
        config = get_classification_config(self.config_file)
        assert isinstance(config, ClassificationConfig)
        assert len(config.rules) == 1
    
    def test_get_classification_config_returns_cached_instance(self):
        """测试get_classification_config返回缓存的实例"""
        config1 = get_classification_config(self.config_file)
        config2 = get_classification_config(self.config_file)
        
        assert config1 is config2
    
    def test_reload_classification_config(self):
        """测试重新加载分类配置"""
        config1 = get_classification_config(self.config_file)
        
        # 修改配置文件
        new_config_data = {
            'classification_rules': [
                {
                    'channel_id': '2240',
                    'classfyname': '新闻头条',
                    'classfy': 'XWTT'
                },
                {
                    'channel_id': '2241',
                    'classfyname': '集团要闻',
                    'classfy': 'JTYW'
                }
            ],
            'default': {
                'classfyname': '其他',
                'classfy': 'QT'
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(new_config_data, f, default_flow_style=False, allow_unicode=True)
        
        config2 = reload_classification_config(self.config_file)
        
        assert config2 is not config1  # 应该是新实例
        assert len(config2.rules) == 2