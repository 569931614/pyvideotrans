# OSS 对象存储配置指南

## 概述

pyvideotrans 支持将处理后的视频自动上传到对象存储服务 (OSS)，包括：
- 阿里云 OSS
- AWS S3
- MinIO (或任何 S3 兼容服务)

上传的视频将获得公网访问 URL，并可自动写入 HearSight 向量库用于 AI 问答。

## 安装依赖

### 必需依赖

已包含在 `requirements.txt` 中：
```bash
pip install psycopg2-binary
```

### OSS 可选依赖

```bash
# 安装所有 OSS 提供商支持
pip install -r requirements_oss.txt

# 或仅安装需要的提供商
pip install oss2  # 阿里云 OSS
pip install boto3  # AWS S3
pip install minio  # MinIO
pip install cryptography  # 配置加密（推荐）
```

## 配置文件

### 位置

- 示例配置: `oss_config.example.json`
- 实际配置: `oss_config.json` (自动创建，不提交到 git)

### 配置字段说明

```json
{
  "enabled": false,           // 是否启用 OSS 上传
  "provider": "aliyun",       // 提供商: aliyun | aws | minio
  "endpoint": "",             // OSS endpoint
  "access_key_id": "",        // Access Key ID
  "access_key_secret": "",    // Access Key Secret (将被加密存储)
  "bucket_name": "",          // Bucket 名称
  "region": "",               // 区域 (AWS S3 需要)
  "custom_domain": "",        // 自定义域名 (可选)
  "path_prefix": "videos/",   // 上传路径前缀
  "public_access": true,      // 是否公网可访问
  "upload_on_complete": true, // 视频处理完成后自动上传
  "upload_timeout": 300,      // 上传超时时间(秒)
  "retry_count": 3,           // 失败重试次数
  "multipart_threshold": 104857600  // 分块上传阈值(字节, 100MB)
}
```

## 配置示例

### 阿里云 OSS

```json
{
  "enabled": true,
  "provider": "aliyun",
  "endpoint": "oss-cn-beijing.aliyuncs.com",
  "access_key_id": "LTAI***************",
  "access_key_secret": "your_secret_key",
  "bucket_name": "my-video-bucket",
  "region": "cn-beijing",
  "path_prefix": "videos/",
  "public_access": true,
  "upload_on_complete": true
}
```

### AWS S3

```json
{
  "enabled": true,
  "provider": "aws",
  "endpoint": "s3.us-east-1.amazonaws.com",
  "access_key_id": "AKIA***************",
  "access_key_secret": "your_secret_key",
  "bucket_name": "my-video-bucket",
  "region": "us-east-1",
  "path_prefix": "videos/",
  "public_access": true,
  "upload_on_complete": true
}
```

### MinIO / 自建 S3

```json
{
  "enabled": true,
  "provider": "minio",
  "endpoint": "minio.example.com:9000",
  "access_key_id": "minioadmin",
  "access_key_secret": "minioadmin",
  "bucket_name": "videos",
  "path_prefix": "pyvideotrans/",
  "public_access": false,
  "upload_on_complete": true
}
```

## GUI 配置

在 pyvideotrans 主界面：

1. 点击菜单 **设置** → **OSS 配置**
2. 选择提供商 (阿里云 OSS / AWS S3 / MinIO)
3. 填写连接信息
4. 点击 **测试连接** 验证配置
5. 勾选 **启用 OSS 上传**
6. 勾选 **处理完成后自动上传** (可选)
7. 点击 **保存**

## 使用流程

### 自动上传

1. 配置 OSS 并启用
2. 勾选 "处理完成后自动上传"
3. 正常处理视频
4. 处理完成后自动上传到 OSS
5. GUI 显示上传进度和结果
6. 向量库使用 OSS URL

### 手动上传

1. 右键点击已处理的视频
2. 选择 "上传到 OSS"
3. 等待上传完成

## 安全建议

### 凭证安全

- ✅ `access_key_secret` 自动加密存储
- ✅ `oss_config.json` 已添加到 `.gitignore`
- ✅ 建议使用 RAM 子账号限制权限
- ✅ 定期轮换 Access Key

### 权限设置

**阿里云 OSS 最小权限**:
```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "oss:PutObject",
        "oss:GetObject"
      ],
      "Resource": "acs:oss:*:*:my-video-bucket/videos/*"
    }
  ]
}
```

**AWS S3 最小权限**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::my-video-bucket/videos/*"
    }
  ]
}
```

## 故障排查

### 连接失败

**错误**: "OSS 连接失败"

**排查步骤**:
1. 检查 endpoint 格式是否正确
2. 检查 Access Key ID 和 Secret
3. 检查网络连接
4. 检查 Bucket 是否存在
5. 检查权限设置

### 上传失败

**错误**: "上传失败: 403 Forbidden"

**原因**: 权限不足

**解决**: 检查 RAM/IAM 权限配置

---

**错误**: "上传超时"

**原因**: 网络速度慢或文件过大

**解决**:
1. 增加 `upload_timeout` 值
2. 检查网络连接
3. 使用更快的网络

### 文件损坏

**错误**: "上传的视频无法播放"

**排查**:
1. 检查本地文件是否正常
2. 重新上传
3. 检查 OSS 存储类型设置

## 高级功能

### CDN 加速

在 `custom_domain` 字段配置 CDN 域名：

```json
{
  "custom_domain": "https://cdn.example.com"
}
```

生成的 URL 将使用 CDN 域名而非 OSS endpoint。

### 批量上传历史视频

```bash
cd pyvideotrans
python -m videotrans.util.batch_upload_oss --dir /path/to/videos
```

## 参考文档

- [阿里云 OSS Python SDK](https://help.aliyun.com/document_detail/32026.html)
- [AWS S3 Python SDK (boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [MinIO Python SDK](https://min.io/docs/minio/linux/developers/python/minio-py.html)
