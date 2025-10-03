# HearSight 智能摘要 + 向量库集成方案

## 📋 概述

本文档说明如何将 HearSight 智能摘要功能集成到视频翻译流程中，并自动存储到向量数据库以支持语义检索。

**更新日期**: 2025-10-01
**版本**: v2.0（视频翻译集成版）

---

## ✨ 核心功能

### 1. 自动摘要生成

当勾选"智能摘要"选项后，视频翻译完成时会自动：
- ✅ 读取生成的 SRT 字幕文件
- ✅ 将字幕合并为段落
- ✅ 生成整体摘要（主题 + 总结）
- ✅ 为每个段落生成独立摘要
- ✅ 存储到本地向量数据库

### 2. 向量数据库存储

使用 ChromaDB 实现：
- ✅ 语义搜索：基于内容相似度检索
- ✅ 持久化存储：数据保存在本地 `vector_db/` 目录
- ✅ 元数据支持：存储视频路径、时间戳、语言等信息
- ✅ 增量更新：支持添加、查询、删除操作

### 3. 非阻塞处理

- ✅ 后台线程处理：不影响主流程
- ✅ 容错机制：摘要生成失败不影响视频输出
- ✅ 日志记录：详细的处理日志便于调试

---

## 🎯 使用流程

### 步骤 1：配置 HearSight

点击工具栏的 **"⚙️"** 按钮，打开 HearSight 配置对话框：

```
┌─────────────────────────────────────┐
│  🤖  LLM API 配置                  │
├─────────────────────────────────────┤
│ API Key:    [your-api-key]         │
│ Base URL:   https://api.openai...  │
│ Model:      gpt-3.5-turbo          │
│ Temperature: 0.3                    │
│ Timeout:    120 秒                 │
├─────────────────────────────────────┤
│  📐  段落合并参数                  │
├─────────────────────────────────────┤
│ 最大时间间隔: 2.0 秒               │
│ 最大段落时长: 30.0 秒              │
│ 最大字符数:   200                  │
└─────────────────────────────────────┘
```

**必填项**：
- ✅ API Key
- ✅ Base URL（默认 OpenAI，也可使用兼容 API）
- ✅ Model（推荐 `gpt-3.5-turbo`）

### 步骤 2：启用智能摘要

在主界面底部，勾选 **"智能摘要"** 复选框：

```
┌─────────────────────────────────────┐
│ ☐ Enable CUDA?                     │
│ ☑ 智能摘要                          │ ← 勾选这个
│                                     │
│  [开始执行]                         │
└─────────────────────────────────────┘
```

**提示**: 鼠标悬停会显示："完成翻译后自动生成智能摘要并存储到向量库"

### 步骤 3：正常执行视频翻译

1. 选择视频文件
2. 配置翻译参数（源语言、目标语言等）
3. 点击 **"开始执行"**
4. 等待翻译完成

### 步骤 4：自动生成摘要

翻译完成后，系统会在后台自动：

```
[100%] 视频处理完成
   ↓
[后台] 启动 HearSight 处理
   ├─ [10%] 读取 SRT 字幕
   ├─ [30%] 合并段落（规则基础）
   ├─ [60%] 生成整体摘要
   ├─ [80%] 生成段落摘要
   └─ [100%] 存储到向量库
```

**日志示例**：
```
[INFO] Starting HearSight summary generation for: output/video_zh.srt
[INFO] Merged 15 paragraphs
[INFO] Generated overall summary: Python编程入门教程
[INFO] Generated 15 paragraph summaries
[INFO] ✅ Successfully stored HearSight summary in vector database
```

---

## 🗂️ 向量数据库结构

### 存储位置

```
pyvideotrans/
├── vector_db/           ← ChromaDB 数据目录
│   ├── chroma.sqlite3
│   └── ...
```

### 数据结构

每个视频存储的数据包括：

#### 1. 整体摘要（1条）
```python
{
    "id": "video_id_overall",
    "document": "主题: Python编程\n总结: 本视频介绍了...",
    "metadata": {
        "video_id": "md5_hash",
        "video_path": "/path/to/video.mp4",
        "type": "overall_summary",
        "topic": "Python编程",
        "paragraph_count": 15,
        "total_duration": 600.5,
        "basename": "video",
        "source_language": "en",
        "target_language": "zh"
    }
}
```

#### 2. 段落数据（N条）
```python
{
    "id": "video_id_para_0",
    "document": "段落摘要: 介绍Python的基本语法\n完整内容: 大家好...",
    "metadata": {
        "video_id": "md5_hash",
        "video_path": "/path/to/video.mp4",
        "type": "paragraph",
        "index": 0,
        "start_time": 0.0,
        "end_time": 30.5,
        "has_summary": true,
        "paragraph_summary": "介绍Python的基本语法"
    }
}
```

---

## 🔍 语义检索示例

### Python API 使用

```python
from videotrans.hearsight.vector_store import get_vector_store

# 获取向量库实例
vector_store = get_vector_store()

# 1. 语义搜索（全库）
results = vector_store.search(
    query="如何定义函数？",
    n_results=5
)

for result in results:
    print(f"匹配度: {result['distance']:.3f}")
    print(f"视频: {result['metadata']['video_path']}")
    print(f"内容: {result['document'][:100]}...")
    print("-" * 50)

# 2. 在特定视频中搜索
video_id = vector_store._generate_video_id("/path/to/video.mp4")
results = vector_store.search(
    query="变量赋值",
    n_results=3,
    video_id=video_id
)

# 3. 只搜索段落（不包含整体摘要）
results = vector_store.search(
    query="列表操作",
    n_results=5,
    filter_type="paragraph"
)

# 4. 获取视频的完整摘要
summary_data = vector_store.get_video_summary("/path/to/video.mp4")
print(f"主题: {summary_data['overall']['metadata']['topic']}")
print(f"段落数: {len(summary_data['paragraphs'])}")

# 5. 列出所有视频
videos = vector_store.list_all_videos()
for video in videos:
    print(f"{video['topic']} ({video['paragraph_count']}段)")

# 6. 删除视频数据
vector_store.delete_video("/path/to/video.mp4")
```

### 搜索结果示例

```python
# 查询: "如何定义函数？"
[
    {
        "document": "段落摘要: 介绍函数定义的基本语法\n完整内容: 在Python中，使用def关键字定义函数...",
        "metadata": {
            "video_path": "/videos/python_tutorial.mp4",
            "start_time": 120.5,
            "end_time": 150.2,
            "paragraph_summary": "介绍函数定义的基本语法"
        },
        "distance": 0.15  # 相似度高
    },
    {
        "document": "段落摘要: 演示函数参数的使用方法\n完整内容: 函数可以接受参数，例如...",
        "metadata": {
            "video_path": "/videos/python_advanced.mp4",
            "start_time": 45.0,
            "end_time": 75.8
        },
        "distance": 0.28
    }
]
```

---

## ⚙️ 配置说明

### HearSight 配置项

#### LLM API 配置
| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `api_key` | **必填** | OpenAI 兼容 API 密钥 |
| `base_url` | `https://api.openai.com/v1` | API 基础 URL |
| `model` | `gpt-3.5-turbo` | 模型名称 |
| `temperature` | `0.3` | 温度参数（0.0-2.0） |
| `timeout` | `120` | 请求超时时间（秒） |

#### 段落合并配置
| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `max_gap` | `2.0` | 最大时间间隔（秒） |
| `max_duration` | `30.0` | 最大段落时长（秒） |
| `max_chars` | `200` | 最大字符数 |

### 向量库配置

向量库使用默认配置，存储在 `pyvideotrans/vector_db/` 目录。

如需自定义，可修改 `vector_store.py`:
```python
# 自定义持久化目录
vector_store = VectorStore(persist_directory="/custom/path")
```

---

## 💡 工作原理

### 处理流程

```
┌─────────────────────────────────────────────────────────┐
│                 视频翻译主流程                          │
│  1. 提取音频                                            │
│  2. 语音识别（生成 SRT）                                │
│  3. 翻译字幕                                            │
│  4. 配音生成                                            │
│  5. 视频合成                                            │
│  ✅ 翻译完成                                            │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ├─→ [if enable_hearsight = true]
                  │
         ┌────────▼────────────────────────────┐
         │    HearSight 后台处理线程           │
         │  (非阻塞，不影响主流程)             │
         └────────┬────────────────────────────┘
                  │
    ┌─────────────▼───────────────┐
    │  Step 1: 读取 SRT 文件      │
    │  - 优先目标语言字幕          │
    │  - 回退到源语言字幕          │
    └─────────────┬───────────────┘
                  │
    ┌─────────────▼───────────────┐
    │  Step 2: 合并段落           │
    │  - 基于时间间隔              │
    │  - 基于字符限制              │
    │  - 基于标点符号              │
    └─────────────┬───────────────┘
                  │
    ┌─────────────▼───────────────┐
    │  Step 3: 生成整体摘要       │
    │  - LLM API 调用（1次）      │
    │  - 提取主题 + 总结           │
    └─────────────┬───────────────┘
                  │
    ┌─────────────▼───────────────┐
    │  Step 4: 生成段落摘要       │
    │  - LLM API 调用（N次）      │
    │  - 每段不超过50字            │
    └─────────────┬───────────────┘
                  │
    ┌─────────────▼───────────────┐
    │  Step 5: 存储向量库         │
    │  - 1条整体摘要              │
    │  - N条段落数据              │
    │  - 语义向量嵌入              │
    └─────────────┬───────────────┘
                  │
                  ✅ 完成
```

### 代码集成点

#### 1. UI 层（`videotrans/ui/en.py`）
```python
# 添加智能摘要复选框
self.enable_hearsight = QtWidgets.QCheckBox(self.layoutWidget)
self.enable_hearsight.setToolTip("完成翻译后自动生成智能摘要并存储到向量库")
```

#### 2. 主窗口（`videotrans/mainwin/_main_win.py`）
```python
# 设置文本和状态
self.enable_hearsight.setText('智能摘要')
self.enable_hearsight.setChecked(bool(config.params.get('enable_hearsight', False)))
```

#### 3. 任务完成回调（`videotrans/task/trans_create.py`）
```python
def task_done(self):
    # ... 现有逻辑 ...

    # 启动 HearSight 后台处理
    def _hearsight_local():
        if not config.params.get('enable_hearsight', False):
            return

        # 1. 读取配置
        # 2. 查找 SRT 文件
        # 3. 生成摘要
        # 4. 存储向量库

    threading.Thread(target=_hearsight_local, daemon=True).start()
```

#### 4. 向量存储（`videotrans/hearsight/vector_store.py`）
```python
class VectorStore:
    def store_summary(self, video_path, summary, paragraphs, metadata):
        # 1. 存储整体摘要
        # 2. 存储每个段落
        # 3. 自动生成向量嵌入

    def search(self, query, n_results=5):
        # 语义搜索
        return results
```

---

## 🚀 性能与成本

### 处理时间

以 10分钟视频（15个段落）为例：

| 步骤 | 耗时 | 说明 |
|------|------|------|
| 读取 SRT | <1秒 | IO 操作 |
| 合并段落 | <5秒 | 本地计算 |
| 整体摘要 | 10-30秒 | LLM API 调用 |
| 段落摘要 | 15-45秒 | 15次 LLM 调用 |
| 存储向量库 | 2-5秒 | 本地写入 + 嵌入 |
| **总计** | **30-90秒** | 后台处理，不阻塞 |

### API 成本

使用 `gpt-3.5-turbo` 计费（以10分钟视频为例）：

| 项目 | Tokens | 成本 (USD) |
|------|--------|-----------|
| 整体摘要（输入） | ~800 | $0.0008 |
| 整体摘要（输出） | ~200 | $0.0003 |
| 段落摘要（输入）| ~2250 (15×150) | $0.00225 |
| 段落摘要（输出）| ~750 (15×50) | $0.0011 |
| **总计** | ~4000 | **$0.0045** |

**约 3 分钱人民币** per 10-minute video

### 优化建议

#### 降低成本
1. 使用国产模型（DeepSeek、Qwen 等）
2. 减少段落数量（增大 `max_duration`）
3. 使用更便宜的模型

#### 提高速度
1. 增加 API timeout
2. 使用更快的 API 服务商
3. 考虑本地 LLM（Ollama）

#### 提升质量
1. 使用 `gpt-4` 或 `claude-3-sonnet`
2. 调整 temperature（0.3-0.5）
3. 优化提示词

---

## 🐛 故障排查

### 问题 1: 摘要未生成

**症状**: 翻译完成，但没有看到摘要生成日志

**检查清单**:
- ✅ 是否勾选了"智能摘要"复选框？
- ✅ HearSight 配置是否完整（API Key 等）？
- ✅ 是否有 SRT 字幕文件生成？
- ✅ 查看日志文件是否有错误信息

**解决方案**:
```python
# 查看日志
import logging
logging.basicConfig(level=logging.INFO)

# 手动测试
from videotrans.hearsight.vector_store import get_vector_store
vector_store = get_vector_store()
videos = vector_store.list_all_videos()
print(f"已存储视频数: {len(videos)}")
```

### 问题 2: ChromaDB 未安装

**症状**: 报错 `ModuleNotFoundError: No module named 'chromadb'`

**解决方案**:
```bash
# 安装 ChromaDB
pip install chromadb

# 验证安装
python -c "import chromadb; print(chromadb.__version__)"
```

### 问题 3: API 调用失败

**症状**: 日志显示 "HearSight local summary error"

**可能原因**:
1. API Key 无效
2. 网络连接问题
3. API 配额耗尽
4. Base URL 配置错误

**解决方案**:
```python
# 测试 API 连接
from videotrans.hearsight.chat_client import chat_simple

response = chat_simple(
    prompt="你好",
    api_key="your-api-key",
    base_url="https://api.openai.com/v1",
    model="gpt-3.5-turbo"
)
print(response)  # 应该返回问候语
```

### 问题 4: 向量库占用空间过大

**症状**: `vector_db/` 目录占用磁盘空间较大

**解决方案**:
```python
# 清理不需要的视频数据
from videotrans.hearsight.vector_store import get_vector_store

vector_store = get_vector_store()

# 列出所有视频
videos = vector_store.list_all_videos()
for video in videos:
    print(f"{video['video_path']} - {video['topic']}")

# 删除特定视频
vector_store.delete_video("/path/to/old/video.mp4")
```

---

## 📊 使用场景

### 场景 1: 视频内容检索

**需求**: 在大量翻译过的视频中快速找到相关内容

```python
from videotrans.hearsight.vector_store import get_vector_store

vector_store = get_vector_store()

# 搜索: "如何使用列表推导式"
results = vector_store.search(
    query="列表推导式用法示例",
    n_results=10
)

for r in results:
    meta = r['metadata']
    print(f"视频: {meta['basename']}")
    print(f"时间: {meta['start_time']:.1f}s - {meta['end_time']:.1f}s")
    print(f"内容: {r['document'][:100]}...")
    print("-" * 60)
```

### 场景 2: 视频内容分析

**需求**: 分析视频的主题和结构

```python
from videotrans.hearsight.vector_store import get_vector_store

vector_store = get_vector_store()

# 获取完整摘要
summary_data = vector_store.get_video_summary("/path/to/video.mp4")

# 分析
print(f"主题: {summary_data['overall']['metadata']['topic']}")
print(f"总时长: {summary_data['overall']['metadata']['total_duration']}秒")
print(f"\n段落结构:")

for i, para in enumerate(summary_data['paragraphs'], 1):
    meta = para['metadata']
    duration = meta['end_time'] - meta['start_time']
    summary = meta.get('paragraph_summary', '无')
    print(f"  {i}. [{duration:.1f}s] {summary}")
```

### 场景 3: 批量处理历史视频

**需求**: 为之前翻译的视频补充生成摘要

```python
import os
from pathlib import Path
from videotrans.hearsight.segment_merger import merge_srt_to_paragraphs
from videotrans.hearsight.summarizer import generate_summary, generate_paragraph_summaries
from videotrans.hearsight.vector_store import get_vector_store

# 配置
llm_cfg = {
    'api_key': 'your-api-key',
    'base_url': 'https://api.openai.com/v1',
    'model': 'gpt-3.5-turbo'
}

vector_store = get_vector_store()

# 查找所有 SRT 文件
srt_dir = Path("/path/to/output/dir")
for srt_file in srt_dir.rglob("*.srt"):
    print(f"处理: {srt_file}")

    try:
        # 1. 合并段落
        paragraphs = merge_srt_to_paragraphs(str(srt_file))

        # 2. 生成摘要
        summary = generate_summary(paragraphs, **llm_cfg)
        paragraphs_with_summaries = generate_paragraph_summaries(paragraphs, **llm_cfg)

        # 3. 存储
        video_path = str(srt_file.with_suffix('.mp4'))
        vector_store.store_summary(video_path, summary, paragraphs_with_summaries)

        print(f"  ✅ 完成")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
```

---

## 📚 API 参考

### VectorStore 类

#### `__init__(persist_directory=None)`
初始化向量存储

**参数**:
- `persist_directory` (str, optional): 持久化目录路径

#### `initialize() -> bool`
初始化 ChromaDB 客户端

**返回**: 初始化是否成功

#### `store_summary(video_path, summary, paragraphs, metadata=None) -> bool`
存储视频摘要

**参数**:
- `video_path` (str): 视频文件路径
- `summary` (dict): 整体摘要
- `paragraphs` (list): 段落列表
- `metadata` (dict, optional): 额外元数据

**返回**: 是否存储成功

#### `search(query, n_results=5, video_id=None, filter_type=None) -> List[Dict]`
语义搜索

**参数**:
- `query` (str): 查询文本
- `n_results` (int): 返回结果数量
- `video_id` (str, optional): 限制在特定视频
- `filter_type` (str, optional): 过滤类型

**返回**: 搜索结果列表

#### `delete_video(video_path) -> bool`
删除视频数据

**参数**:
- `video_path` (str): 视频路径

**返回**: 是否删除成功

#### `get_video_summary(video_path) -> Optional[Dict]`
获取视频完整摘要

**参数**:
- `video_path` (str): 视频路径

**返回**: 摘要数据或 None

#### `list_all_videos() -> List[Dict]`
列出所有视频

**返回**: 视频列表

---

## 🎯 总结

### 已实现功能

✅ **UI 集成**
- 主界面添加"智能摘要"复选框
- HearSight 配置对话框

✅ **核心功能**
- 视频翻译完成后自动生成摘要
- 整体摘要 + 段落级摘要
- 非阻塞后台处理

✅ **向量数据库**
- ChromaDB 存储
- 语义搜索
- 持久化 + 元数据

✅ **容错机制**
- API 调用失败处理
- 日志记录
- 不影响主流程

### 使用优势

1. **自动化**: 无需手动操作，勾选即可
2. **高效**: 后台处理，不影响主流程
3. **智能**: 基于 LLM 的高质量摘要
4. **可检索**: 向量库支持语义搜索
5. **低成本**: 每个10分钟视频约3分钱

### 下一步优化

可能的改进方向：
1. **并发处理**: 使用线程池加速段落摘要生成
2. **缓存机制**: 避免重复内容的重复调用
3. **Web UI**: 提供向量库管理界面
4. **多模态**: 支持视频帧分析
5. **导出功能**: 导出摘要为 PDF/HTML

---

**开发完成时间**: 2025-10-01
**版本**: v2.0（视频翻译集成版）
