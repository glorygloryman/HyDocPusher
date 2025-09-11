"""
数据模型模块
包含所有Pydantic数据模型定义
"""

from .message_models import (
    SourceMessageSchema,
    MessageData,
    DocumentData,
    ChannelDoc,
    AppendixInfo
)

from .archive_models import (
    ArchiveRequestSchema,
    ArchiveData,
    AttachmentData,
    ArchiveResponseSchema
)

__all__ = [
    # Source message models
    'SourceMessageSchema',
    'MessageData',
    'DocumentData',
    'ChannelDoc',
    'AppendixInfo',
    
    # Archive request models
    'ArchiveRequestSchema',
    'ArchiveData',
    'AttachmentData',
    'ArchiveResponseSchema'
]