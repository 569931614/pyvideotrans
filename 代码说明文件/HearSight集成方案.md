# HearSight功能集成方案 - BDvideoTrans

## 一、目标功能

将HearSight的核心能力集成到BDvideoTrans项目中：

1. **智能段落划分** - 音频转文字并按时间戳生成语义连贯的段落
2. **时间轴播放器** - 支持精确定位与播放同步的交互式视频播放器
3. **LLM摘要生成** - 基于大语言模型生成段落级与视频级摘要/总结
4. **历史记录管理** - 数据库存储转写记录和摘要，支持检索和管理

## 二、技术架构设计

### 2.1 现有BDvideoTrans架构分析

```
BDvideoTrans/
├── videotrans/
│   ├── recognition/      # 现有语音识别模块
│   ├── translator/       # 翻译模块
│   ├── tts/             # 文本转语音
│   ├── task/            # 任务处理
│   ├── mainwin/         # 主窗口
│   ├── ui/              # UI组件
│   └── util/            # 工具函数
└── sp.py                # GUI入口
```

### 2.2 新增模块设计

```
BDvideoTrans/
├── videotrans/
│   ├── hearsight/                    # 【新增】HearSight功能模块
│   │   ├── __init__.py
│   │   ├── asr_segment.py           # ASR段落识别（基于FunASR）
│   │   ├── summarizer.py            # LLM摘要生成
│   │   ├── transcript_db.py         # 转写记录数据库管理
│   │   └── chat_client.py           # OpenAI兼容的聊天客户端
│   │
│   ├── winform/
│   │   └── hearsight_player.py      # 【新增】HearSight播放器窗口
│   │
│   └── ui/
│       └── hearsight_config.py      # 【新增】HearSight配置UI
│
└── requirements.txt                  # 添加新依赖
```

## 三、核心功能实现

### 3.1 ASR段落识别模块 (`videotrans/hearsight/asr_segment.py`)

**功能说明**：
- 使用FunASR的Paraformer模型进行语音识别
- 自动VAD（语音活动检测）
- 自动添加标点符号
- 说话人分离（可选）
- 输出带时间戳的段落列表

**数据结构**：
```python
Segment = {
    "index": int,           # 段落索引
    "spk_id": str,          # 说话人ID（可选）
    "sentence": str,        # 文本内容
    "start_time": float,    # 开始时间（秒）
    "end_time": float       # 结束时间（秒）
}
```

**依赖**：
- `funasr` - 阿里达摩院语音识别库
- 模型会自动下载到 `models/funasr/` 目录

**与现有识别模块的关系**：
- BDvideoTrans已有的faster-whisper/openai-whisper生成SRT字幕
- HearSight的段落识别生成更适合摘要的语义段落
- 两者可以共存，用户根据需求选择

### 3.2 LLM摘要生成模块 (`videotrans/hearsight/summarizer.py`)

**功能说明**：
- 基于段落列表生成摘要
- 支持段落级摘要（每个段落一个摘要）
- 支持视频级总摘要（整体概览）
- 使用tiktoken进行token计数，避免超过模型限制
- 支持所有OpenAI兼容的API（ChatGPT、DeepSeek、Gemini等）

**输出格式**：
```python
SummaryItem = {
    "topic": str,           # 主题
    "summary": str,         # 摘要内容
    "start_time": float,    # 对应时间段开始
    "end_time": float       # 对应时间段结束
}
```

**配置参数**：
- API Key
- Base URL
- Model名称
- Max tokens（默认1,000,000）

**提示词策略**：
- 明确要求JSON格式输出
- 中文摘要，简洁准确
- 避免重复原文
- 包含时间戳信息

### 3.3 转写记录数据库 (`videotrans/hearsight/transcript_db.py`)

**功能说明**：
- 存储视频转写记录
- 存储段落列表和摘要
- 支持历史记录查询和管理

**数据库方案**：
- **方案A（推荐）**：使用SQLite（轻量级，无需额外配置）
  - 数据库文件：`BDvideoTrans/hearsight_data.db`
  - 适合单机应用

- **方案B（可选）**：PostgreSQL（如需多用户/网络访问）
  - 需要额外配置

**表结构**：
```sql
-- 转写记录表
CREATE TABLE transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_path TEXT NOT NULL,        -- 视频/音频文件路径
    media_name TEXT,                 -- 文件名
    segments_json TEXT NOT NULL,     -- 段落JSON数据
    summary_json TEXT,               -- 摘要JSON数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_transcripts_media ON transcripts(media_path);
CREATE INDEX idx_transcripts_created ON transcripts(created_at DESC);
```

### 3.4 交互式播放器UI (`videotrans/winform/hearsight_player.py`)

**功能说明**：
- 视频播放控件（基于PySide6）
- 时间轴显示（可视化段落分布）
- 段落列表展示（左侧或右侧面板）
- 摘要显示（可折叠）
- 时间戳跳转（点击段落直接跳转）
- 播放同步（播放时高亮当前段落）

**界面布局**：
```
┌────────────────────────────────────────────────────┐
│  [文件] [播放] [设置]                    [最小化][关闭] │
├────────────────┬───────────────────────────────────┤
│                │                                   │
│  段落列表       │      视频播放区域                  │
│  [00:00-00:05] │                                   │
│  段落1内容...   │                                   │
│                │                                   │
│  [00:05-00:15] │                                   │
│  段落2内容...   │                                   │
│                │                                   │
│  [摘要]        │                                   │
│  总结内容...    │                                   │
│                │                                   │
├────────────────┴───────────────────────────────────┤
│  [播放] [暂停] [停止]  进度条 [00:12/05:30]          │
└────────────────────────────────────────────────────┘
```

**技术选型**：
- **视频播放**：PySide6.QtMultimedia（QMediaPlayer + QVideoWidget）
- **时间轴**：自定义QWidget绘制
- **列表**：QListWidget或QTreeWidget
- **布局**：QSplitter实现可调整大小的分栏

**交互功能**：
1. 点击段落 → 视频跳转到对应时间
2. 播放进度 → 自动滚动并高亮当前段落
3. 双击段落 → 编辑内容（支持手动修正识别错误）
4. 右键菜单 → 复制、导出、重新生成摘要

### 3.5 配置UI (`videotrans/ui/hearsight_config.py`)

**配置项**：
1. **ASR配置**
   - 模型选择（paraformer-zh / sense-voice等）
   - 是否启用说话人分离
   - VAD参数

2. **LLM配置**
   - API Key
   - Base URL
   - Model名称
   - 温度、Max tokens等参数

3. **UI配置**
   - 播放器主题
   - 字体大小
   - 时间轴样式

## 四、集成到BDvideoTrans主界面

### 4.1 添加新菜单项

在主窗口菜单栏添加"HearSight"菜单：

```python
# videotrans/mainwin/_main_win.py

hearsight_menu = self.menuBar().addMenu("HearSight")

# 子菜单项
action_open_player = QAction("打开视频播放器", self)
action_open_player.triggered.connect(self.open_hearsight_player)
hearsight_menu.addAction(action_open_player)

action_batch_transcribe = QAction("批量转写和摘要", self)
action_batch_transcribe.triggered.connect(self.batch_transcribe)
hearsight_menu.addAction(action_batch_transcribe)

action_history = QAction("历史记录", self)
action_history.triggered.connect(self.show_transcript_history)
hearsight_menu.addAction(action_history)

action_config = QAction("配置", self)
action_config.triggered.connect(self.show_hearsight_config)
hearsight_menu.addAction(action_config)
```

### 4.2 添加快捷按钮

在主界面工具栏或侧边栏添加HearSight快捷入口：

```python
# 添加HearSight工具按钮
btn_hearsight = QPushButton("HearSight播放器")
btn_hearsight.clicked.connect(self.open_hearsight_player)
# 添加到主界面布局
```

### 4.3 与现有功能的协同

**场景1：视频翻译后查看摘要**
- 用户完成视频翻译 → 自动提示"是否生成摘要？"
- 点击"是" → 使用已有的识别结果生成摘要 → 打开HearSight播放器

**场景2：仅做转写和摘要**
- 用户选择视频文件 → 点击"HearSight播放器"
- 自动进行ASR识别 → 生成摘要 → 显示结果

**场景3：历史记录复用**
- 如果视频已转写过，直接加载历史记录
- 避免重复计算，提升用户体验

## 五、实施步骤

### 阶段1：基础模块开发（3-5天）

1. **创建模块结构**
   ```bash
   mkdir -p BDvideoTrans/videotrans/hearsight
   touch BDvideoTrans/videotrans/hearsight/__init__.py
   touch BDvideoTrans/videotrans/hearsight/asr_segment.py
   touch BDvideoTrans/videotrans/hearsight/summarizer.py
   touch BDvideoTrans/videotrans/hearsight/transcript_db.py
   touch BDvideoTrans/videotrans/hearsight/chat_client.py
   ```

2. **实现ASR段落识别**
   - 从HearSight移植`asr_sentence_segments.py`代码
   - 适配BDvideoTrans的文件路径结构
   - 测试识别效果

3. **实现LLM摘要生成**
   - 从HearSight移植`summarize.py`和`chat_client.py`
   - 测试摘要生成效果
   - 处理token超限情况

4. **实现数据库模块**
   - 使用SQLite实现`transcript_db.py`
   - 实现CRUD操作
   - 添加索引优化查询

### 阶段2：UI开发（5-7天）

1. **开发播放器窗口**
   - 创建基础窗口框架
   - 集成QMediaPlayer视频播放
   - 实现段落列表显示
   - 实现时间戳跳转

2. **开发时间轴组件**
   - 自定义QWidget绘制时间轴
   - 可视化段落分布
   - 支持拖拽调整

3. **开发配置UI**
   - 创建配置对话框
   - 集成到主窗口设置

4. **UI优化和美化**
   - 适配深色/浅色主题
   - 响应式布局
   - 添加图标和提示

### 阶段3：集成和测试（2-3天）

1. **集成到主界面**
   - 添加菜单项
   - 添加快捷按钮
   - 实现与现有功能的联动

2. **端到端测试**
   - 测试完整流程：视频导入 → ASR识别 → 生成摘要 → 播放器查看
   - 测试边界情况：长视频、多说话人、识别错误等
   - 性能测试：大文件处理、内存占用等

3. **文档编写**
   - 用户使用手册
   - API文档
   - 配置说明

### 阶段4：优化和发布（1-2天）

1. **性能优化**
   - 异步处理长时间任务
   - 进度条显示
   - 缓存优化

2. **错误处理**
   - 友好的错误提示
   - 异常恢复机制
   - 日志记录

3. **发布准备**
   - 更新requirements.txt
   - 更新README
   - 发布测试版本

## 六、依赖变更

### 6.1 新增Python依赖

在`BDvideoTrans/requirements.txt`中添加：

```txt
# HearSight功能依赖
funasr>=1.0.0              # 语音识别
modelscope>=1.0.0          # FunASR模型下载（已有）
tiktoken>=0.5.0            # Token计数
```

### 6.2 可选依赖

```txt
# SQLite是Python内置，无需额外安装
# 如使用PostgreSQL则需要：
psycopg2-binary>=2.9.0     # PostgreSQL驱动
```

## 七、配置文件变更

### 7.1 新增配置节

在`videotrans/set.ini`或创建`hearsight_config.json`：

```json
{
    "hearsight": {
        "asr": {
            "model": "paraformer-zh",
            "enable_speaker_separation": false,
            "vad_threshold": 0.5
        },
        "llm": {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-3.5-turbo",
            "temperature": 0.3,
            "max_tokens": 1000000
        },
        "ui": {
            "theme": "auto",
            "font_size": 12,
            "show_timestamps": true
        },
        "database": {
            "type": "sqlite",
            "path": "hearsight_data.db"
        }
    }
}
```

## 八、注意事项和风险

### 8.1 技术风险

1. **模型下载问题**
   - FunASR模型较大（~1GB）
   - 首次使用需要下载
   - **解决方案**：提供国内镜像或预打包模型

2. **内存占用**
   - 视频播放 + ASR模型同时运行可能占用大量内存
   - **解决方案**：分步处理，ASR完成后释放模型

3. **跨平台兼容性**
   - FunASR主要在Linux/macOS上测试
   - Windows支持需要额外验证
   - **解决方案**：提供备选方案（使用现有的faster-whisper）

### 8.2 用户体验风险

1. **学习成本**
   - 新增功能需要用户学习
   - **解决方案**：提供详细教程和示例视频

2. **性能感知**
   - ASR和摘要生成需要时间
   - **解决方案**：显示进度条和预计时间

### 8.3 维护成本

1. **依赖维护**
   - FunASR更新可能导致API变化
   - **解决方案**：锁定版本号，定期更新测试

2. **数据库迁移**
   - 未来可能需要更改表结构
   - **解决方案**：使用数据库版本控制和迁移脚本

## 九、未来扩展方向

### 9.1 短期扩展（1-3个月）

1. **支持更多ASR模型**
   - SenseVoice（多语言）
   - Whisper-large-v3（更高精度）
   - 用户自定义模型

2. **增强摘要功能**
   - 分段摘要（自动分段）
   - 多语言摘要
   - 关键词提取

3. **导出功能**
   - 导出摘要为Markdown/PDF
   - 导出带时间戳的全文本
   - 导出到笔记软件（Notion、Obsidian等）

### 9.2 中期扩展（3-6个月）

1. **AI辅助功能**
   - 智能问答（基于视频内容）
   - 内容检索（语义搜索）
   - 自动标签和分类

2. **协作功能**
   - 共享转写记录
   - 多人标注
   - 评论和讨论

3. **高级分析**
   - 说话人情感分析
   - 主题演变分析
   - 关键时刻检测

### 9.3 长期规划（6-12个月）

1. **云端服务**
   - 云端ASR和摘要
   - 跨设备同步
   - API服务

2. **移动端**
   - Android/iOS应用
   - 快速查看和编辑

3. **企业版功能**
   - 团队协作
   - 权限管理
   - 高级统计和报表

## 十、总结

本方案旨在将HearSight的核心能力无缝集成到BDvideoTrans中，为用户提供：

1. **更智能的语音识别** - 段落级别的语义理解
2. **AI驱动的内容理解** - 自动摘要和总结
3. **更好的内容交互** - 可视化播放和时间戳导航
4. **完整的历史管理** - 数据库存储和检索

通过分阶段实施，我们可以逐步验证和优化每个功能模块，确保最终产品的质量和用户体验。

**预计总工期：11-17天**

---

*文档版本：v1.0*
*创建日期：2025-10-01*
*作者：Claude Code*
