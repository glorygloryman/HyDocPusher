"""
分类映射配置管理模块
负责从YAML文件加载频道到档案分类的映射规则
"""

import yaml
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from ..exceptions.custom_exceptions import ConfigurationException


@dataclass
class ClassificationRule:
    """分类规则数据类"""
    channel_id: str
    classfyname: str
    classfy: str


class ClassificationConfig:
    """分类映射配置管理类"""
    
    def __init__(self, rules_file: str = None):
        """
        初始化分类配置
        
        Args:
            rules_file: 分类规则文件路径
        """
        self.rules_file = rules_file or "config/classification-rules.yaml"
        self.rules: Dict[str, ClassificationRule] = {}
        self.default_rule: ClassificationRule = None
        self._last_modified: float = 0
        
        # 加载配置
        self._load_config()
    
    def _load_config(self) -> None:
        """加载分类配置文件"""
        try:
            if not os.path.exists(self.rules_file):
                raise ConfigurationException(f"Classification rules file not found: {self.rules_file}")
            
            with open(self.rules_file, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
            
            if not config_data or 'classification_rules' not in config_data:
                raise ConfigurationException("Invalid classification rules file format")
            
            # 解析分类规则
            self.rules.clear()
            for rule_data in config_data['classification_rules']:
                if 'channel_id' not in rule_data:
                    raise ConfigurationException("Missing 'channel_id' in classification rule")
                
                rule = ClassificationRule(
                    channel_id=str(rule_data['channel_id']),
                    classfyname=rule_data.get('classfyname', '其他'),
                    classfy=rule_data.get('classfy', 'QT')
                )
                self.rules[rule.channel_id] = rule
            
            # 设置默认规则
            default_config = config_data.get('default', {})
            self.default_rule = ClassificationRule(
                channel_id='default',
                classfyname=default_config.get('classfyname', '其他'),
                classfy=default_config.get('classfy', 'QT')
            )
            
            # 记录文件修改时间
            self._last_modified = os.path.getmtime(self.rules_file)
            
        except yaml.YAMLError as e:
            raise ConfigurationException(f"Failed to parse classification rules file: {str(e)}", cause=e)
        except Exception as e:
            if isinstance(e, ConfigurationException):
                raise
            raise ConfigurationException(f"Failed to load classification configuration: {str(e)}", cause=e)
    
    def get_classification(self, channel_id: str) -> Tuple[str, str]:
        """
        根据频道ID获取分类信息
        
        Args:
            channel_id: 频道ID
            
        Returns:
            Tuple[classfyname, classfy]: 分类名称和分类代码
        """
        # 检查是否需要重新加载配置
        self._check_reload()
        
        # 查找匹配的规则
        rule = self.rules.get(str(channel_id))
        if rule is None:
            rule = self.default_rule
        
        return rule.classfyname, rule.classfy
    
    def get_classification_rule(self, channel_id: str) -> ClassificationRule:
        """
        根据频道ID获取分类规则对象
        
        Args:
            channel_id: 频道ID
            
        Returns:
            ClassificationRule: 分类规则对象
        """
        # 检查是否需要重新加载配置
        self._check_reload()
        
        return self.rules.get(str(channel_id), self.default_rule)
    
    def get_all_rules(self) -> List[ClassificationRule]:
        """
        获取所有分类规则
        
        Returns:
            List[ClassificationRule]: 分类规则列表
        """
        # 检查是否需要重新加载配置
        self._check_reload()
        
        return list(self.rules.values())
    
    def get_channel_ids(self) -> List[str]:
        """
        获取所有配置的频道ID
        
        Returns:
            List[str]: 频道ID列表
        """
        # 检查是否需要重新加载配置
        self._check_reload()
        
        return list(self.rules.keys())
    
    def add_rule(self, channel_id: str, classfyname: str, classfy: str) -> None:
        """
        添加新的分类规则
        
        Args:
            channel_id: 频道ID
            classfyname: 分类名称
            classfy: 分类代码
        """
        rule = ClassificationRule(
            channel_id=str(channel_id),
            classfyname=classfyname,
            classfy=classfy
        )
        self.rules[str(channel_id)] = rule
    
    def remove_rule(self, channel_id: str) -> bool:
        """
        移除分类规则
        
        Args:
            channel_id: 频道ID
            
        Returns:
            bool: 是否成功移除
        """
        channel_id = str(channel_id)
        if channel_id in self.rules:
            del self.rules[channel_id]
            return True
        return False
    
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            # 构建配置数据
            config_data = {
                'classification_rules': [
                    {
                        'channel_id': rule.channel_id,
                        'classfyname': rule.classfyname,
                        'classfy': rule.classfy
                    }
                    for rule in self.rules.values()
                ],
                'default': {
                    'classfyname': self.default_rule.classfyname,
                    'classfy': self.default_rule.classfy
                }
            }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self.rules_file), exist_ok=True)
            
            # 写入文件
            with open(self.rules_file, 'w', encoding='utf-8') as file:
                yaml.dump(config_data, file, default_flow_style=False, allow_unicode=True)
            
            # 更新修改时间
            self._last_modified = os.path.getmtime(self.rules_file)
            
        except Exception as e:
            raise ConfigurationException(f"Failed to save classification configuration: {str(e)}", cause=e)
    
    def _check_reload(self) -> None:
        """检查是否需要重新加载配置"""
        try:
            if os.path.exists(self.rules_file):
                current_modified = os.path.getmtime(self.rules_file)
                if current_modified > self._last_modified:
                    self._load_config()
        except Exception:
            # 如果检查失败，继续使用现有配置
            pass
    
    def reload(self) -> None:
        """强制重新加载配置"""
        self._load_config()
    
    def validate_config(self) -> None:
        """验证配置的有效性"""
        if not self.default_rule:
            raise ConfigurationException("Default classification rule is required")
        
        if not self.default_rule.classfyname or not self.default_rule.classfy:
            raise ConfigurationException("Default classification rule must have classfyname and classfy")
        
        # 验证所有规则
        for channel_id, rule in self.rules.items():
            if not rule.classfyname or not rule.classfy:
                raise ConfigurationException(f"Classification rule for channel {channel_id} must have classfyname and classfy")
    
    def get_statistics(self) -> Dict[str, int]:
        """
        获取配置统计信息
        
        Returns:
            Dict[str, int]: 统计信息
        """
        return {
            'total_rules': len(self.rules),
            'unique_channels': len(set(self.rules.keys())),
            'unique_classfy': len(set(rule.classfy for rule in self.rules.values())),
            'unique_classfyname': len(set(rule.classfyname for rule in self.rules.values()))
        }


# 全局分类配置实例
_classification_config: Optional[ClassificationConfig] = None


def get_classification_config(rules_file: str = None) -> ClassificationConfig:
    """
    获取全局分类配置实例
    
    Args:
        rules_file: 分类规则文件路径
        
    Returns:
        ClassificationConfig: 分类配置实例
    """
    global _classification_config
    if _classification_config is None:
        _classification_config = ClassificationConfig(rules_file)
    return _classification_config


def reload_classification_config(rules_file: str = None) -> ClassificationConfig:
    """
    重新加载分类配置
    
    Args:
        rules_file: 分类规则文件路径
        
    Returns:
        ClassificationConfig: 重新加载的分类配置实例
    """
    global _classification_config
    _classification_config = ClassificationConfig(rules_file)
    return _classification_config