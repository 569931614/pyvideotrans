# OSS 功能测试指南

本指南将帮助您测试新实现的 OSS（对象存储服务）上传功能。

## 前提条件

1. **安装依赖**
   ```bash
   cd pyvideotrans
   pip install -r requirements.txt
   ```

2. **准备 OSS 账户**（至少需要以下之一）：
   - 阿里云 OSS
   - AWS S3
   - MinIO（可以本地部署）

3. **获取凭证**：
   - Access Key ID
   - Access Key Secret
   - Endpoint
   - Bucket 名称

## 测试步骤

### 第一步：配置 OSS

运行配置测试脚本：

```bash
cd pyvideotrans
python test_oss.py
```

然后选择 **选项 4：打开配置对话框**

在配置对话框中：
1. ✅ 勾选 "启用 OSS 上传功能"
2. 选择提供商（阿里云 OSS / AWS S3 / MinIO）
3. 填写连接信息：
   - **Endpoint**: 例如 `oss-cn-beijing.aliyuncs.com`
   - **Bucket 名称**: 例如 `my-video-bucket`
   - **Access Key ID**: 您的访问密钥 ID
   - **Access Key Secret**: 您的访问密钥（将被加密存储）
   - **Region**: 区域代码（AWS 必填）
4. 点击 **"测试连接"** 验证配置
5. 如果测试成功，点击 **"保存配置"**

### 第二步：测试配置管理器

继续在 `test_oss.py` 中选择：

- **选项 1**: 测试配置管理器
  - 验证配置加载
  - 验证配置验证逻辑
  - 验证密钥加密/解密

- **选项 2**: 测试上传器初始化
  - 验证上传器能否正确初始化
  - 验证对象键生成
  - 验证 URL 生成

- **选项 3**: 测试 OSS 连接
  - 实际连接到配置的 OSS
  - 验证凭证是否有效

### 第三步：测试文件上传

运行上传测试脚本：

```bash
python test_oss_upload.py
```

测试选项：

1. **选项 1**: 上传 1MB 测试文件（快速测试）
2. **选项 2**: 上传 10MB 测试文件
3. **选项 3**: 上传 100MB 测试文件（测试分块上传）
4. **选项 4**: 上传指定文件

也可以直接指定文件：
```bash
python test_oss_upload.py /path/to/your/video.mp4
```

### 第四步：验证上传结果

上传成功后：
1. 查看控制台输出的 **URL**
2. 在浏览器中访问该 URL（如果配置了公网访问）
3. 或者登录 OSS 控制台查看文件

## 测试不同的提供商

### 阿里云 OSS
```
提供商: 阿里云 OSS
Endpoint: oss-cn-beijing.aliyuncs.com
Bucket: your-bucket-name
Region: cn-beijing (可选)
```

### AWS S3
```
提供商: AWS S3
Endpoint: 留空（使用默认）
Bucket: your-bucket-name
Region: us-east-1 (必填)
```

### MinIO
```
提供商: MinIO / 自定义 S3
Endpoint: minio.example.com:9000
Bucket: your-bucket-name
✅ 使用 HTTP (如果没有 HTTPS)
```

## 测试功能清单

### 基础功能
- [ ] 配置对话框正常打开
- [ ] 提供商切换正常工作
- [ ] 配置保存成功
- [ ] 配置加载正常
- [ ] 密钥加密存储（不以明文显示）

### 连接测试
- [ ] 阿里云 OSS 连接测试通过
- [ ] AWS S3 连接测试通过（如果有账号）
- [ ] MinIO 连接测试通过（如果有服务）
- [ ] 错误凭证能正确提示

### 文件上传
- [ ] 小文件上传成功（< 100MB）
- [ ] 大文件分块上传成功（> 100MB）
- [ ] 上传进度正确显示
- [ ] 上传失败自动重试
- [ ] 返回正确的公网 URL

### 多提供商
- [ ] 可以切换不同提供商
- [ ] 每个提供商的 UI 正确适配
- [ ] 不同提供商的 URL 格式正确

## 常见问题

### 1. 连接测试失败
**可能原因**：
- 凭证错误
- Endpoint 错误
- Bucket 不存在
- 网络问题

**解决方法**：
- 检查 Access Key ID 和 Secret
- 确认 Endpoint 格式正确
- 确认 Bucket 已创建
- 检查防火墙设置

### 2. 上传失败
**可能原因**：
- 权限不足
- 网络超时
- Bucket 空间不足

**解决方法**：
- 确认账号有上传权限
- 增加超时时间
- 检查存储空间

### 3. 依赖安装失败
```bash
# 如果安装 oss2 失败
pip install oss2 -i https://pypi.tuna.tsinghua.edu.cn/simple

# 如果安装 boto3 失败
pip install boto3 -i https://pypi.tuna.tsinghua.edu.cn/simple

# 如果安装 minio 失败
pip install minio -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 测试报告模板

完成测试后，可以填写以下报告：

```
OSS 功能测试报告
================

测试环境：
- 操作系统: Windows/Linux/macOS
- Python 版本:
- 提供商: 阿里云 OSS / AWS S3 / MinIO

测试结果：
1. 配置管理: ✅ 通过 / ❌ 失败
2. 连接测试: ✅ 通过 / ❌ 失败
3. 文件上传: ✅ 通过 / ❌ 失败
4. 进度显示: ✅ 通过 / ❌ 失败
5. 重试机制: ✅ 通过 / ❌ 失败

问题和建议：
-

```

## 下一步

测试通过后，OSS 功能将被集成到视频处理流程中，届时：
1. 视频处理完成后自动上传到 OSS
2. 上传进度在主窗口显示
3. OSS URL 自动存储到数据库和向量库

---

如有问题，请查看日志文件或联系开发团队。
