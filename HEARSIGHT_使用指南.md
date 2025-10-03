# HearSight功能使用指南 - MVP版本

## 📚 目录

1. [功能介绍](#功能介绍)
2. [快速开始](#快速开始)
3. [详细使用说明](#详细使用说明)
4. [常见问题](#常见问题)
5. [技术说明](#技术说明)

---

## 功能介绍

HearSight MVP版本为pyvideotrans添加了两个核心能力：

### ✨ 核心功能

1. **智能段落划分**
   - 基于Whisper识别的SRT字幕进行智能合并
   - 将短句合并为语义连贯的段落
   - 考虑时间间隔、句子长度、标点符号等因素

2. **LLM智能摘要**
   - 基于OpenAI兼容API生成内容摘要
   - 支持ChatGPT、DeepSeek、Gemini等所有兼容服务
   - 自动提取主题和关键信息
   - 生成简洁准确的中文总结

### 🎯 使用场景

- **学习笔记**: 快速获取视频要点
- **内容总结**: 生成会议/讲座摘要
- **内容检索**: 通过段落快速定位关键信息
- **质量检查**: 验证字幕识别效果

---

## 快速开始

### 前置条件

1. ✅ 已安装pyvideotrans
2. ✅ Python虚拟环境已激活
3. ✅ 拥有OpenAI兼容的API密钥

### 1. 测试功能（无需GUI）

使用独立测试脚本验证功能：

```bash
cd pyvideotrans
python test_hearsight.py
```

按照提示选择测试项目：
- 选项1: 测试段落合并
- 选项2: 测试摘要生成
- 选项3: 测试UI界面
- 选项4: 测试完整流程

### 2. 集成到主界面

参考 `HEARSIGHT_INTEGRATION_EXAMPLE.py` 文件，将代码集成到主窗口。

或者按照以下步骤手动集成：

#### 步骤1: 修改 `videotrans/mainwin/_main_win.py`

在 `MainWindow` 类的 `__init__` 方法末尾添加：

```python
# 初始化HearSight
self.hearsight_config = None
self.hearsight_processor = None
QTimer.singleShot(1000, self._init_hearsight)
```

添加初始化方法：

```python
def _init_hearsight(self):
    """初始化HearSight"""
    # 加载配置
    import json
    config_path = os.path.join(config.ROOT_DIR, 'hearsight_config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.hearsight_config = json.load(f)
        except:
            pass

    # 添加按钮到工具栏
    self.hearsight_btn = QPushButton("🎯 智能摘要")
    self.hearsight_btn.clicked.connect(self.open_hearsight)
    if hasattr(self, 'toolBar'):
        self.toolBar.addWidget(self.hearsight_btn)
```

复制 `HEARSIGHT_INTEGRATION_EXAMPLE.py` 中的其他方法到 `MainWindow` 类中。

---

## 详细使用说明

### 配置LLM API

首次使用需要配置LLM API参数。

#### 方法1: 通过配置对话框（推荐）

1. 点击工具栏的 "⚙️" 按钮
2. 填写配置信息：

   - **API Key**: 你的API密钥（必填）
   - **Base URL**: API地址（例如：`https://api.openai.com/v1`）
   - **Model**: 模型名称（例如：`gpt-3.5-turbo`）
   - **Temperature**: 温度参数（0.0-2.0，推荐0.3）
   - **Timeout**: 超时时间（秒）

3. 点击"测试连接"验证配置
4. 点击"保存"

#### 方法2: 手动创建配置文件

在 `pyvideotrans` 目录下创建 `hearsight_config.json`:

```json
{
  "llm": {
    "api_key": "你的API密钥",
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

### 使用HearSight功能

#### 步骤1: 准备SRT文件

确保你已经通过pyvideotrans的语音识别功能生成了SRT字幕文件。

#### 步骤2: 启动HearSight

1. 点击工具栏的 "🎯 智能摘要" 按钮
2. 选择要处理的SRT文件
3. 等待处理完成（通常需要1-2分钟）

#### 步骤3: 查看结果

处理完成后会自动弹出查看器窗口：

- **顶部区域**: 显示整体摘要
  - 主题
  - 总结内容
  - 统计信息（段落数、总时长）

- **左侧面板**: 段落列表
  - 点击任意段落查看详细内容
  - 显示时间范围和内容预览

- **右侧面板**: 段落详细内容
  - 完整文本内容
  - 时间戳信息

#### 步骤4: 导出结果

点击 "导出Markdown" 按钮，选择保存位置，即可导出为Markdown格式文件。

导出的文件包含：
- 主题和总结
- 统计信息
- 所有段落的详细内容和时间戳

---

## 常见问题

### Q1: 配置测试连接失败

**可能原因**：
- API密钥错误
- Base URL不正确
- 网络连接问题
- 代理设置问题

**解决方法**：
1. 检查API密钥是否正确复制
2. 确认Base URL格式正确（需以 `/v1` 结尾）
3. 检查网络连接
4. 如需代理，在pyvideotrans主界面配置代理

### Q2: 段落合并结果不理想

**调整参数**：

在配置对话框中调整段落合并参数：

- **最大时间间隔** (max_gap): 相邻字幕间隔超过此值则分段
  - 默认: 2.0秒
  - 增大: 合并更多短句
  - 减小: 分段更细致

- **最大段落时长** (max_duration): 单个段落最长时长
  - 默认: 30.0秒
  - 增大: 允许更长的段落
  - 减小: 强制分段更短

- **最大字符数** (max_chars): 单个段落最多字符数
  - 默认: 200字符
  - 增大: 允许更长的段落
  - 减小: 强制分段更短

### Q3: 摘要生成超时

**可能原因**：
- 视频过长，内容过多
- API响应慢
- 网络不稳定

**解决方法**：
1. 增加超时时间（配置中调整timeout参数）
2. 分段处理长视频
3. 使用速度更快的API服务

### Q4: 摘要质量不理想

**优化方法**：
1. 使用更强大的模型（如gpt-4）
2. 调整temperature参数（降低可获得更一致的结果）
3. 确保SRT字幕质量良好
4. 针对特定领域，可修改提示词模板（在 `summarizer.py` 中）

### Q5: UI显示乱码或样式异常

**解决方法**：
1. 确保系统支持中文显示
2. 检查Qt样式表是否正确加载
3. 尝试切换pyvideotrans主题

---

## 技术说明

### 模块架构

```
pyvideotrans/
└── videotrans/
    ├── hearsight/                    # HearSight核心模块
    │   ├── __init__.py              # 模块入口
    │   ├── segment_merger.py        # 段落合并逻辑
    │   ├── summarizer.py            # 摘要生成
    │   ├── chat_client.py           # OpenAI客户端
    │   └── processor.py             # 处理器线程
    └── ui/
        ├── hearsight_config.py      # 配置对话框
        └── hearsight_viewer.py      # 结果查看器
```

### 段落合并算法

采用规则基础的合并策略：

1. **时间间隔判断**: 相邻字幕时间间隔 ≤ max_gap 时考虑合并
2. **长度限制**: 合并后不超过 max_duration 和 max_chars
3. **语义边界**: 检测句号、问号等结束标点
4. **自然停顿**: 结束标点后有明显停顿则分段

### LLM提示词策略

提示词设计原则：

1. **明确任务**: 要求提取主题和生成摘要
2. **输出格式**: 严格要求JSON格式输出
3. **质量要求**: 简洁、准确、中文、无重复
4. **上下文**: 提供完整的时间戳和文本信息

提示词模板位于 `videotrans/hearsight/summarizer.py` 的 `build_summary_prompt` 函数中。

### API兼容性

支持所有OpenAI Chat Completion API兼容的服务：

| 服务 | Base URL 示例 | 说明 |
|------|---------------|------|
| OpenAI | `https://api.openai.com/v1` | 官方服务 |
| DeepSeek | `https://api.deepseek.com/v1` | 高性价比 |
| 硅基流动 | `https://api.siliconflow.cn/v1` | 国内服务 |
| Gemini | 需要转换为OpenAI格式 | 使用中间代理 |
| 本地LLM | `http://localhost:11434/v1` | Ollama等本地服务 |

### 性能考虑

- **处理时间**: 通常需要30秒-2分钟，取决于：
  - 视频长度
  - API响应速度
  - 网络状况

- **内存占用**: 约50-200MB，取决于：
  - SRT文件大小
  - 段落数量
  - UI组件

- **API成本**: 估算：
  - 10分钟视频 ≈ 1000-2000 tokens
  - gpt-3.5-turbo成本 < $0.01
  - gpt-4成本 < $0.05

---

## 扩展开发

### 自定义提示词

编辑 `videotrans/hearsight/summarizer.py` 中的 `build_summary_prompt` 函数：

```python
def build_summary_prompt(paragraphs: List[Dict[str, Any]]) -> str:
    header = """
    你的自定义提示词...
    """
    # ... 其他代码
    return header + "\n\n" + body + "\n" + footer
```

### 添加新功能

可以扩展的方向：

1. **段落级摘要**: 为每个段落生成单独摘要
2. **关键词提取**: 提取视频关键词和标签
3. **时间轴可视化**: 可视化段落分布
4. **导出更多格式**: PDF、HTML等
5. **多语言支持**: 英文摘要、双语摘要

参考 `summarizer.py` 中的 `generate_paragraph_summaries` 函数实现段落级摘要。

### 集成到视频处理流程

在视频翻译完成后自动触发摘要：

```python
# 在视频处理完成的回调中
def on_video_finished(self, video_path, srt_path):
    # 询问是否生成摘要
    reply = QMessageBox.question(
        self,
        "生成智能摘要？",
        "视频处理完成，是否生成智能摘要？",
        QMessageBox.Yes | QMessageBox.No
    )

    if reply == QMessageBox.Yes:
        # 使用生成的SRT文件启动HearSight
        self.start_hearsight_with_srt(srt_path)
```

---

## 更新日志

### v1.0 (MVP版本) - 2025-10-01

**新功能**:
- ✨ 智能段落合并
- ✨ LLM摘要生成
- ✨ 结果查看器UI
- ✨ 配置管理
- ✨ Markdown导出

**技术栈**:
- PySide6 (UI)
- OpenAI Compatible API (LLM)
- Whisper SRT (语音识别输入)

**文件清单**:
- `videotrans/hearsight/` - 核心模块
- `videotrans/ui/hearsight_*.py` - UI组件
- `test_hearsight.py` - 测试脚本
- `HEARSIGHT_INTEGRATION_EXAMPLE.py` - 集成示例
- `HEARSIGHT_使用指南.md` - 本文档

---

## 反馈和支持

如果遇到问题或有功能建议，请：

1. 检查本文档的"常见问题"部分
2. 运行 `test_hearsight.py` 进行诊断
3. 查看日志文件
4. 提交Issue到项目仓库

---

## 许可证

遵循pyvideotrans项目的许可证（GPL-V3）

---

*祝你使用愉快！🎉*
