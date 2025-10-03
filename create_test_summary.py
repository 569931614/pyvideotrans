#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建测试摘要数据
"""

def create_test_summary():
    """创建一个测试摘要"""
    print("=" * 80)
    print("创建测试摘要数据")
    print("=" * 80)
    
    try:
        from videotrans.hearsight.vector_store import get_vector_store
        
        vector_store = get_vector_store()
        print("✅ 向量数据库初始化成功")
        
        # 创建测试数据
        test_video_path = "test_video.mp4"
        
        test_summary = {
            "topic": "测试视频主题",
            "summary": "这是一个测试视频的摘要内容，用于验证ChromaDB查询修复。",
            "paragraph_count": 3,
            "total_duration": 180.0
        }
        
        test_paragraphs = [
            {
                "text": "第一段内容：介绍视频的背景和目的。",
                "summary": "视频介绍",
                "start_time": 0.0,
                "end_time": 60.0
            },
            {
                "text": "第二段内容：详细讲解主要内容和关键点。",
                "summary": "主要内容讲解",
                "start_time": 60.0,
                "end_time": 120.0
            },
            {
                "text": "第三段内容：总结和展望未来发展方向。",
                "summary": "总结与展望",
                "start_time": 120.0,
                "end_time": 180.0
            }
        ]
        
        test_metadata = {
            "basename": "test_video",
            "source_language": "zh",
            "target_language": "en",
            "app_mode": "test"
        }
        
        print("\n正在存储测试摘要...")
        success = vector_store.store_summary(
            video_path=test_video_path,
            summary=test_summary,
            paragraphs=test_paragraphs,
            metadata=test_metadata
        )
        
        if success:
            print("\n✅ 测试摘要创建成功！")
            print(f"   视频路径: {test_video_path}")
            print(f"   主题: {test_summary['topic']}")
            print(f"   段落数: {len(test_paragraphs)}")
            
            # 验证存储
            print("\n验证存储...")
            summary_data = vector_store.get_video_summary(test_video_path)
            
            if summary_data:
                print("✅ 验证成功！可以正确读取摘要")
                print(f"   读取到的主题: {summary_data['overall']['metadata'].get('topic')}")
                print(f"   读取到的段落数: {len(summary_data['paragraphs'])}")
            else:
                print("❌ 验证失败：无法读取刚存储的摘要")
                return False
            
            return True
        else:
            print("❌ 测试摘要创建失败")
            return False
            
    except Exception as e:
        print(f"❌ 创建测试摘要失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("ChromaDB修复验证 - 创建测试数据")
    print("=" * 80 + "\n")
    
    success = create_test_summary()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ 测试数据创建成功！")
        print("=" * 80)
        print("\n现在可以运行以下命令测试查询功能:")
        print("   python test_chromadb_fix.py")
    else:
        print("\n" + "=" * 80)
        print("❌ 测试数据创建失败")
        print("=" * 80)


if __name__ == '__main__':
    main()

