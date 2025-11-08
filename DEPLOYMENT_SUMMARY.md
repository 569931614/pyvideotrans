# 跨服务器部署完成总结

## ✅ 已完成的工作

### 1. 代码修改

#### pyvideotrans修改：

1. **`videotrans/task/trans_create.py`** (907-936行)
   - ✅ 添加`title`字段到metadata
   - ✅ 配置HearSight共享存储路径
   - ✅ 传递`local_storage_path`参数

2. **`videotrans/hearsight/volcengine_vector.py`**
   - ✅ 添加`db_config`参数到`__init__`（18-52行）
   - ✅ 添加`_pg_conn`属性（PostgreSQL连接）
   - ✅ 实现`_get_pg_connection()`方法（581-601行）
   - ✅ 实现`_store_to_postgresql()`方法（603-687行）
   - ✅ 在`store_summary()`中调用PostgreSQL存储（269-273行）

3. **`videotrans/hearsight/vector_store.py`** (411-428行)
   - ✅ 获取数据库配置并传递给VolcengineVectorClient
   - ✅ 添加PostgreSQL配置日志输出

### 2. 部署架构

```
服务器A (pyvideotrans)                      服务器B (HearSight)
        │                                           │
        ├──► 火山向量数据库 ◄──────────────────────┤
        │    (语义搜索)                             │
        │                                           │
        ├──► PostgreSQL      ◄──────────────────────┤
        │    (Metadata存储)                         │
        │                                           │
        └──► 阿里云OSS       ◄──────────────────────┘
             (视频文件)
```

### 3. 数据流

**pyvideotrans处理视频后：**
1. 上传视频到阿里云OSS
2. 生成摘要和向量embedding
3. 存储到火山向量数据库
4. **同时存储到PostgreSQL**（完整metadata + 段落信息）

**HearSight查询时：**
1. 使用火山向量进行语义搜索
2. 从PostgreSQL获取完整metadata
3. 返回结果给用户

---

## 📋 配置要求

### pyvideotrans配置文件 (hearsight_config.json)

当前配置已正确：

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

### HearSight配置文件 (.env)

当前配置已正确：

```bash
# 向量数据库后端
HEARSIGHT_VECTOR_BACKEND=volcengine

# 火山配置
VOLCENGINE_API_KEY=2cad3d85-a6a5-433e-9ac5-41598e1aae83
VOLCENGINE_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
VOLCENGINE_COLLECTION_NAME=video_summaries
VOLCENGINE_EMBEDDING_MODEL=ep-20251029203615-d2xlt

# PostgreSQL配置
POSTGRES_HOST=117.72.164.82
POSTGRES_PORT=5433
POSTGRES_USER=admin
POSTGRES_PASSWORD=Admin@123
POSTGRES_DB=hearsight
```

---

## 🧪 测试步骤

### 1. 验证PostgreSQL连接

```bash
cd HearSight
python test_db_connection.py
```

### 2. 创建数据库表

```bash
cd HearSight
python auto_setup_database.py
```

### 3. 处理一个测试视频

在pyvideotrans中处理任何一个视频，检查日志中是否出现：

```
[volcengine] PostgreSQL连接成功
[volcengine] PostgreSQL存储成功: transcript_id=xxxxx
```

### 4. 在HearSight中搜索

打开 http://localhost:10000，搜索视频相关关键词

---

## 🔧 故障排查

### 问题1：PostgreSQL连接失败

**检查：**
```bash
# 测试PostgreSQL连接
psql -h 117.72.164.82 -p 5433 -U admin -d hearsight
```

**解决：**
- 检查防火墙规则
- 确认PostgreSQL允许远程连接
- 验证用户名密码

### 问题2：表不存在

**错误：** `relation "video_summaries" does not exist`

**解决：**
```bash
cd HearSight
python auto_setup_database.py
```

### 问题3：HearSight搜索不到数据

**检查数据是否存储：**
```sql
psql -h 117.72.164.82 -p 5433 -U admin -d hearsight \
  -c "SELECT transcript_id, title FROM video_summaries LIMIT 5;"
```

**如果为空：**
- 重新处理一个视频
- 检查pyvideotrans日志
- 确认PostgreSQL写入成功

---

## 📈 性能优化建议

### 1. 数据库索引

```sql
-- 在title和summary上创建全文搜索索引
CREATE INDEX IF NOT EXISTS idx_video_summaries_search
ON video_summaries USING gin(
  to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary, ''))
);

-- 在transcript_id上创建索引
CREATE INDEX IF NOT EXISTS idx_paragraphs_transcript
ON video_paragraphs(transcript_id);
```

### 2. 连接池

修改pyvideotrans使用连接池：

```python
from psycopg2 import pool

# 在应用启动时创建连接池
pg_pool = pool.SimpleConnectionPool(1, 20, **db_config)
```

### 3. 异步存储

将PostgreSQL存储改为异步：

```python
import threading

def async_store():
    threading.Thread(
        target=self._store_to_postgresql,
        args=(video_path, summary, paragraphs, metadata),
        daemon=True
    ).start()
```

---

## 🚀 部署到生产环境

### 服务器A部署pyvideotrans

```bash
# 1. 克隆代码
git clone <repo>
cd pyvideotrans

# 2. 安装依赖
pip install -r requirements.txt
pip install psycopg2-binary  # PostgreSQL驱动

# 3. 配置hearsight_config.json
# 确保database配置正确

# 4. 启动服务
python api.py
```

### 服务器B部署HearSight

```bash
# 1. 克隆代码
git clone <repo>
cd HearSight

# 2. 配置.env文件
# 确保所有配置正确

# 3. 创建数据库表
python auto_setup_database.py

# 4. Docker部署
docker compose up -d

# 或手动部署
pip install -r requirements.txt
python main.py &
cd frontend && npm install && npm run build
```

---

## ✅ 验证清单

- [ ] PostgreSQL可以从两台服务器访问
- [ ] 火山向量数据库API密钥正确
- [ ] 阿里云OSS配置正确
- [ ] pyvideotrans能成功连接PostgreSQL
- [ ] HearSight能成功连接PostgreSQL
- [ ] 数据库表已创建
- [ ] 处理测试视频后能在HearSight中搜索到

---

## 📞 支持

如遇到问题，请检查：

1. **日志文件**
   - pyvideotrans: `logs/YYYYMMDD.log`
   - HearSight: Docker logs或控制台输出

2. **数据库状态**
   ```sql
   SELECT * FROM video_summaries ORDER BY created_at DESC LIMIT 1;
   ```

3. **网络连接**
   ```bash
   # 从服务器A测试到PostgreSQL
   telnet 117.72.164.82 5433

   # 从服务器B测试到PostgreSQL
   telnet 117.72.164.82 5433
   ```

---

## 🎯 下一步

1. 在pyvideotrans处理一个新视频
2. 验证PostgreSQL中有数据
3. 在HearSight中搜索验证
4. 如成功，即可部署到生产环境

所有代码修改已完成，可以开始测试了！
