#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试内嵌视频播放器
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_video_player():
    """测试视频播放器"""
    print("=" * 80)
    print("测试内嵌视频播放器")
    print("=" * 80)
    
    app = QApplication(sys.argv)
    
    try:
        from videotrans.ui.video_player import VideoPlayerDialog
        print("✅ 成功导入VideoPlayerDialog")
        
        # 创建一个测试视频路径（实际使用时需要真实的视频文件）
        test_video = r"F:\智能体定制\20250904translateVideo\pyvideotrans\tmp\test_video.mp4"
        
        if not os.path.exists(test_video):
            QMessageBox.information(
                None,
                "测试说明",
                f"测试视频不存在：\n{test_video}\n\n"
                "请将一个视频文件放到该路径，或修改test_video_player.py中的路径。\n\n"
                "如果您有真实的视频文件，可以直接在摘要管理器中测试播放功能。"
            )
            print(f"⚠️ 测试视频不存在: {test_video}")
            print("💡 提示: 请在摘要管理器中使用真实视频测试")
            return
        
        # 创建播放器（从10秒开始播放）
        player = VideoPlayerDialog(test_video, start_time=10.0)
        print("✅ 成功创建播放器")
        
        player.show()
        print("✅ 播放器显示成功")
        
        print("\n" + "=" * 80)
        print("播放器功能说明:")
        print("- 空格键: 播放/暂停")
        print("- F键: 全屏/退出全屏")
        print("- ESC键: 退出全屏")
        print("- 左箭头: 后退5秒")
        print("- 右箭头: 前进5秒")
        print("- 上箭头: 增加音量")
        print("- 下箭头: 减少音量")
        print("=" * 80)
        
        sys.exit(app.exec())
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ 测试失败: {e}")
        print(f"\n详细错误:\n{error_detail}")
        
        QMessageBox.critical(
            None,
            "测试失败",
            f"无法创建视频播放器：\n{str(e)}\n\n详细信息:\n{error_detail}"
        )


if __name__ == '__main__':
    test_video_player()

