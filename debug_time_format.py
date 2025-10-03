#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试时间格式问题
"""

def debug_time_format():
    """检查数据库中的时间格式"""
    print("=" * 80)
    print("调试时间格式")
    print("=" * 80)
    
    try:
        from videotrans.hearsight.vector_store import get_vector_store
        
        vector_store = get_vector_store()
        print("✅ 向量数据库初始化成功\n")
        
        # 获取所有视频
        videos = vector_store.list_all_videos()
        
        if not videos:
            print("⚠️ 数据库为空")
            return
        
        print(f"找到 {len(videos)} 个视频\n")
        
        # 检查第一个视频
        video = videos[0]
        video_path = video['video_path']
        
        print(f"检查视频: {video_path}")
        print(f"视频ID: {video['video_id']}\n")
        
        # 获取摘要数据
        summary_data = vector_store.get_video_summary(video_path)
        
        if not summary_data:
            print("❌ 无法获取摘要数据")
            return
        
        print(f"段落数量: {len(summary_data['paragraphs'])}\n")
        
        # 检查前3个段落的时间格式
        for i, para in enumerate(summary_data['paragraphs'][:3], 1):
            print(f"段落 {i}:")
            print(f"  metadata keys: {list(para['metadata'].keys())}")
            
            meta = para['metadata']
            start = meta.get('start_time', 0)
            end = meta.get('end_time', 0)
            
            print(f"  start_time: {start} (type: {type(start).__name__})")
            print(f"  end_time: {end} (type: {type(end).__name__})")
            
            # 测试转换
            try:
                start_float = float(start)
                print(f"  ✅ start转换为float: {start_float}")
            except Exception as e:
                print(f"  ❌ start转换失败: {e}")
            
            try:
                end_float = float(end)
                print(f"  ✅ end转换为float: {end_float}")
            except Exception as e:
                print(f"  ❌ end转换失败: {e}")
            
            # 测试生成链接
            time_link = f"playvideo://{start}"
            print(f"  生成的链接: {time_link}")
            
            # 测试解析链接
            time_str = time_link.replace("playvideo://", "")
            print(f"  解析的时间字符串: '{time_str}'")
            
            try:
                parsed_time = float(time_str)
                print(f"  ✅ 解析成功: {parsed_time}")
            except Exception as e:
                print(f"  ❌ 解析失败: {e}")
            
            print()
        
        print("=" * 80)
        print("调试完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    debug_time_format()

