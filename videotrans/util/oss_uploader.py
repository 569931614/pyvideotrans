# -*- coding: utf-8 -*-
"""
OSS 上传器
负责将文件上传到阿里云 OSS
"""
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Dict

from videotrans.configure import config


class OSSUploader:
    """OSS 上传器"""

    def __init__(self, oss_config: Dict):
        """
        初始化上传器

        Args:
            oss_config: OSS 配置字典
        """
        self.config = oss_config
        self.client = None
        self.bucket = None
        self._init_client()

    def _init_client(self):
        """初始化 OSS 客户端"""
        provider = self.config['provider']

        if provider == 'aliyun':
            self._init_aliyun_client()
        elif provider == 'aws':
            self._init_aws_client()
        elif provider == 'minio':
            self._init_minio_client()
        else:
            raise ValueError(f"不支持的提供商: {provider}")

        config.logger.info(f"OSS client initialized successfully ({provider})")

    def _init_aliyun_client(self):
        """初始化阿里云 OSS 客户端"""
        try:
            import oss2
            from videotrans.configure.oss_config import get_oss_config_manager

            manager = get_oss_config_manager()

            # 创建认证对象
            auth = oss2.Auth(
                self.config['access_key_id'],
                manager.decrypt_secret(self.config['access_key_secret'])
            )

            # 创建 Bucket 对象
            self.bucket = oss2.Bucket(
                auth,
                self.config['endpoint'],
                self.config['bucket_name']
            )
            self.client = self.bucket

        except ImportError:
            raise ImportError("缺少 oss2 依赖，请运行: pip install oss2")
        except Exception as e:
            config.logger.error(f"Failed to initialize Aliyun OSS client: {e}")
            raise

    def _init_aws_client(self):
        """初始化 AWS S3 客户端"""
        try:
            import boto3
            from videotrans.configure.oss_config import get_oss_config_manager

            manager = get_oss_config_manager()

            # 创建 S3 客户端
            self.client = boto3.client(
                's3',
                aws_access_key_id=self.config['access_key_id'],
                aws_secret_access_key=manager.decrypt_secret(self.config['access_key_secret']),
                region_name=self.config.get('region', 'us-east-1')
            )
            self.bucket = None  # S3 uses bucket name directly in API calls

        except ImportError:
            raise ImportError("缺少 boto3 依赖，请运行: pip install boto3")
        except Exception as e:
            config.logger.error(f"Failed to initialize AWS S3 client: {e}")
            raise

    def _init_minio_client(self):
        """初始化 MinIO 客户端"""
        try:
            from minio import Minio
            from videotrans.configure.oss_config import get_oss_config_manager

            manager = get_oss_config_manager()

            # 解析 endpoint（可能包含端口）
            endpoint = self.config['endpoint']
            secure = not endpoint.startswith('http://') and not self.config.get('use_http', False)

            # 移除协议前缀
            if endpoint.startswith('http://') or endpoint.startswith('https://'):
                endpoint = endpoint.split('://', 1)[1]

            # 创建 MinIO 客户端
            self.client = Minio(
                endpoint,
                access_key=self.config['access_key_id'],
                secret_key=manager.decrypt_secret(self.config['access_key_secret']),
                secure=secure
            )
            self.bucket = None  # MinIO uses bucket name directly in API calls

        except ImportError:
            raise ImportError("缺少 minio 依赖，请运行: pip install minio")
        except Exception as e:
            config.logger.error(f"Failed to initialize MinIO client: {e}")
            raise

    def upload_file(
        self,
        local_path: str,
        remote_key: Optional[str] = None,
        callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict:
        """
        上传文件到 OSS

        Args:
            local_path: 本地文件路径
            remote_key: OSS 对象键 (可选，默认自动生成)
            callback: 进度回调函数 (consumed_bytes, total_bytes)

        Returns:
            {
                "success": bool,
                "url": str,           # 公网访问 URL
                "oss_key": str,       # OSS 对象键
                "size": int,          # 文件大小
                "error": str          # 错误信息 (如果失败)
            }
        """
        result = {
            "success": False,
            "url": "",
            "oss_key": "",
            "size": 0,
            "error": ""
        }

        try:
            # 验证文件存在
            if not os.path.exists(local_path):
                result["error"] = f"文件不存在: {local_path}"
                return result

            # 获取文件大小
            file_size = os.path.getsize(local_path)
            result["size"] = file_size

            # 生成 OSS 对象键
            if not remote_key:
                remote_key = self._generate_object_key(local_path)

            result["oss_key"] = remote_key

            config.logger.info(f"Uploading {local_path} to OSS as {remote_key}")

            # 选择上传方式
            threshold = self.config.get('multipart_threshold', 104857600)  # 100MB
            provider = self.config['provider']

            if file_size > threshold:
                # 分块上传（大文件）
                if provider == 'aliyun':
                    success = self._aliyun_multipart_upload(local_path, remote_key, callback)
                elif provider == 'aws':
                    success = self._aws_multipart_upload(local_path, remote_key, callback)
                elif provider == 'minio':
                    success = self._minio_upload(local_path, remote_key, callback)
                else:
                    raise ValueError(f"不支持的提供商: {provider}")
            else:
                # 简单上传（小文件）
                if provider == 'aliyun':
                    success = self._aliyun_simple_upload(local_path, remote_key, callback)
                elif provider == 'aws':
                    success = self._aws_simple_upload(local_path, remote_key, callback)
                elif provider == 'minio':
                    success = self._minio_upload(local_path, remote_key, callback)
                else:
                    raise ValueError(f"不支持的提供商: {provider}")

            if success:
                # 生成公网 URL
                url = self.get_public_url(remote_key)
                result["success"] = True
                result["url"] = url
                config.logger.info(f"Upload successful: {url}")
            else:
                result["error"] = "上传失败"

        except Exception as e:
            result["error"] = str(e)
            config.logger.error(f"Upload failed: {e}")

        return result

    def _aliyun_simple_upload(
        self,
        local_path: str,
        remote_key: str,
        callback: Optional[Callable] = None
    ) -> bool:
        """
        阿里云简单上传（一次性上传整个文件）

        Args:
            local_path: 本地文件路径
            remote_key: OSS 对象键
            callback: 进度回调

        Returns:
            是否成功
        """
        try:
            import oss2

            # 创建进度回调（如果提供）
            if callback:
                def percentage_callback(consumed, total):
                    callback(consumed, total)

                # 使用进度回调上传
                self.bucket.put_object_from_file(
                    remote_key,
                    local_path,
                    progress_callback=percentage_callback
                )
            else:
                # 直接上传
                self.bucket.put_object_from_file(remote_key, local_path)

            return True

        except Exception as e:
            config.logger.error(f"Aliyun simple upload failed: {e}")
            return False

    def _aliyun_multipart_upload(
        self,
        local_path: str,
        remote_key: str,
        callback: Optional[Callable] = None
    ) -> bool:
        """
        阿里云分块上传（适用于大文件）

        Args:
            local_path: 本地文件路径
            remote_key: OSS 对象键
            callback: 进度回调

        Returns:
            是否成功
        """
        try:
            import oss2
            from oss2.models import PartInfo

            # 初始化分块上传
            upload_id = self.bucket.init_multipart_upload(remote_key).upload_id

            # 分块大小 (10MB)
            part_size = 10 * 1024 * 1024
            file_size = os.path.getsize(local_path)

            parts = []
            uploaded_size = 0

            with open(local_path, 'rb') as f:
                part_number = 1

                while True:
                    data = f.read(part_size)
                    if not data:
                        break

                    # 上传分块
                    result = self.bucket.upload_part(
                        remote_key,
                        upload_id,
                        part_number,
                        data
                    )

                    parts.append(PartInfo(part_number, result.etag))
                    uploaded_size += len(data)

                    # 调用进度回调
                    if callback:
                        callback(uploaded_size, file_size)

                    part_number += 1

            # 完成分块上传
            self.bucket.complete_multipart_upload(remote_key, upload_id, parts)
            return True

        except Exception as e:
            config.logger.error(f"Aliyun multipart upload failed: {e}")
            # 尝试取消分块上传
            try:
                if upload_id:
                    self.bucket.abort_multipart_upload(remote_key, upload_id)
            except:
                pass
            return False

    def _aws_simple_upload(
        self,
        local_path: str,
        remote_key: str,
        callback: Optional[Callable] = None
    ) -> bool:
        """
        AWS S3 简单上传

        Args:
            local_path: 本地文件路径
            remote_key: S3 对象键
            callback: 进度回调

        Returns:
            是否成功
        """
        try:
            # S3 简单上传
            extra_args = {}

            # S3 callback needs a different format
            if callback:
                file_size = os.path.getsize(local_path)

                def s3_callback(bytes_amount):
                    callback(bytes_amount, file_size)

                self.client.upload_file(
                    local_path,
                    self.config['bucket_name'],
                    remote_key,
                    ExtraArgs=extra_args,
                    Callback=s3_callback
                )
            else:
                self.client.upload_file(
                    local_path,
                    self.config['bucket_name'],
                    remote_key,
                    ExtraArgs=extra_args
                )

            return True

        except Exception as e:
            config.logger.error(f"AWS S3 simple upload failed: {e}")
            return False

    def _aws_multipart_upload(
        self,
        local_path: str,
        remote_key: str,
        callback: Optional[Callable] = None
    ) -> bool:
        """
        AWS S3 分块上传（boto3 会自动处理）

        Args:
            local_path: 本地文件路径
            remote_key: S3 对象键
            callback: 进度回调

        Returns:
            是否成功
        """
        try:
            import boto3
            from boto3.s3.transfer import TransferConfig

            # 配置分块上传
            config_transfer = TransferConfig(
                multipart_threshold=10 * 1024 * 1024,  # 10MB
                max_concurrency=4,
                multipart_chunksize=10 * 1024 * 1024
            )

            # 上传文件（boto3 会自动处理分块）
            if callback:
                file_size = os.path.getsize(local_path)
                uploaded_size = [0]  # Use list to allow modification in nested function

                def s3_callback(bytes_amount):
                    uploaded_size[0] += bytes_amount
                    callback(uploaded_size[0], file_size)

                self.client.upload_file(
                    local_path,
                    self.config['bucket_name'],
                    remote_key,
                    Config=config_transfer,
                    Callback=s3_callback
                )
            else:
                self.client.upload_file(
                    local_path,
                    self.config['bucket_name'],
                    remote_key,
                    Config=config_transfer
                )

            return True

        except Exception as e:
            config.logger.error(f"AWS S3 multipart upload failed: {e}")
            return False

    def _minio_upload(
        self,
        local_path: str,
        remote_key: str,
        callback: Optional[Callable] = None
    ) -> bool:
        """
        MinIO 上传（MinIO 自动处理分块）

        Args:
            local_path: 本地文件路径
            remote_key: 对象键
            callback: 进度回调

        Returns:
            是否成功
        """
        try:
            file_size = os.path.getsize(local_path)

            # MinIO 上传
            if callback:
                # MinIO 的 put_object 不直接支持进度回调
                # 我们需要手动读取文件并追踪进度
                with open(local_path, 'rb') as file_data:
                    self.client.put_object(
                        self.config['bucket_name'],
                        remote_key,
                        file_data,
                        file_size
                    )
                    # 上传完成后调用回调
                    callback(file_size, file_size)
            else:
                self.client.fput_object(
                    self.config['bucket_name'],
                    remote_key,
                    local_path
                )

            return True

        except Exception as e:
            config.logger.error(f"MinIO upload failed: {e}")
            return False

    def upload_file_with_retry(
        self,
        local_path: str,
        remote_key: Optional[str] = None,
        callback: Optional[Callable] = None
    ) -> Dict:
        """
        带重试的上传

        Args:
            local_path: 本地文件路径
            remote_key: OSS 对象键
            callback: 进度回调

        Returns:
            上传结果字典
        """
        retry_count = self.config.get('retry_count', 3)
        last_error = ""

        for attempt in range(retry_count):
            if attempt > 0:
                config.logger.info(f"Retrying upload ({attempt + 1}/{retry_count})")
                time.sleep(5)  # 重试前等待

            result = self.upload_file(local_path, remote_key, callback)

            if result["success"]:
                return result

            last_error = result["error"]

        # 所有重试都失败
        return {
            "success": False,
            "url": "",
            "oss_key": remote_key or "",
            "size": 0,
            "error": f"上传失败（重试 {retry_count} 次）: {last_error}"
        }

    def _generate_object_key(self, local_path: str) -> str:
        """
        生成 OSS 对象键

        格式: {path_prefix}/{date}/{uuid}_{filename}
        例如: videos/2025-11-02/abc123_output.mp4

        Args:
            local_path: 本地文件路径

        Returns:
            OSS 对象键
        """
        # 获取文件名
        filename = os.path.basename(local_path)

        # 生成唯一 ID
        unique_id = str(uuid.uuid4())[:8]

        # 当前日期
        date_str = datetime.now().strftime("%Y-%m-%d")

        # 路径前缀
        prefix = self.config.get('path_prefix', 'videos/')
        if prefix and not prefix.endswith('/'):
            prefix += '/'

        # 组合对象键
        object_key = f"{prefix}{date_str}/{unique_id}_{filename}"

        return object_key

    def get_public_url(self, object_key: str) -> str:
        """
        获取公网访问 URL

        Args:
            object_key: 对象键

        Returns:
            公网 URL
        """
        provider = self.config['provider']

        # 如果配置了自定义域名，使用自定义域名
        custom_domain = self.config.get('custom_domain', '')
        if custom_domain:
            custom_domain = custom_domain.rstrip('/')
            return f"{custom_domain}/{object_key}"

        # 根据提供商生成 URL
        if provider == 'aliyun':
            return self._get_aliyun_url(object_key)
        elif provider == 'aws':
            return self._get_aws_url(object_key)
        elif provider == 'minio':
            return self._get_minio_url(object_key)
        else:
            # 默认返回简单拼接
            return f"https://{self.config['endpoint']}/{object_key}"

    def _get_aliyun_url(self, object_key: str) -> str:
        """生成阿里云 OSS URL"""
        bucket_name = self.config['bucket_name']
        endpoint = self.config['endpoint']

        # 处理 endpoint
        if endpoint.startswith('http://') or endpoint.startswith('https://'):
            base_url = endpoint
        else:
            base_url = f"https://{endpoint}"

        # OSS 公网访问格式: https://{bucket}.{endpoint}/{object_key}
        if bucket_name in endpoint:
            return f"{base_url}/{object_key}"
        else:
            protocol = 'https://' if not endpoint.startswith('http') else ''
            if '://' in endpoint:
                endpoint = endpoint.split('://', 1)[1]
            return f"{protocol}{bucket_name}.{endpoint}/{object_key}"

    def _get_aws_url(self, object_key: str) -> str:
        """生成 AWS S3 URL"""
        bucket_name = self.config['bucket_name']
        region = self.config.get('region', 'us-east-1')

        # S3 URL format: https://{bucket}.s3.{region}.amazonaws.com/{key}
        # or for us-east-1: https://{bucket}.s3.amazonaws.com/{key}
        if region == 'us-east-1':
            return f"https://{bucket_name}.s3.amazonaws.com/{object_key}"
        else:
            return f"https://{bucket_name}.s3.{region}.amazonaws.com/{object_key}"

    def _get_minio_url(self, object_key: str) -> str:
        """生成 MinIO URL"""
        bucket_name = self.config['bucket_name']
        endpoint = self.config['endpoint']

        # 判断是否使用 HTTP
        secure = not endpoint.startswith('http://') and not self.config.get('use_http', False)
        protocol = 'https' if secure else 'http'

        # 移除协议前缀（如果有）
        if endpoint.startswith('http://') or endpoint.startswith('https://'):
            endpoint = endpoint.split('://', 1)[1]

        # MinIO URL format: http(s)://{endpoint}/{bucket}/{key}
        return f"{protocol}://{endpoint}/{bucket_name}/{object_key}"

    def delete_file(self, object_key: str) -> bool:
        """
        删除对象存储文件

        Args:
            object_key: 对象键

        Returns:
            是否成功
        """
        try:
            provider = self.config['provider']

            if provider == 'aliyun':
                self.bucket.delete_object(object_key)
            elif provider == 'aws':
                self.client.delete_object(
                    Bucket=self.config['bucket_name'],
                    Key=object_key
                )
            elif provider == 'minio':
                self.client.remove_object(
                    self.config['bucket_name'],
                    object_key
                )
            else:
                return False

            config.logger.info(f"Deleted object: {object_key}")
            return True

        except Exception as e:
            config.logger.error(f"Failed to delete object: {e}")
            return False
