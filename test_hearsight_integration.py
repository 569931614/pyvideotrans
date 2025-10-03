#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试HearSight集成功能
"""

import json
import os
from pathlib import Path

def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("测试1: 配置文件加载")
    print("=" * 60)
    
    config_path = 'hearsight_config.json'
    
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        return False
    
    print(f"✅ 配置文件存在: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✅ 配置文件加载成功")
        print(f"   配置项: {list(config.keys())}")
        
        # 检查LLM配置
        llm_cfg = config.get('llm', {})
        if not llm_cfg:
            print("❌ 缺少LLM配置")
            return False
        
        print(f"✅ LLM配置存在")
        print(f"   API Key: {'已配置' if llm_cfg.get('api_key') else '未配置'}")
        print(f"   Base URL: {llm_cfg.get('base_url', 'N/A')}")
        print(f"   Model: {llm_cfg.get('model', 'N/A')}")
        
        # 检查Merge配置
        merge_cfg = config.get('merge', {})
        if merge_cfg:
            print(f"✅ Merge配置存在")
            print(f"   max_gap: {merge_cfg.get('max_gap', 'N/A')}")
            print(f"   max_duration: {merge_cfg.get('max_duration', 'N/A')}")
            print(f"   max_chars: {merge_cfg.get('max_chars', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return False


def test_vector_db():
    """测试向量数据库"""
    print("\n" + "=" * 60)
    print("测试2: 向量数据库")
    print("=" * 60)
    
    try:
        from videotrans.hearsight.vector_store import get_vector_store
        
        vector_store = get_vector_store()
        print(f"✅ 向量数据库初始化成功")
        
        # 获取所有视频
        videos = vector_store.list_videos()
        print(f"✅ 当前数据库中有 {len(videos)} 个视频")
        
        if videos:
            print("\n视频列表:")
            for i, video in enumerate(videos[:5], 1):  # 只显示前5个
                print(f"   {i}. {video.get('basename', 'N/A')}")
                print(f"      主题: {video.get('topic', 'N/A')}")
                print(f"      段落数: {video.get('paragraph_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 向量数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_params_config():
    """测试params配置"""
    print("\n" + "=" * 60)
    print("测试3: Params配置")
    print("=" * 60)
    
    try:
        from videotrans.configure import config
        
        # 检查enable_hearsight参数
        enable_hearsight = config.params.get('enable_hearsight', False)
        print(f"enable_hearsight: {enable_hearsight}")
        
        # 检查hearsight_config
        hearsight_config = getattr(config, 'hearsight_config', None)
        if hearsight_config:
            print(f"✅ config.hearsight_config 已设置")
            print(f"   配置项: {list(hearsight_config.keys())}")
        else:
            print(f"⚠️ config.hearsight_config 未设置")
            print(f"   这可能是因为主窗口还未初始化")
        
        return True
        
    except Exception as e:
        print(f"❌ Params配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_srt_processing():
    """测试SRT处理"""
    print("\n" + "=" * 60)
    print("测试4: SRT处理功能")
    print("=" * 60)
    
    # 查找测试SRT文件
    test_srt = None
    possible_paths = [
        'tmp',
        'output',
        '.'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            for file in Path(path).rglob('*.srt'):
                test_srt = str(file)
                break
        if test_srt:
            break
    
    if not test_srt:
        print("⚠️ 未找到测试SRT文件，跳过此测试")
        return True
    
    print(f"✅ 找到测试SRT文件: {test_srt}")
    
    try:
        from videotrans.hearsight.segment_merger import merge_srt_to_paragraphs
        
        paragraphs = merge_srt_to_paragraphs(
            srt_path=test_srt,
            max_gap=2.0,
            max_duration=30.0,
            max_chars=200
        )
        
        print(f"✅ SRT处理成功，生成 {len(paragraphs)} 个段落")
        
        if paragraphs:
            print(f"\n第一个段落示例:")
            para = paragraphs[0]
            print(f"   时间: {para.get('start_time', 0):.2f}s - {para.get('end_time', 0):.2f}s")
            print(f"   文本: {para.get('text', '')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ SRT处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("HearSight集成功能测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 运行测试
    results.append(("配置加载", test_config_loading()))
    results.append(("向量数据库", test_vector_db()))
    results.append(("Params配置", test_params_config()))
    results.append(("SRT处理", test_srt_processing()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️ 部分测试失败，请检查上述错误信息")


if __name__ == '__main__':
    main()

