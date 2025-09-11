"""
Pytest configuration and shared fixtures
"""

import pytest
import tempfile
import os
import yaml
from pathlib import Path


@pytest.fixture
def temp_directory():
    """Create temporary directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_classification_rules():
    """Sample classification rules data"""
    return {
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
            },
            {
                'channel_id': '2242',
                'classfyname': '通知公告',
                'classfy': 'TZGG'
            }
        ],
        'default': {
            'classfyname': '其他',
            'classfy': 'QT'
        }
    }


@pytest.fixture
def classification_rules_file(temp_directory, sample_classification_rules):
    """Create classification rules config file"""
    config_file = os.path.join(temp_directory, 'classification-rules.yaml')
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(sample_classification_rules, f, default_flow_style=False, allow_unicode=True)
    yield config_file


@pytest.fixture
def sample_env_vars():
    """Sample environment variables"""
    return {
        'ARCHIVE_API_URL': 'http://test.example.com/api',
        'ARCHIVE_APP_TOKEN': 'test-token-123',
        'SERVER_PORT': '8080',
        'PULSAR_CLUSTER_URL': 'pulsar://localhost:6650',
        'LOG_LEVEL': 'INFO'
    }


@pytest.fixture
def mock_env_vars(sample_env_vars):
    """Mock environment variables"""
    original_env = os.environ.copy()
    
    # Set test environment variables
    for key, value in sample_env_vars.items():
        os.environ[key] = value
    
    yield
    
    # Restore original environment variables
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_archive_config():
    """Sample archive system configuration"""
    return {
        'api_url': 'http://archive.example.com/api',
        'timeout': 30000,
        'retry_max_attempts': 3,
        'retry_delay': 60000,
        'app_id': 'NEWS',
        'app_token': 'test-token',
        'company_name': '云南省能源投资集团有限公司',
        'archive_type': '17',
        'domain': 'example.com',
        'retention_period': 30
    }


@pytest.fixture
def sample_pulsar_config():
    """Sample Pulsar configuration"""
    return {
        'cluster_url': 'pulsar://localhost:6650',
        'topic': 'persistent://public/default/content-publish',
        'subscription': 'hydocpusher-subscription',
        'dead_letter_topic': 'persistent://public/default/hydocpusher-dlq'
    }


@pytest.fixture
def invalid_yaml_file(temp_directory):
    """Create invalid YAML file"""
    invalid_file = os.path.join(temp_directory, 'invalid.yaml')
    with open(invalid_file, 'w') as f:
        f.write('invalid: yaml: [')
    yield invalid_file


@pytest.fixture
def missing_rules_file(temp_directory):
    """Create config file missing classification rules"""
    missing_rules_file = os.path.join(temp_directory, 'missing-rules.yaml')
    with open(missing_rules_file, 'w') as f:
        yaml.dump({'default': {'classfyname': '其他', 'classfy': 'QT'}}, f)
    yield missing_rules_file


@pytest.fixture
def empty_config_file(temp_directory):
    """Create empty config file"""
    empty_file = os.path.join(temp_directory, 'empty.yaml')
    with open(empty_file, 'w') as f:
        f.write('')
    yield empty_file