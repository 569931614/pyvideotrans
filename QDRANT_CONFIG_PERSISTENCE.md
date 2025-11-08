# Qdrant 配置持久化问题解决方案

## 问题分析

pyvideotrans 会在运行时重写 cfg.json，覆盖手动添加的配置。

## ✅ 最终解决方案

**通过 GUI 保存配置**，这样配置会同时更新到内存和文件：

### 步骤

1. **启动 pyvideotrans**
   ```
   双击 "启动程序.bat"
   ```

2. **打开摘要配置**
   - 找到菜单中的"摘要配置"或"HearSight 配置"选项
   - 点击打开

3. **选择 Qdrant**
   - 向量存储类型：选择 **"Qdrant (推荐)"**

4. **填写配置**
   ```
   Qdrant URL: http://localhost:6333
   API Key: (留空)

   Embedding API URL: https://api.siliconflow.cn/v1
   Embedding API Key: sk-yjmvqfzgdciokjvjmalmlunxrjjezbweklryihdmjmahsbjc
   Embedding 模型: BAAI/bge-large-zh-v1.5

   LLM API:
   - API Key: sk-yjmvqfzgdciokjvjmalmlunxrjjezbweklryihdmjmahsbjc
   - Base URL: https://api.siliconflow.cn/v1
   - Model: deepseek-ai/DeepSeek-V3
   ```

5. **保存配置**
   - 点击"💾 保存配置"按钮
   - 这会同时更新：
     - `hearsight_config.json`
     - `cfg.json` 中的 Qdrant 配置
     - 内存中的 config 对象

6. **翻译视频**
   - 翻译任意视频
   - 观察日志应出现：
     ```
     [Qdrant Export] Step 1/5: Parsing SRT file...
     ...
     [Qdrant Export] ✓ Successfully exported to Qdrant
     ```

## 🔍 验证配置是否生效

### 检查配置文件
```bash
cd videotrans
python -c "import json; d=json.load(open('cfg.json', encoding='utf-8')); print('qdrant_enabled:', d.get('qdrant_enabled'))"
```

应显示：`qdrant_enabled: True`

### 检查 Qdrant 数据
```bash
curl http://localhost:6333/collections/video_chunks | python -c "import sys, json; print('Points:', json.load(sys.stdin)['result']['points_count'])"
```

翻译后应显示：`Points: > 0`

## ⚠️ 临时方案（如果 GUI 配置不可用）

运行配置脚本，然后**立即翻译**（不要关闭程序）：

```bash
# 在 pyvideotrans 运行时
python configure_qdrant.py

# 然后立即在 GUI 中翻译视频
# 不要关闭或重启程序
```

## 📝 配置会被重置的时机

pyvideotrans 在以下情况会重写 cfg.json：
1. 程序关闭时
2. 修改任何设置并保存时
3. 某些操作触发配置保存时

**解决方法**：通过 GUI 保存的配置会包含在 pyvideotrans 的配置管理中，不会丢失。

---

**关键**：必须通过 GUI 的摘要配置对话框保存，不能只手动编辑 cfg.json！
