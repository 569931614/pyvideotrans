#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置 pyvideotrans 的 Qdrant 导出功能

运行方式:
    python configure_qdrant.py
"""
import os
import sys
import json

# 添加 videotrans 到路径
sys.path.insert(0, os.path.dirname(__file__))

from videotrans.configure import config


def configure_qdrant():
    """配置 Qdrant 导出功能"""

    print("=" * 60)
    print("配置 pyvideotrans Qdrant 导出功能")
    print("=" * 60)

    # Qdrant 配置
    qdrant_config = {
        # 基础配置
        "qdrant_enabled": True,
        "qdrant_as_primary": False,
        "qdrant_url": "http://localhost:6333",
        "qdrant_api_key": "",
        "qdrant_export_summaries": True,

        # Embedding API 配置 (SiliconFlow)
        "qdrant_embedding_api_url": "https://api.siliconflow.cn/v1",
        "qdrant_embedding_api_key": "sk-yjmvqfzgdciokjvjmalmlunxrjjezbweklryihdmjmahsbjc",
        "qdrant_embedding_model": "BAAI/bge-large-zh-v1.5",

        # LLM API 配置 (SiliconFlow)
        "qdrant_llm_api_url": "https://api.siliconflow.cn/v1",
        "qdrant_llm_api_key": "sk-yjmvqfzgdciokjvjmalmlunxrjjezbweklryihdmjmahsbjc",
        "qdrant_llm_model": "deepseek-ai/DeepSeek-V3"
    }

    print("\n[1/3] 更新内存配置...")
    # 更新到 config 对象
    for key, value in qdrant_config.items():
        setattr(config, key, value)
        print(f"  [OK] {key} = {value if 'api_key' not in key else '***'}")

    print("\n[2/3] 读取现有 cfg.json...")
    cfg_path = os.path.join(os.path.dirname(__file__), 'videotrans', 'cfg.json')

    try:
        with open(cfg_path, 'r', encoding='utf-8') as f:
            cfg_data = json.load(f)
        print(f"  [OK] 读取成功: {len(cfg_data)} 个配置项")
    except Exception as e:
        print(f"  [ERROR] 读取失败: {e}")
        return False

    print("\n[3/3] 合并并保存 Qdrant 配置到 cfg.json...")
    # 合并配置
    cfg_data.update(qdrant_config)

    try:
        with open(cfg_path, 'w', encoding='utf-8') as f:
            json.dump(cfg_data, f, ensure_ascii=False)
        print(f"  [OK] 保存成功")
    except Exception as e:
        print(f"  [ERROR] 保存失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("[SUCCESS] 配置完成！")
    print("=" * 60)
    print("\n[配置摘要]")
    print(f"  - Qdrant 地址: {qdrant_config['qdrant_url']}")
    print(f"  - 启用摘要生成: {qdrant_config['qdrant_export_summaries']}")
    print(f"  - Embedding 模型: {qdrant_config['qdrant_embedding_model']}")
    print(f"  - LLM 模型: {qdrant_config['qdrant_llm_model']}")

    print("\n[重要提示]")
    print("  1. 如果 pyvideotrans 正在运行，请重启程序")
    print("  2. 翻译视频后会自动导出到 Qdrant")
    print("  3. 查看日志确认导出成功:")
    print("     [Qdrant Export] Step 1/5: Parsing SRT file...")
    print("     [Qdrant Export] Step 5/5: Uploading to Qdrant...")
    print("     [Qdrant Export] Successfully exported to Qdrant")

    return True


if __name__ == '__main__':
    success = configure_qdrant()
    sys.exit(0 if success else 1)
