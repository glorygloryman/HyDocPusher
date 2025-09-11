"""
Exception handling module
Defines all custom exception classes used in HyDocPusher project
"""

from .custom_exceptions import (
    HyDocPusherException,
    ConfigurationException,
    MessageProcessException,
    DataTransformException,
    ArchiveClientException,
    ValidationException,
    RetryExhaustedException,
    ConnectionException
)

__all__ = [
    'HyDocPusherException',
    'ConfigurationException',
    'MessageProcessException',
    'DataTransformException',
    'ArchiveClientException',
    'ValidationException',
    'RetryExhaustedException',
    'ConnectionException'
]