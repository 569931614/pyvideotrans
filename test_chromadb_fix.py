#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试ChromaDB查询修复
"""

import os
import sys

def test_chromadb_queries():
    """测试ChromaDB的where查询"""
    print("=" * 80)
    print("测试ChromaDB查询修复")
    print("=" * 80)
    
    try:
        from videotrans.hearsight.vector_store import get_vector_store
        
        vector_store = get_vector_store()
        print("✅ 向量数据库初始化成功")
        
        # 测试1: 列出所有视频
        print("\n测试1: 列出所有视频")
        videos = vector_store.list_all_videos()
        print(f"✅ 找到 {len(videos)} 个视频")
        
        if not videos:
            print("⚠️ 数据库为空，无法测试查询功能")
            print("   请先处理一个视频并生成摘要")
            return False
        
        # 使用第一个视频进行测试
        test_video = videos[0]
        video_path = test_video['video_path']
        video_id = test_video['video_id']
        
        print(f"\n使用测试视频: {os.path.basename(video_path)}")
        print(f"   Video ID: {video_id}")
        print(f"   主题: {test_video.get('topic', 'N/A')}")
        
        # 测试2: 获取视频摘要（包含多条件查询）
        print("\n测试2: 获取视频摘要（测试多条件where查询）")
        try:
            summary_data = vector_store.get_video_summary(video_path)
            
            if summary_data:
                print("✅ 成功获取视频摘要")
                print(f"   整体摘要: {summary_data['overall']['metadata'].get('topic', 'N/A')}")
                print(f"   段落数量: {len(summary_data['paragraphs'])}")
                
                if summary_data['paragraphs']:
                    para = summary_data['paragraphs'][0]
                    print(f"   第一个段落: {para['metadata'].get('start_time', 0):.2f}s - {para['metadata'].get('end_time', 0):.2f}s")
            else:
                print("❌ 获取摘要失败：返回None")
                return False
                
        except Exception as e:
            print(f"❌ 获取摘要失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 测试3: 搜索功能（测试单条件和多条件）
        print("\n测试3: 搜索功能")
        
        # 3.1 无过滤条件的搜索
        print("   3.1 无过滤条件的搜索")
        try:
            results = vector_store.search("主题", n_results=3)
            print(f"   ✅ 找到 {len(results)} 个结果")
        except Exception as e:
            print(f"   ❌ 搜索失败: {e}")
            return False
        
        # 3.2 单条件搜索（只指定video_id）
        print("   3.2 单条件搜索（video_id）")
        try:
            results = vector_store.search("内容", n_results=3, video_id=video_id)
            print(f"   ✅ 找到 {len(results)} 个结果")
        except Exception as e:
            print(f"   ❌ 搜索失败: {e}")
            return False
        
        # 3.3 单条件搜索（只指定type）
        print("   3.3 单条件搜索（type）")
        try:
            results = vector_store.search("段落", n_results=3, filter_type="paragraph")
            print(f"   ✅ 找到 {len(results)} 个结果")
        except Exception as e:
            print(f"   ❌ 搜索失败: {e}")
            return False
        
        # 3.4 多条件搜索（video_id + type）
        print("   3.4 多条件搜索（video_id + type）")
        try:
            results = vector_store.search("内容", n_results=3, video_id=video_id, filter_type="paragraph")
            print(f"   ✅ 找到 {len(results)} 个结果")
        except Exception as e:
            print(f"   ❌ 搜索失败: {e}")
            return False
        
        print("\n" + "=" * 80)
        print("🎉 所有测试通过！")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行测试"""
    print("\n" + "=" * 80)
    print("ChromaDB查询修复验证")
    print("=" * 80 + "\n")
    
    success = test_chromadb_queries()
    
    if success:
        print("\n✅ 修复验证成功！")
        print("\n修复内容:")
        print("1. 修复了get_video_summary中的多条件where查询")
        print("2. 修复了search方法中的多条件where查询")
        print("3. 移除了QSS中不支持的box-shadow属性")
    else:
        print("\n⚠️ 测试未完全通过")
        print("\n可能的原因:")
        print("1. 数据库为空，需要先处理视频生成摘要")
        print("2. ChromaDB版本不兼容")
        print("3. 其他未知错误，请查看上述错误信息")


if __name__ == '__main__':
    main()

