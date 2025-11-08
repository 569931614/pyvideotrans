# 火山引擎 TTS 配置指南

## 概述

火山引擎TTS是字节跳动提供的文本转语音服务,音色丰富,音质优秀。

## 配置步骤

### 1. 获取火山引擎 TTS 凭证

访问火山引擎控制台:
- **语音技术**: https://console.volcengine.com/speech/app
- **文档**: https://www.volcengine.com/docs/6561/79816

#### 需要获取的参数:

1. **App ID** (应用ID)
   - 在"语音合成" → "应用管理"中创建应用
   - 复制应用的 `App ID`

2. **Access Token** (访问令牌)
   - 在应用详情中找到"访问令牌"
   - 或者使用 API 密钥生成令牌
   - 文档: https://www.volcengine.com/docs/6561/80426

3. **Cluster ID** (集群ID)
   - 通常为区域代码,如: `volcengine_tts`
   - 在应用配置中查看

### 2. 在 pyvideotrans 中配置

#### 方法1: 通过 GUI 配置

1. 启动程序:
   ```bash
   cd pyvideotrans
   python sp.py
   ```

2. 打开配置:
   - 菜单: **设置** → **配音服务** → **字节火山TTS**

3. 填写参数:
   - **App ID**: 您的应用ID
   - **Access Token**: 您的访问令牌
   - **Cluster ID**: 集群ID

4. 点击 **"测试"** 验证配置

5. 点击 **"保存"**

#### 方法2: 直接编辑配置文件

编辑 `videotrans/params.json`:

```json
{
  "volcenginetts_appid": "您的App ID",
  "volcenginetts_access": "您的Access Token",
  "volcenginetts_cluster": "您的Cluster ID"
}
```

### 3. 选择音色

火山引擎提供丰富的中文音色,参考官方文档:
- **音色列表**: https://www.volcengine.com/docs/6561/1257544

#### 常用中文音色示例:

**通用音色**:
- `BV700_V2_streaming` - 通用女声
- `BV701_V2_streaming` - 通用男声
- `BV406_streaming` - 灿灿(女声)
- `BV407_streaming` - 擎苍(男声)

**情感音色**:
- `BV001_streaming` - 温柔女声
- `BV002_streaming` - 开朗男声
- `BV158_streaming` - 知性女声
- `BV033_streaming` - 磁性男声

**方言音色**:
- 东北话、粤语、上海话、西安话、成都话等

**更多音色**: 查看完整列表 https://www.volcengine.com/docs/6561/1257544

### 4. 使用火山TTS配音

1. 在主界面选择视频文件

2. 配置翻译设置:
   - 源语言: 选择视频原语言
   - 目标语言: 选择翻译目标语言

3. **配音设置**:
   - **TTS类型**: 选择 **"字节火山TTS"**
   - **配音角色**: 从下拉列表选择音色
     - 例如: `BV700_V2_streaming` (通用女声)

4. 开始处理

## 音色选择建议

### 根据场景选择:

| 场景 | 推荐音色 | 音色代码 |
|------|---------|---------|
| 新闻播报 | 知性女声 | BV158_streaming |
| 教育培训 | 灿灿(女) | BV406_streaming |
| 商业广告 | 擎苍(男) | BV407_streaming |
| 有声读物 | 温柔女声 | BV001_streaming |
| 解说视频 | 磁性男声 | BV033_streaming |

### 方言音色:

如果原视频是方言,可以选择对应方言音色:
- **东北话**: 选择东北方言音色
- **粤语**: 选择粤语音色
- **其他**: 查看完整列表选择

## 费用说明

火山引擎TTS是**付费服务**:
- **免费额度**: 新用户通常有免费试用额度
- **计费方式**: 按字符数计费
- **价格**: 约 ¥0.1-0.3/千字符 (根据音色不同)
- **详情**: https://www.volcengine.com/pricing/tts

建议:
1. 先使用免费额度测试
2. 小额充值(¥10-50)用于日常使用
3. 监控用量,避免超支

## 与 Edge TTS 对比

| 特性 | Edge TTS | 火山引擎 TTS |
|------|----------|-------------|
| **价格** | 完全免费 | 按量付费 |
| **稳定性** | 偶尔失效 | 非常稳定 |
| **音色质量** | 优秀 | 优秀 |
| **中文音色** | 丰富 | 非常丰富 |
| **方言支持** | 有限 | 丰富 |
| **配置难度** | 简单 | 需要注册 |
| **推荐场景** | 个人免费使用 | 商业/稳定需求 |

## 故障排查

### 1. 配音失败: "无效的请求"
**原因**:
- App ID/Access Token/Cluster ID 错误
- 音色需要单独购买

**解决**:
- 检查配置参数是否正确
- 确认所选音色在您的账号下可用
- 查看火山引擎控制台确认权限

### 2. 配音失败: "并发超限"
**原因**: 同时请求过多

**解决**:
- 降低并发数 (设置中调整)
- 联系火山引擎提升配额

### 3. 配音失败: "文本长度超限"
**原因**: 单次请求文本过长

**解决**:
- 自动处理,如仍失败请分段

## OSS + 火山引擎集成

好消息!您现在已经配置了:
- ✅ **阿里云 OSS** - 视频存储
- ✅ **火山向量库** - 摘要存储
- ✅ **火山引擎 TTS** - 语音合成

**完整工作流**:
```
视频处理
    ↓
火山TTS配音
    ↓
上传到阿里云OSS
    ↓
HearSight生成摘要
    ↓
存储到火山向量库
```

**全部使用您已有的火山引擎账号!**

## 测试配置

创建测试脚本 `test_volcengine_tts.py`:

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试火山引擎TTS配置"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from videotrans.configure import config

# 检查配置
appid = config.params.get('volcenginetts_appid', '')
access = config.params.get('volcenginetts_access', '')
cluster = config.params.get('volcenginetts_cluster', '')

print("=" * 60)
print("火山引擎 TTS 配置检查")
print("=" * 60)
print(f"App ID: {'已配置' if appid else '未配置'}")
print(f"Access Token: {'已配置' if access else '未配置'}")
print(f"Cluster ID: {'已配置' if cluster else '未配置'}")

if appid and access and cluster:
    print("\n✅ 配置完整,可以使用火山引擎TTS")
else:
    print("\n❌ 配置不完整,请补充缺失项")
    print("\n配置方法:")
    print("1. GUI: 设置 → 配音服务 → 字节火山TTS")
    print("2. 手动: 编辑 videotrans/params.json")
```

运行:
```bash
cd pyvideotrans
python test_volcengine_tts.py
```

## 相关链接

- **火山引擎控制台**: https://console.volcengine.com/speech/app
- **API 文档**: https://www.volcengine.com/docs/6561/79816
- **音色列表**: https://www.volcengine.com/docs/6561/1257544
- **计费说明**: https://www.volcengine.com/pricing/tts
- **接入指南**: https://www.volcengine.com/docs/6561/80426

---

**配置完成后,您就可以使用火山引擎TTS进行高质量配音了!**
