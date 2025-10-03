#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
诊断HearSight功能问题
"""

import json
import os
import sys

def diagnose():
    """诊断HearSight功能"""
    print("=" * 80)
    print("HearSight 功能诊断")
    print("=" * 80)
    
    # 1. 检查配置文件
    print("\n1️⃣ 检查配置文件...")
    config_path = 'hearsight_config.json'
    if os.path.exists(config_path):
        print(f"   ✅ 配置文件存在: {config_path}")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"   ✅ 配置加载成功")
            
            llm_cfg = config.get('llm', {})
            if llm_cfg.get('api_key'):
                print(f"   ✅ API Key已配置")
                print(f"   ✅ Base URL: {llm_cfg.get('base_url')}")
                print(f"   ✅ Model: {llm_cfg.get('model')}")
            else:
                print(f"   ❌ API Key未配置")
                return
        except Exception as e:
            print(f"   ❌ 配置加载失败: {e}")
            return
    else:
        print(f"   ❌ 配置文件不存在: {config_path}")
        return
    
    # 2. 检查向量数据库
    print("\n2️⃣ 检查向量数据库...")
    try:
        from videotrans.hearsight.vector_store import get_vector_store
        vector_store = get_vector_store()
        print(f"   ✅ 向量数据库初始化成功")
        
        videos = vector_store.list_all_videos()
        print(f"   ✅ 数据库中有 {len(videos)} 个视频")
        
        if videos:
            print(f"\n   最近的视频:")
            for i, video in enumerate(videos[-3:], 1):
                print(f"      {i}. {os.path.basename(video.get('video_path', 'N/A'))}")
                print(f"         主题: {video.get('topic', 'N/A')}")
                print(f"         段落数: {video.get('paragraph_count', 0)}")
        else:
            print(f"   ⚠️ 数据库为空，还没有存储任何视频摘要")
            
    except Exception as e:
        print(f"   ❌ 向量数据库检查失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 检查params配置
    print("\n3️⃣ 检查运行时配置...")
    try:
        from videotrans.configure import config as cfg
        
        enable_hearsight = cfg.params.get('enable_hearsight', False)
        print(f"   enable_hearsight: {enable_hearsight}")
        
        if enable_hearsight:
            print(f"   ✅ 智能摘要功能已启用")
        else:
            print(f"   ⚠️ 智能摘要功能未启用")
            print(f"   提示: 请在HTML UI中勾选'智能摘要'选项")
        
        hearsight_config = getattr(cfg, 'hearsight_config', None)
        if hearsight_config:
            print(f"   ✅ config.hearsight_config 已设置")
        else:
            print(f"   ⚠️ config.hearsight_config 未设置")
            print(f"   提示: 这个配置会在主窗口初始化时加载")
            
    except Exception as e:
        print(f"   ❌ 配置检查失败: {e}")
    
    # 4. 检查日志文件
    print("\n4️⃣ 检查最近的日志...")
    try:
        import datetime
        from pathlib import Path
        
        logs_dir = Path('logs')
        if logs_dir.exists():
            # 获取今天的日志文件
            today = datetime.datetime.now().strftime('%Y%m%d')
            log_file = logs_dir / f'{today}.log'
            
            if log_file.exists():
                print(f"   ✅ 找到日志文件: {log_file}")
                
                # 读取最后100行
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # 查找HearSight相关的日志
                hearsight_logs = [line for line in lines if 'hearsight' in line.lower() or 'HearSight' in line]
                
                if hearsight_logs:
                    print(f"   ✅ 找到 {len(hearsight_logs)} 条HearSight相关日志")
                    print(f"\n   最近的HearSight日志:")
                    for log in hearsight_logs[-5:]:
                        print(f"      {log.strip()}")
                else:
                    print(f"   ⚠️ 未找到HearSight相关日志")
                    print(f"   提示: 可能还没有处理过视频，或者功能未被触发")
            else:
                print(f"   ⚠️ 今天的日志文件不存在: {log_file}")
        else:
            print(f"   ⚠️ 日志目录不存在: {logs_dir}")
            
    except Exception as e:
        print(f"   ❌ 日志检查失败: {e}")
    
    # 5. 提供建议
    print("\n" + "=" * 80)
    print("💡 诊断建议")
    print("=" * 80)
    
    print("""
如果视频处理完成后摘要库没有新增数据，请检查：

1. ✅ 确认在HTML UI中勾选了"智能摘要"选项
2. ✅ 确认hearsight_config.json配置正确（API Key等）
3. ✅ 查看日志文件中是否有HearSight相关的错误信息
4. ✅ 确认视频处理完成后生成了SRT字幕文件
5. ✅ 检查网络连接，确保可以访问LLM API

调试步骤：
1. 处理一个视频
2. 查看logs目录下今天的日志文件
3. 搜索"HearSight"关键词，查看详细的执行日志
4. 如果看到"enable_hearsight: False"，说明选项未勾选
5. 如果看到"HearSight config not found"，说明配置未加载
6. 如果看到"No SRT file found"，说明字幕文件未生成

常见问题：
- 如果enable_hearsight一直是False，检查HTML UI的JavaScript是否正确发送参数
- 如果config.hearsight_config未设置，确保主窗口已经初始化
- 如果API调用失败，检查API Key和网络连接
    """)
    
    print("\n" + "=" * 80)
    print("诊断完成")
    print("=" * 80)


if __name__ == '__main__':
    diagnose()

