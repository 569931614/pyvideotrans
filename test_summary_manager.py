#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试摘要管理器是否能正常打开
"""

import sys
from PySide6.QtWidgets import QApplication

def test_summary_manager():
    """测试摘要管理器"""
    print("=" * 80)
    print("测试摘要管理器")
    print("=" * 80)
    
    try:
        from videotrans.ui.summary_manager import SummaryManagerDialog
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 创建对话框
        dialog = SummaryManagerDialog()
        print("✅ 摘要管理器创建成功")
        
        # 显示对话框
        dialog.show()
        print("✅ 摘要管理器显示成功")
        
        # 不执行事件循环，只是测试能否创建
        dialog.close()
        
        print("\n" + "=" * 80)
        print("🎉 测试通过！摘要管理器可以正常打开")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_summary_manager()
    sys.exit(0 if success else 1)

