# HearSight 智能摘要 + 向量库 - 快速开始

## 📦 安装

### 1. 安装依赖

```bash
cd BDvideoTrans
pip install chromadb
```

或者：
```bash
pip install -r requirements_hearsight.txt
```

### 2. 验证安装

```bash
python -c "import chromadb; print('ChromaDB installed:', chromadb.__version__)"
```

---

## 🚀 快速使用

### 方式 1: 自动集成（推荐）

**在视频翻译时自动生成摘要**

1. **配置 HearSight**
   - 点击工具栏 **"🎯 智能摘要"** 旁边的 **"⚙️"**
   - 填写 API Key 和其他配置
   - 点击 **"保存"**

2. **启用智能摘要**
   - 在主界面底部勾选 **"☑ 智能摘要"**

3. **正常翻译视频**
   - 选择视频、配置参数
   - 点击 **"开始执行"**
   - 等待完成

4. **查看结果**
   - 翻译完成后，摘要会自动生成并存储到向量库
   - 查看日志确认："✅ Successfully stored HearSight summary in vector database"

---

### 方式 2: 手动使用

**单独使用 HearSight 功能**

#### 2.1 生成摘要并存储

```python
from videotrans.hearsight.segment_merger import merge_srt_to_paragraphs
from videotrans.hearsight.summarizer import generate_summary, generate_paragraph_summaries
from videotrans.hearsight.vector_store import get_vector_store

# 1. 读取并合并段落
paragraphs = merge_srt_to_paragraphs("path/to/subtitle.srt")

# 2. 生成整体摘要
summary = generate_summary(
    paragraphs=paragraphs,
    api_key="your-api-key",
    model="gpt-3.5-turbo"
)

# 3. 生成段落摘要
paragraphs_with_summaries = generate_paragraph_summaries(
    paragraphs=paragraphs,
    api_key="your-api-key",
    model="gpt-3.5-turbo"
)

# 4. 存储到向量库
vector_store = get_vector_store()
vector_store.store_summary(
    video_path="path/to/video.mp4",
    summary=summary,
    paragraphs=paragraphs_with_summaries
)
```

#### 2.2 语义搜索

```python
from videotrans.hearsight.vector_store import get_vector_store

vector_store = get_vector_store()

# 搜索相关内容
results = vector_store.search("如何定义函数", n_results=5)

for result in results:
    print(f"视频: {result['metadata']['video_path']}")
    print(f"时间: {result['metadata']['start_time']:.1f}s")
    print(f"内容: {result['document'][:100]}...")
    print("-" * 60)
```

#### 2.3 查看存储的视频

```python
from videotrans.hearsight.vector_store import get_vector_store

vector_store = get_vector_store()

# 列出所有视频
videos = vector_store.list_all_videos()
for video in videos:
    print(f"{video['topic']} - {video['paragraph_count']}段")

# 获取特定视频的摘要
summary_data = vector_store.get_video_summary("path/to/video.mp4")
print(f"主题: {summary_data['overall']['metadata']['topic']}")
```

---

## 🎛️ 配置说明

### HearSight 配置位置

配置文件: `BDvideoTrans/hearsight_config.json`

```json
{
  "llm": {
    "api_key": "your-api-key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-3.5-turbo",
    "temperature": 0.3,
    "timeout": 120
  },
  "merge": {
    "max_gap": 2.0,
    "max_duration": 30.0,
    "max_chars": 200
  }
}
```

### 向量库位置

数据存储: `BDvideoTrans/vector_db/`

---

## 🔍 检查是否正常工作

### 1. 查看日志

翻译完成后，检查日志中是否有：

```
[INFO] Starting HearSight summary generation for: ...
[INFO] Merged X paragraphs
[INFO] Generated overall summary: ...
[INFO] Generated X paragraph summaries
[INFO] ✅ Successfully stored HearSight summary in vector database
```

### 2. 检查向量库

```python
from videotrans.hearsight.vector_store import get_vector_store

vector_store = get_vector_store()
videos = vector_store.list_all_videos()
print(f"已存储视频数: {len(videos)}")
```

### 3. 测试搜索

```python
from videotrans.hearsight.vector_store import get_vector_store

vector_store = get_vector_store()
results = vector_store.search("测试查询", n_results=3)
print(f"找到 {len(results)} 个结果")
```

---

## 🐛 常见问题

### Q1: 勾选"智能摘要"后没有生成摘要？

**A**: 检查以下几点：
1. HearSight 配置是否完整（API Key 等）
2. 是否有 SRT 字幕文件生成
3. 查看日志是否有错误信息

### Q2: 提示 "ChromaDB 未安装"？

**A**: 运行安装命令：
```bash
pip install chromadb
```

### Q3: API 调用失败？

**A**:
1. 检查 API Key 是否正确
2. 检查网络连接
3. 测试 API 连接（使用配置对话框的"测试连接"按钮）

### Q4: 向量库占用空间过大？

**A**: 定期清理不需要的视频：
```python
from videotrans.hearsight.vector_store import get_vector_store
vector_store = get_vector_store()
vector_store.delete_video("path/to/old/video.mp4")
```

---

## 📚 更多信息

- **完整文档**: `HEARSIGHT_视频翻译集成方案.md`
- **段落摘要功能**: `HEARSIGHT_段落摘要功能更新.md`
- **使用指南**: `HEARSIGHT_使用指南.md`

---

## 🎉 快速演示

```python
# 完整示例：从 SRT 到向量库
from videotrans.hearsight.segment_merger import merge_srt_to_paragraphs
from videotrans.hearsight.summarizer import generate_summary, generate_paragraph_summaries
from videotrans.hearsight.vector_store import get_vector_store

# 配置
API_KEY = "your-api-key"
SRT_FILE = "output/video_zh.srt"
VIDEO_FILE = "videos/video.mp4"

# 1. 处理 SRT
paragraphs = merge_srt_to_paragraphs(SRT_FILE)
print(f"✅ 合并了 {len(paragraphs)} 个段落")

# 2. 生成摘要
summary = generate_summary(paragraphs, api_key=API_KEY)
print(f"✅ 主题: {summary['topic']}")

# 3. 生成段落摘要
paragraphs_with_summaries = generate_paragraph_summaries(paragraphs, api_key=API_KEY)
print(f"✅ 生成了 {len(paragraphs_with_summaries)} 个段落摘要")

# 4. 存储
vector_store = get_vector_store()
success = vector_store.store_summary(VIDEO_FILE, summary, paragraphs_with_summaries)
print(f"✅ 存储成功" if success else "❌ 存储失败")

# 5. 搜索测试
results = vector_store.search("测试查询", n_results=3)
print(f"✅ 找到 {len(results)} 个结果")
```

---

**版本**: v2.0
**更新日期**: 2025-10-01
