#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试URL解析
"""

from PySide6.QtCore import QUrl

def test_url_parsing():
    """测试QUrl解析自定义协议"""
    print("=" * 80)
    print("测试URL解析")
    print("=" * 80)
    
    test_cases = [
        "playvideo:///0.0",
        "playvideo:///19.064",
        "playvideo:///48.892",
        "playvideo:///123.456",
    ]
    
    for url_str in test_cases:
        print(f"\n测试URL: {url_str}")
        
        # 创建QUrl对象
        url = QUrl(url_str)
        
        print(f"  toString(): {url.toString()}")
        print(f"  scheme(): {url.scheme()}")
        print(f"  host(): {url.host()}")
        print(f"  path(): {url.path()}")
        print(f"  url(): {url.url()}")
        
        # 尝试提取时间（从路径）
        extracted = url.path().strip('/')
        print(f"  提取的时间字符串（从path）: '{extracted}'")
        
        try:
            time_value = float(extracted)
            print(f"  ✅ 转换成功: {time_value}")
        except Exception as e:
            print(f"  ❌ 转换失败: {e}")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == '__main__':
    test_url_parsing()

