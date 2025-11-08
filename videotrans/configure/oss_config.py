# -*- coding: utf-8 -*-
"""
OSS 配置管理器
负责加载、保存、验证和加密 OSS 配置
"""
import json
import os
from pathlib import Path
from typing import Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

from videotrans.configure import config


class OSSConfigManager:
    """OSS 配置管理器"""

    # 配置文件路径
    CONFIG_FILE = "oss_config.json"
    EXAMPLE_FILE = "oss_config.example.json"

    # 加密密钥（基于机器特征生成，简单实现）
    _SALT = b'pyvideotrans_oss_salt_v1'

    def __init__(self):
        """初始化配置管理器"""
        self.config_path = Path(config.ROOT_DIR) / self.CONFIG_FILE
        self.example_path = Path(config.ROOT_DIR) / self.EXAMPLE_FILE
        self._cipher = None
        self._init_cipher()

    def _init_cipher(self):
        """初始化加密器"""
        try:
            # 使用 PBKDF2HMAC 从固定密码派生密钥
            # 注意：生产环境应使用更安全的密钥管理方案
            password = b'pyvideotrans_oss_encryption_key'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self._SALT,
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            self._cipher = Fernet(key)
        except Exception as e:
            config.logger.warning(f"Failed to initialize cipher: {e}")
            self._cipher = None

    def encrypt_secret(self, secret: str) -> str:
        """
        加密密钥

        Args:
            secret: 明文密钥

        Returns:
            加密后的密钥，格式: encrypted:base64_string
        """
        if not secret or not self._cipher:
            return secret

        try:
            encrypted = self._cipher.encrypt(secret.encode('utf-8'))
            return f"encrypted:{encrypted.decode('utf-8')}"
        except Exception as e:
            config.logger.error(f"Failed to encrypt secret: {e}")
            return secret

    def decrypt_secret(self, encrypted: str) -> str:
        """
        解密密钥

        Args:
            encrypted: 加密的密钥

        Returns:
            明文密钥
        """
        if not encrypted or not self._cipher:
            return encrypted

        # 检查是否已加密
        if not encrypted.startswith("encrypted:"):
            return encrypted

        try:
            encrypted_data = encrypted[10:]  # 去掉 "encrypted:" 前缀
            decrypted = self._cipher.decrypt(encrypted_data.encode('utf-8'))
            return decrypted.decode('utf-8')
        except Exception as e:
            config.logger.error(f"Failed to decrypt secret: {e}")
            return encrypted

    def load_config(self) -> Dict:
        """
        加载 OSS 配置

        Returns:
            配置字典
        """
        # 如果配置文件不存在，返回默认配置
        if not self.config_path.exists():
            return self._get_default_config()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 解密 access_key_secret
            if 'access_key_secret' in config_data:
                config_data['access_key_secret'] = self.decrypt_secret(
                    config_data['access_key_secret']
                )

            config.logger.info("OSS config loaded successfully")
            return config_data

        except Exception as e:
            config.logger.error(f"Failed to load OSS config: {e}")
            return self._get_default_config()

    def save_config(self, config_data: Dict) -> bool:
        """
        保存 OSS 配置

        Args:
            config_data: 配置字典

        Returns:
            是否保存成功
        """
        try:
            # 复制配置以避免修改原始数据
            save_data = config_data.copy()

            # 加密 access_key_secret
            if 'access_key_secret' in save_data and save_data['access_key_secret']:
                # 如果已经加密，先解密再重新加密（确保使用当前密钥）
                secret = self.decrypt_secret(save_data['access_key_secret'])
                save_data['access_key_secret'] = self.encrypt_secret(secret)

            # 保存到文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            config.logger.info("OSS config saved successfully")
            return True

        except Exception as e:
            config.logger.error(f"Failed to save OSS config: {e}")
            return False

    def validate_config(self, config_data: Dict) -> tuple[bool, str]:
        """
        验证配置有效性

        Args:
            config_data: 配置字典

        Returns:
            (是否有效, 错误信息)
        """
        # 如果未启用，跳过验证
        if not config_data.get('enabled', False):
            return True, ""

        # 验证必需字段
        required_fields = {
            'provider': '提供商',
            'endpoint': 'Endpoint',
            'access_key_id': 'Access Key ID',
            'access_key_secret': 'Access Key Secret',
            'bucket_name': 'Bucket 名称'
        }

        for field, name in required_fields.items():
            if not config_data.get(field):
                return False, f"缺少必需字段: {name}"

        # 验证提供商
        valid_providers = ['aliyun', 'aws', 'minio']
        if config_data['provider'] not in valid_providers:
            return False, f"不支持的提供商: {config_data['provider']}"

        # 验证 endpoint 格式
        endpoint = config_data['endpoint']
        if not endpoint or '.' not in endpoint:
            return False, "Endpoint 格式无效"

        # 验证 bucket_name 格式
        bucket = config_data['bucket_name']
        if not bucket or len(bucket) < 3:
            return False, "Bucket 名称格式无效"

        return True, ""

    def test_connection(self, config_data: Dict) -> tuple[bool, str]:
        """
        测试 OSS 连接

        Args:
            config_data: 配置字典

        Returns:
            (是否成功, 消息)
        """
        # 先验证配置
        valid, msg = self.validate_config(config_data)
        if not valid:
            return False, f"配置验证失败: {msg}"

        provider = config_data['provider']

        try:
            if provider == 'aliyun':
                return self._test_aliyun_connection(config_data)
            elif provider == 'aws':
                return self._test_aws_connection(config_data)
            elif provider == 'minio':
                return self._test_minio_connection(config_data)
            else:
                return False, f"不支持的提供商: {provider}"
        except Exception as e:
            config.logger.error(f"Test connection failed: {e}")
            return False, f"❌ 连接测试失败: {str(e)}"

    def _test_aliyun_connection(self, config_data: Dict) -> tuple[bool, str]:
        """测试阿里云 OSS 连接"""
        try:
            import oss2

            # 创建 OSS 客户端
            auth = oss2.Auth(
                config_data['access_key_id'],
                self.decrypt_secret(config_data['access_key_secret'])
            )

            bucket = oss2.Bucket(
                auth,
                config_data['endpoint'],
                config_data['bucket_name']
            )

            # 测试连接：列出前1个对象
            try:
                result = bucket.list_objects(max_keys=1)
                return True, "[OK] 连接成功"
            except oss2.exceptions.NoSuchBucket:
                return False, f"[X] Bucket 不存在: {config_data['bucket_name']}"
            except oss2.exceptions.AccessDenied:
                return False, "[X] 访问被拒绝，请检查 Access Key 权限"
            except Exception as e:
                return False, f"[X] 连接失败: {str(e)}"

        except ImportError:
            return False, "[X] 缺少依赖: 请安装 oss2 (pip install oss2)"
        except Exception as e:
            return False, f"[X] 测试失败: {str(e)}"

    def _test_aws_connection(self, config_data: Dict) -> tuple[bool, str]:
        """测试 AWS S3 连接"""
        try:
            import boto3
            from botocore.exceptions import ClientError

            # 创建 S3 客户端
            s3_client = boto3.client(
                's3',
                aws_access_key_id=config_data['access_key_id'],
                aws_secret_access_key=self.decrypt_secret(config_data['access_key_secret']),
                region_name=config_data.get('region', 'us-east-1')
            )

            # 测试连接：列出前1个对象
            try:
                response = s3_client.list_objects_v2(
                    Bucket=config_data['bucket_name'],
                    MaxKeys=1
                )
                return True, "[OK] 连接成功"
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'NoSuchBucket':
                    return False, f"[X] Bucket 不存在: {config_data['bucket_name']}"
                elif error_code == 'AccessDenied':
                    return False, "[X] 访问被拒绝，请检查 Access Key 权限"
                else:
                    return False, f"[X] 连接失败: {error_code}"
            except Exception as e:
                return False, f"[X] 连接失败: {str(e)}"

        except ImportError:
            return False, "[X] 缺少依赖: 请安装 boto3 (pip install boto3)"
        except Exception as e:
            return False, f"[X] 测试失败: {str(e)}"

    def _test_minio_connection(self, config_data: Dict) -> tuple[bool, str]:
        """测试 MinIO 连接"""
        try:
            from minio import Minio
            from minio.error import S3Error

            # 解析 endpoint（可能包含端口）
            endpoint = config_data['endpoint']
            secure = not endpoint.startswith('http://') and not config_data.get('use_http', False)

            # 移除协议前缀
            if endpoint.startswith('http://') or endpoint.startswith('https://'):
                endpoint = endpoint.split('://', 1)[1]

            # 创建 MinIO 客户端
            minio_client = Minio(
                endpoint,
                access_key=config_data['access_key_id'],
                secret_key=self.decrypt_secret(config_data['access_key_secret']),
                secure=secure
            )

            # 测试连接：检查 bucket 是否存在
            try:
                exists = minio_client.bucket_exists(config_data['bucket_name'])
                if exists:
                    return True, "[OK] 连接成功"
                else:
                    return False, f"[X] Bucket 不存在: {config_data['bucket_name']}"
            except S3Error as e:
                return False, f"[X] 连接失败: {e.message}"
            except Exception as e:
                return False, f"[X] 连接失败: {str(e)}"

        except ImportError:
            return False, "[X] 缺少依赖: 请安装 minio (pip install minio)"
        except Exception as e:
            return False, f"[X] 测试失败: {str(e)}"

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "enabled": False,
            "provider": "aliyun",
            "endpoint": "",
            "access_key_id": "",
            "access_key_secret": "",
            "bucket_name": "",
            "region": "",
            "custom_domain": "",
            "path_prefix": "videos/",
            "public_access": True,
            "upload_on_complete": True,
            "upload_timeout": 300,
            "retry_count": 3,
            "multipart_threshold": 104857600
        }

    def get_config(self) -> Dict:
        """获取当前配置（快捷方法）"""
        return self.load_config()

    def is_enabled(self) -> bool:
        """检查 OSS 是否启用"""
        config_data = self.load_config()
        return config_data.get('enabled', False)


# 全局单例
_oss_config_manager = None


def get_oss_config_manager() -> OSSConfigManager:
    """获取 OSS 配置管理器单例"""
    global _oss_config_manager
    if _oss_config_manager is None:
        _oss_config_manager = OSSConfigManager()
    return _oss_config_manager
