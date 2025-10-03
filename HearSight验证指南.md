# HearSight功能验证步骤

## ✅ 已完成的集成

现在HearSight功能已经成功集成到pyvideotrans主窗口！

### 集成内容

1. **修改了主窗口文件** (`videotrans/mainwin/_main_win.py`)
   - ✅ 添加了初始化调用 `_init_hearsight()`
   - ✅ 添加了所有HearSight相关方法（230行代码）
   - ✅ 在工具栏添加了两个按钮

2. **创建的模块文件**
   - ✅ `videotrans/hearsight/` - 核心模块（5个文件）
   - ✅ `videotrans/ui/hearsight_*.py` - UI组件（2个文件）

---

## 🚀 如何验证功能

### 步骤1: 启动pyvideotrans

```bash
cd pyvideotrans

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 启动程序
python sp.py
```

### 步骤2: 查找HearSight按钮

启动后，在主窗口的工具栏（顶部）查找：

- 🟢 **绿色按钮** "🎯 智能摘要" - 点击启动功能
- ⚙️ **齿轮按钮** - 点击打开配置

![工具栏位置示意]
```
╔════════════════════════════════════════════════╗
║ 文件  编辑  工具  帮助                          ║
╠════════════════════════════════════════════════╣
║ [选择视频] [保存到] ... [🎯 智能摘要] [⚙️]      ║
╠════════════════════════════════════════════════╣
║                                                ║
║          主界面内容区域                         ║
║                                                ║
╚════════════════════════════════════════════════╝
```

### 步骤3: 配置LLM API

首次使用需要配置：

1. 点击 **⚙️** 按钮
2. 填写配置信息：
   - **API Key**: 你的API密钥（必填）
   - **Base URL**: API地址（例如 `https://api.openai.com/v1`）
   - **Model**: 模型名称（例如 `gpt-3.5-turbo`）
3. 点击 **"测试连接"** 验证配置
4. 点击 **"保存"**

### 步骤4: 处理视频生成摘要

1. 首先使用pyvideotrans的正常流程进行语音识别，生成SRT字幕文件
2. 点击 **"🎯 智能摘要"** 按钮
3. 选择刚才生成的SRT文件
4. 等待处理（1-2分钟）
5. 查看结果窗口：
   - 顶部显示整体摘要
   - 左侧显示段落列表
   - 右侧显示详细内容
6. 点击 **"导出Markdown"** 保存结果

---

## ⚠️ 如果按钮没有显示

### 可能原因及解决方法

#### 原因1: 虚拟环境未激活
确保激活了虚拟环境再运行 `python sp.py`

#### 原因2: 代码有语法错误
查看终端输出，是否有错误信息：
```bash
python sp.py 2>&1 | grep -i "error\|exception"
```

#### 原因3: 导入失败
测试导入HearSight模块：
```bash
cd pyvideotrans
python -c "from videotrans.hearsight import segment_merger; print('导入成功')"
python -c "from videotrans.ui.hearsight_config import HearSightConfigDialog; print('UI导入成功')"
```

#### 原因4: 初始化延迟
`_init_hearsight()` 在900毫秒后才执行，可能需要等待一下，或者重新启动程序。

---

## 🐛 调试方法

### 方法1: 查看控制台输出

运行程序时注意控制台输出：

```bash
python sp.py
```

查找关键信息：
- `加载HearSight配置失败:` - 配置加载问题
- `添加HearSight按钮失败:` - 按钮创建问题
- 任何 Python traceback 错误信息

### 方法2: 独立测试模块

```bash
cd pyvideotrans
python test_hearsight.py
```

选择测试项目：
- 选项3: 测试UI界面
- 这将单独测试UI组件，不依赖主窗口

### 方法3: 检查文件是否创建成功

```bash
cd pyvideotrans

# 检查hearsight模块
ls -la videotrans/hearsight/

# 应该看到：
# __init__.py
# chat_client.py
# segment_merger.py
# summarizer.py
# processor.py

# 检查UI文件
ls -la videotrans/ui/hearsight*.py

# 应该看到：
# hearsight_config.py
# hearsight_viewer.py
```

### 方法4: 强制重新初始化

如果按钮没显示，可以尝试在Python控制台手动初始化：

```python
# 在pyvideotrans运行时，如果有Python控制台访问权限
from videotrans.mainwin._main_win import MainWindow
# 获取主窗口实例
main_win = QApplication.instance().activeWindow()
# 手动初始化
main_win._init_hearsight()
```

---

## 📸 预期效果截图

### 工具栏按钮
启动后应该看到工具栏上有：
- 绿色的 "🎯 智能摘要" 按钮
- 齿轮图标 "⚙️" 配置按钮

### 配置对话框
点击 ⚙️ 后应该显示：
- LLM API 配置表单
- 段落合并参数
- 测试连接、保存、取消按钮

### 结果查看器
处理完成后显示：
- 顶部：摘要文本框
- 左侧：段落列表（可点击）
- 右侧：段落详细内容
- 底部：导出Markdown、关闭按钮

---

## ✨ 成功标志

如果看到以下情况，说明集成成功：

1. ✅ 程序启动无错误
2. ✅ 工具栏显示绿色按钮和齿轮按钮
3. ✅ 点击齿轮按钮能打开配置对话框
4. ✅ 点击智能摘要按钮能弹出文件选择对话框
5. ✅ 选择SRT文件后能显示进度条
6. ✅ 处理完成后能显示结果窗口

---

## 📞 问题反馈

如果遇到问题，请提供以下信息：

1. **错误信息**: 完整的控制台输出
2. **操作步骤**: 你执行了什么操作
3. **环境信息**:
   - Python版本: `python --version`
   - PySide6版本: `pip show PySide6`
   - 操作系统

---

## 🎉 下一步

集成成功后，你可以：

1. **尝试完整流程**: 识别视频 → 生成摘要 → 查看结果
2. **调整参数**: 在配置中调整段落合并策略
3. **优化提示词**: 编辑 `summarizer.py` 优化摘要质量
4. **添加快捷键**: 为HearSight功能添加键盘快捷键
5. **自动化集成**: 视频处理完成后自动生成摘要

---

**现在请启动pyvideotrans，查看工具栏是否显示HearSight按钮！** 🚀
