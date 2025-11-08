# 跨服务器部署指南

## 架构概述

当pyvideotrans和HearSight部署在不同服务器时，通过云服务实现数据共享：

```
服务器A (pyvideotrans)              云服务                服务器B (HearSight)
       │                               │                          │
       ├──────────────────────────────►│                          │
       │     1. 视频处理完成            │                          │
       │                               │                          │
       ├──────────────────────────────►│  阿里云OSS               │
       │     2. 上传视频                │  (视频文件)              │
       │                               │                          │
       ├──────────────────────────────►│  火山向量数据库          │
       │     3. 存储向量+文本            │  (语义搜索)              │
       │                               │                          │
       ├──────────────────────────────►│  PostgreSQL              │
       │     4. 存储Metadata            │  (元数据+全文)           │
       │                               │     ▲                    │
       │                               │     │                    │
       │                               │     └────────────────────┤
       │                               │     5. 查询/检索         │
```

## 方案1：PostgreSQL作为中心化存储（推荐）

### 优点
- ✅ 完全云端化，无需共享文件系统
- ✅ 支持复杂查询和事务
- ✅ 易于备份和扩展
- ✅ 您已经有PostgreSQL数据库

### 配置步骤

#### 1. pyvideotrans配置 (hearsight_config.json)

```json
{
  "vector": {
    "type": "postgresql",
    "database": {
      "host": "117.72.164.82",
      "port": 5433,
      "user": "admin",
      "password": "Admin@123",
      "database": "hearsight"
    }
  }
}
```

#### 2. HearSight配置 (.env)

```bash
# 使用PostgreSQL作为向量后端
HEARSIGHT_VECTOR_BACKEND=postgresql

# PostgreSQL配置
POSTGRES_HOST=117.72.164.82
POSTGRES_PORT=5433
POSTGRES_USER=admin
POSTGRES_PASSWORD=Admin@123
POSTGRES_DB=hearsight
```

#### 3. 数据库表结构

HearSight需要以下表（自动创建）：

```sql
-- 视频摘要表
CREATE TABLE IF NOT EXISTS video_summaries (
    id SERIAL PRIMARY KEY,
    transcript_id VARCHAR(32) UNIQUE NOT NULL,
    video_path TEXT NOT NULL,
    title TEXT,
    topic TEXT,
    summary TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 段落表
CREATE TABLE IF NOT EXISTS video_paragraphs (
    id SERIAL PRIMARY KEY,
    transcript_id VARCHAR(32) NOT NULL,
    paragraph_index INTEGER NOT NULL,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    text TEXT NOT NULL,
    summary TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (transcript_id) REFERENCES video_summaries(transcript_id)
);

-- 全文搜索索引
CREATE INDEX IF NOT EXISTS idx_video_summaries_search
ON video_summaries USING gin(to_tsvector('english', title || ' ' || summary));
```

---

## 方案2：火山向量数据库 + PostgreSQL混合

### 架构
- **火山向量**: 语义搜索（embedding相似度）
- **PostgreSQL**: Metadata存储 + 全文搜索（关键词）

### 优点
- ✅ 最佳搜索性能（语义+关键词双重检索）
- ✅ 完全云端化
- ✅ 您当前的配置

### 配置步骤

#### pyvideotrans配置

```json
{
  "vector": {
    "type": "volcengine",
    "volcengine": {
      "api_key": "2cad3d85-a6a5-433e-9ac5-41598e1aae83",
      "base_url": "https://ark.cn-beijing.volces.com/api/v3",
      "collection_name": "video_summaries",
      "embedding_model": "ep-20251029203615-d2xlt"
    },
    "database": {
      "host": "117.72.164.82",
      "port": 5433,
      "user": "admin",
      "password": "Admin@123",
      "database": "hearsight"
    }
  }
}
```

#### HearSight配置

```bash
# 使用火山向量数据库
HEARSIGHT_VECTOR_BACKEND=volcengine

# 火山配置
VOLCENGINE_API_KEY=2cad3d85-a6a5-433e-9ac5-41598e1aae83
VOLCENGINE_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
VOLCENGINE_COLLECTION_NAME=video_summaries
VOLCENGINE_EMBEDDING_MODEL=ep-20251029203615-d2xlt

# PostgreSQL配置（存储完整metadata）
POSTGRES_HOST=117.72.164.82
POSTGRES_PORT=5433
POSTGRES_USER=admin
POSTGRES_PASSWORD=Admin@123
POSTGRES_DB=hearsight
```

---

## 方案3：MinIO对象存储（文件共享方案）

如果您不想使用PostgreSQL存储metadata，可以用MinIO替代本地文件系统：

### 架构
```
pyvideotrans ──┐
               ├──► MinIO (metadata JSON文件)
HearSight   ───┘
```

### 配置示例

#### 部署MinIO

```bash
# Docker运行MinIO
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=admin" \
  -e "MINIO_ROOT_PASSWORD=Admin@123" \
  -v /data/minio:/data \
  minio/minio server /data --console-address ":9001"
```

#### pyvideotrans配置

```python
# 修改 volcengine_vector.py，将本地JSON保存改为MinIO
from minio import Minio

minio_client = Minio(
    "your-minio-server:9000",
    access_key="admin",
    secret_key="Admin@123",
    secure=False
)

# 上传metadata
minio_client.put_object(
    "hearsight-metadata",
    f"{video_id}.json",
    json.dumps(data),
    content_type="application/json"
)
```

---

## 推荐部署方案对比

| 方案 | 复杂度 | 性能 | 成本 | 推荐场景 |
|------|--------|------|------|----------|
| **方案1: PostgreSQL单一存储** | ⭐ 低 | ⭐⭐ 中 | ⭐ 低 | 小规模，已有PostgreSQL |
| **方案2: 火山+PostgreSQL混合** | ⭐⭐ 中 | ⭐⭐⭐ 高 | ⭐⭐ 中 | 生产环境，需要最佳搜索 |
| **方案3: MinIO文件共享** | ⭐⭐⭐ 高 | ⭐⭐ 中 | ⭐⭐ 中 | 需要保留JSON文件结构 |

---

## 实施建议

### 当前情况
您已经配置了：
- ✅ 火山向量数据库
- ✅ PostgreSQL数据库
- ✅ 阿里云OSS

### 建议方案：**方案2（火山+PostgreSQL混合）**

原因：
1. 您已有所有必要的基础设施
2. 性能最优（语义搜索+全文搜索）
3. 无需额外部署服务

### 需要做的修改

#### 1. 修改pyvideotrans的向量存储实现

让`VolcengineVectorClient`同时写入PostgreSQL：

```python
# videotrans/hearsight/volcengine_vector.py
def store_summary(self, video_path, summary, paragraphs, metadata, **kwargs):
    # 1. 存储到火山向量数据库（用于语义搜索）
    self._store_to_volcengine(...)

    # 2. 同时存储到PostgreSQL（用于metadata和全文搜索）
    self._store_to_postgresql(video_path, summary, paragraphs, metadata)
```

#### 2. HearSight查询时结合两个数据源

```python
# 先从火山向量搜索获取相关文档ID
vector_results = volcengine_client.search(query)

# 再从PostgreSQL获取完整metadata
for result in vector_results:
    transcript_id = result['transcript_id']
    metadata = pg_client.get_metadata(transcript_id)
    result.update(metadata)
```

---

## 迁移步骤

### 如果选择方案2（推荐）

1. **验证PostgreSQL连接**
   ```bash
   cd HearSight
   python test_db_connection.py
   ```

2. **创建数据库表**
   ```bash
   python auto_setup_database.py
   ```

3. **修改pyvideotrans代码**（我可以帮您完成）
   - 在`volcengine_vector.py`添加PostgreSQL写入
   - 确保同时更新两个数据源

4. **修改HearSight查询代码**
   - 结合火山向量和PostgreSQL结果
   - 优先使用火山向量语义搜索，补充PostgreSQL metadata

5. **测试新视频处理**
   - 在pyvideotrans处理一个新视频
   - 验证HearSight能否正确检索

---

## 故障排查

### 问题：HearSight搜索不到pyvideotrans处理的视频

**检查项：**
1. 两边是否使用相同的向量数据库配置？
2. PostgreSQL连接是否正常？
3. transcript_id是否一致？
4. metadata是否正确存储？

**调试命令：**
```bash
# 检查PostgreSQL中的数据
psql -h 117.72.164.82 -p 5433 -U admin -d hearsight \
  -c "SELECT transcript_id, title FROM video_summaries;"

# 检查火山向量数据库
cd pyvideotrans
python -c "
from videotrans.hearsight.volcengine_vector import VolcengineVectorClient
client = VolcengineVectorClient(...)
results = client.search('test', n_results=5)
print(results)
"
```

---

## 后续优化

### 1. 添加缓存层
- Redis缓存热门查询结果
- 减少数据库查询压力

### 2. 异步同步
- 使用消息队列（如RabbitMQ）
- pyvideotrans发送消息，HearSight异步处理

### 3. 监控和日志
- 监控向量搜索性能
- 记录同步失败的视频

---

需要我帮您实现具体的代码修改吗？
