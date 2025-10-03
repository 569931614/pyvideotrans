# HearSight 智能摘要功能测试指南

## 问题修复说明

### 问题描述
在HTML UI页面中勾选"智能摘要"选项后，视频处理完成但摘要库没有新增数据。

### 根本原因
`config.hearsight_config` 配置对象未在程序启动时加载，导致视频处理完成后无法生成摘要。

### 修复内容

#### 1. 修改 `videotrans/configure/_config_loader.py`
在配置加载器中添加了HearSight配置的自动加载：

```python
# 加载HearSight配置
hearsight_config = None
_hearsight_config_path = Path(ROOT_DIR) / 'hearsight_config.json'
if _hearsight_config_path.exists():
    try:
        hearsight_config = json.loads(_hearsight_config_path.read_text(encoding='utf-8'))
        logger.info(f"✅ HearSight配置加载成功")
    except Exception as e:
        logger.warning(f"⚠️ HearSight配置加载失败: {e}")
```

#### 2. 修改 `videotrans/mainwin/_main_win.py`
在MainWindow初始化时，将配置同步到全局config对象：

```python
def _init_hearsight(self):
    """初始化HearSight功能"""
    # ... 加载配置 ...
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.hearsight_config = json.load(f)
                # 同时保存到全局config对象，供trans_create.py使用
                config.hearsight_config = self.hearsight_config
                print(f"✅ HearSight配置加载成功")
        except Exception as e:
            print(f"加载HearSight配置失败: {e}")
```

#### 3. 增强 `videotrans/task/trans_create.py` 的日志
添加了详细的调试日志，方便追踪问题：

```python
# Debug: Log all params
_cfg.logger.info(f"🔍 HearSight Debug - enable_hearsight param: {_cfg.params.get('enable_hearsight', False)}")
_cfg.logger.info(f"🔍 HearSight Debug - all params keys: {list(_cfg.params.keys())}")

# Check if enable_hearsight is checked
if not _cfg.params.get('enable_hearsight', False):
    _cfg.logger.info("⏭️ HearSight is not enabled, skipping summary generation")
    return

_cfg.logger.info("✅ HearSight is enabled, starting summary generation...")
```

## 测试步骤

### 前置条件

1. **确认配置文件存在**
   ```bash
   # 检查hearsight_config.json是否存在
   ls hearsight_config.json
   ```

2. **验证配置内容**
   ```json
   {
     "llm": {
       "api_key": "your-api-key",
       "base_url": "https://api.gptgod.online/v1/",
       "model": "gpt-4o-mini",
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

3. **运行诊断脚本**
   ```bash
   python diagnose_hearsight.py
   ```
   
   确认输出包含：
   - ✅ 配置文件存在
   - ✅ API Key已配置
   - ✅ 向量数据库初始化成功
   - ✅ 智能摘要功能已启用
   - ✅ config.hearsight_config 已设置

### 测试流程

#### 方法1: 使用HTML UI测试

1. **启动程序**
   ```bash
   python sp.py
   ```

2. **切换到HTML UI**
   - 点击工具栏中的"HTML UI"按钮

3. **配置处理参数**
   - 选择视频文件
   - 选择保存目录
   - 设置翻译渠道和语言
   - 设置语音识别类型
   - **重要：勾选"智能摘要"选项**

4. **开始处理**
   - 点击"开始处理"按钮
   - 等待视频处理完成

5. **查看日志**
   打开 `logs/YYYYMMDD.log` 文件，搜索以下关键词：
   
   ```
   HearSight
   ```
   
   应该看到类似的日志：
   ```
   ✅ HearSight is enabled, starting summary generation...
   ✅ HearSight config loaded: ['llm', 'merge']
   ✅ HearSight API key configured
   🔍 Looking for SRT files...
   ✅ Found target SRT: xxx.srt
   🚀 Starting HearSight summary generation for: xxx.srt
   Merged X paragraphs
   Generated overall summary: [主题]
   Generated X paragraph summaries
   ✅ Successfully stored HearSight summary in vector database
   ```

6. **验证摘要库**
   ```bash
   python diagnose_hearsight.py
   ```
   
   应该看到：
   ```
   ✅ 数据库中有 1 个视频
   ```

7. **查看摘要**
   - 在主界面点击"📚"按钮打开摘要管理器
   - 应该能看到刚处理的视频及其摘要

#### 方法2: 使用命令行测试

```bash
# 运行完整的集成测试
python test_hearsight_integration.py
```

### 常见问题排查

#### 问题1: 日志显示 "HearSight is not enabled"

**原因**: HTML UI中未勾选"智能摘要"选项

**解决**: 
1. 在HTML UI中找到"智能摘要"复选框
2. 确保勾选该选项
3. 重新开始处理

#### 问题2: 日志显示 "HearSight config not found"

**原因**: 配置文件未加载或不存在

**解决**:
1. 确认 `hearsight_config.json` 文件存在于项目根目录
2. 运行诊断脚本检查配置
3. 重启程序

#### 问题3: 日志显示 "No SRT file found"

**原因**: 视频处理未生成SRT字幕文件

**解决**:
1. 确认语音识别设置正确
2. 检查视频是否有音频轨道
3. 查看日志中的语音识别部分是否有错误

#### 问题4: 日志显示 "HearSight API key not configured"

**原因**: API密钥未配置或配置错误

**解决**:
1. 检查 `hearsight_config.json` 中的 `llm.api_key` 字段
2. 确保API密钥有效
3. 重启程序

#### 问题5: 摘要生成失败

**原因**: API调用失败或网络问题

**解决**:
1. 检查网络连接
2. 验证API密钥是否有效
3. 检查API服务是否可用
4. 查看日志中的详细错误信息

### 验证成功的标志

1. **日志中包含**:
   ```
   ✅ Successfully stored HearSight summary in vector database
   ```

2. **诊断脚本显示**:
   ```
   ✅ 数据库中有 X 个视频 (X > 0)
   ```

3. **摘要管理器中**:
   - 能看到处理的视频列表
   - 能查看视频的整体摘要
   - 能查看各段落的摘要

## 性能说明

- **段落合并**: 通常在1秒内完成
- **整体摘要生成**: 根据视频长度，通常5-30秒
- **段落摘要生成**: 每个段落约1-3秒，并行处理
- **向量存储**: 通常在1秒内完成

总体来说，一个10分钟的视频，生成完整摘要大约需要30-60秒。

## 注意事项

1. **后台处理**: 摘要生成在后台线程中进行，不会阻塞视频处理
2. **失败不影响主流程**: 即使摘要生成失败，视频处理仍会正常完成
3. **日志记录**: 所有操作都有详细的日志记录，便于调试
4. **配置热加载**: 修改配置文件后需要重启程序才能生效

## 下一步

如果测试成功，可以：

1. 处理更多视频，建立摘要库
2. 使用摘要管理器查看和导出摘要
3. 使用语义搜索功能查找相关内容
4. 根据需要调整配置参数（段落长度、摘要风格等）

