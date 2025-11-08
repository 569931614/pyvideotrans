# HTML UI 任务处理修复说明

## 🐛 问题诊断

### 症状
选择视频文件后点击"开始处理"，任务队列显示但没有实际处理动作。

### 根本原因

**问题1**: `check_start()` 方法依赖Qt UI控件
```python
# Qt UI读取方式（HTML UI不适用）
self.cfg['translate_type'] = self.main.translate_type.currentIndex()
self.cfg['source_language'] = self.main.source_language.currentText()
```

**问题2**: 直接调用 `check_start()` 无法工作
HTML UI 没有Qt控件（如 `translate_type`, `source_language` 等），导致读取失败。

**问题3**: 错误的任务创建方式
最初尝试直接调用 `task.start()`，但系统使用**队列机制**处理任务。

---

## ✅ 解决方案

### 核心修改：重写 `startTranslate()` 方法

**文件**: `videotrans/ui/webbridge.py`

#### 1. 从 `config.params` 读取配置

```python
cfg = {
    'translate_type': config.params.get('translate_type', 0),
    'source_language': config.params.get('source_language', ''),
    'target_language': config.params.get('target_language', '-'),
    'tts_type': config.params.get('tts_type', 0),
    'voice_role': config.params.get('voice_role', 'No'),
    # ... 所有必要参数
}
```

**优势**:
- ✅ 不依赖Qt控件
- ✅ HTML UI 已通过 `setParams()` 更新了 `config.params`
- ✅ 所有配置都在 `config.params` 中

#### 2. 使用队列系统

```python
from videotrans.task.trans_create import TransCreate
import uuid as uuid_module

for video_path in win_action.queue_mp4:
    task_uuid = uuid_module.uuid4().hex
    task = TransCreate(
        uuid=task_uuid,
        cfg=cfg.copy(),
        source_mp4=video_path,
        target_dir=config.params.get('target_dir', ''),
    )
    # ✅ 添加到准备队列，Worker线程会自动处理
    config.prepare_queue.append(task)
```

---

## 🔄 任务处理流程

### BDvideoTrans 任务队列架构

```
用户点击"开始处理"
    ↓
startTranslate() 创建任务
    ↓
添加到 config.prepare_queue
    ↓
WorkerPrepare 线程拾取任务
    ↓
task.prepare() 预处理
    ↓
根据需要分发到不同队列：
├─ config.regcon_queue  (语音识别)
├─ config.trans_queue   (翻译)
├─ config.dubb_queue    (配音)
└─ config.assemb_queue  (合成)
    ↓
各自的Worker线程处理
    ↓
最终输出视频
```

### Worker 线程列表

| Worker | 队列 | 功能 |
|--------|------|------|
| WorkerPrepare | prepare_queue | 预处理（提取音频等） |
| WorkerRegcon | regcon_queue | 语音识别 |
| WorkerTrans | trans_queue | 字幕翻译 |
| WorkerDubb | dubb_queue | 配音生成 |
| WorkerAlign | align_queue | 音频对齐 |
| WorkerAssemb | assemb_queue | 视频合成 |

---

## 📋 完整的配置参数映射

| 参数名 | HTML UI | config.params | 说明 |
|--------|---------|---------------|------|
| translate_type | 翻译渠道下拉 | ✅ | 翻译服务类型（0-N） |
| source_language | 原语言下拉 | ✅ | 源语言名称 |
| target_language | 目标语言下拉 | ✅ | 目标语言名称 |
| tts_type | 配音渠道下拉 | ✅ | TTS服务类型（0-N） |
| voice_role | 配音角色输入框 | ✅ | 配音角色名称 |
| volume | 音量调整输入框 | ✅ | 音量调整（+0%格式） |
| pitch | 音调调整输入框 | ✅ | 音调调整（+0Hz格式） |
| recogn_type | 识别类型下拉 | ✅ | 语音识别类型（0-N） |
| model_name | 识别模型下拉 | ✅ | 识别模型名称 |
| split_type | 切割方式下拉 | ✅ | all/avg |
| subtitle_type | 字幕输出下拉 | ✅ | 字幕类型（0-4） |
| voice_rate | 语速调整输入框 | ✅ | 语速（+0%格式） |
| voice_autorate | 配音加速复选框 | ✅ | 布尔值 |
| video_autorate | 视频慢速复选框 | ✅ | 布尔值 |
| cuda | 启用CUDA复选框 | ✅ | 布尔值 |
| remove_noise | 降噪处理复选框 | ✅ | 布尔值 |

---

## 🧪 测试步骤

### 1. 启动程序
```bash
python sp.py
```

### 2. 切换到HTML UI
点击工具栏的 **"HTML UI"** 按钮

### 3. 配置参数
- 选择翻译渠道
- 选择源语言和目标语言
- 配置识别和配音选项

### 4. 选择视频
- 点击 **"📹 选择视频"**
- 选择一个或多个视频文件
- 确认任务队列显示文件列表

### 5. 开始处理
- 点击 **"开始处理"** 按钮
- 查看终端输出：
  ```
  Starting translation with config: {...}
  Queue: 2 videos
  Task added to queue: D:\Videos\video1.mp4
  Task added to queue: D:\Videos\video2.mp4
  ```

### 6. 观察处理过程
- Worker线程自动处理任务
- 查看输出目录中生成的文件

---

## 🔍 调试信息

启动处理时，终端会输出详细日志：

```python
# 配置信息
Starting translation with config: {
    'translate_type': 0,
    'source_language': '中文',
    'target_language': 'English',
    'tts_type': 0,
    'voice_role': 'zh-CN-XiaoxiaoNeural',
    # ...
}

# 队列信息
Queue: 2 videos

# 任务创建
Task added to queue: D:\Videos\video1.mp4
Task added to queue: D:\Videos\video2.mp4
```

如果出现错误，会打印完整的堆栈跟踪。

---

## ⚠️ 常见问题

### Q1: 点击"开始处理"后没有反应

**检查**:
1. 打开终端/控制台，查看是否有错误日志
2. 确认已选择视频文件（任务队列不为空）
3. 查看 `config.prepare_queue` 是否有任务

**解决**:
```python
# 在 Python 控制台检查
from videotrans.configure import config
print(f"Prepare queue: {len(config.prepare_queue)} tasks")
```

### Q2: Worker线程未启动

**检查**:
主窗口初始化时应该调用 `start_thread()`

**解决**:
在 `_main_win.py` 的 `_bindsignal()` 方法中确认：
```python
from videotrans.task.job import start_thread
start_thread(self)
```

### Q3: 配置参数不正确

**检查**:
```python
# 查看当前配置
from videotrans.configure import config
print(config.params)
```

**解决**:
确认HTML UI的所有下拉框和输入框都正确绑定了 `setParams()`。

---

## 📊 对比：Qt UI vs HTML UI 启动方式

| 步骤 | Qt UI | HTML UI |
|------|-------|---------|
| 读取配置 | 从Qt控件 `.currentIndex()` | 从 `config.params.get()` |
| 验证参数 | `check_start()` 内部验证 | 简化验证（待完善） |
| 创建任务 | `check_start()` → 队列 | 直接创建 → 队列 |
| 队列机制 | ✅ 使用 | ✅ 使用 |
| Worker线程 | ✅ 共享 | ✅ 共享 |

---

## 🔜 后续改进

### 1. 参数验证
当前实现跳过了一些验证步骤，建议添加：
- ✅ 检查代理设置
- ✅ 检查识别模型可用性
- ✅ 检查翻译服务配置
- ✅ 检查TTS服务配置

### 2. 进度反馈
添加实时进度更新：
- 通过 WebChannel Signal 发送进度事件
- 更新任务队列UI状态
- 显示当前处理步骤

### 3. 日志输出
在HTML UI中显示处理日志：
- 捕获 `config.logger` 输出
- 通过WebChannel传递到JavaScript
- 显示在日志面板中

### 4. 错误处理
改进错误提示：
- 更友好的错误消息
- 提供解决建议
- 允许重试失败的任务

---

## 📝 代码变更总结

### 修改文件
- `videotrans/ui/webbridge.py` (startTranslate方法完全重写)

### 新增功能
- ✅ 从 `config.params` 读取配置
- ✅ 使用队列系统添加任务
- ✅ 详细的调试日志输出
- ✅ 错误处理和堆栈跟踪

### 删除依赖
- ❌ 不再依赖 Qt UI 控件
- ❌ 不再调用 `check_start()`

---

**修复完成时间**: 2025-10-02
**版本**: v3.2
**状态**: ✅ 已测试并验证

现在HTML UI可以正常启动视频处理任务了！🎉
