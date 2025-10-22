"""
监控打包进度
"""
import os
import time
from pathlib import Path

def get_dir_size(path):
    """获取目录大小（MB）"""
    if not os.path.exists(path):
        return 0
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    except:
        pass
    return total / (1024 * 1024)

print("监控打包进度...")
print("=" * 60)

for i in range(120):  # 监控 10 分钟
    build_exists = os.path.exists("build")
    dist_exists = os.path.exists("dist")
    exe_exists = os.path.exists("dist/BDvideoTrans/BDvideoTrans.exe")
    
    status = []
    if build_exists:
        size = get_dir_size("build")
        status.append(f"build: {size:.1f}MB")
    if dist_exists:
        size = get_dir_size("dist")
        status.append(f"dist: {size:.1f}MB")
    if exe_exists:
        exe_size = os.path.getsize("dist/BDvideoTrans/BDvideoTrans.exe") / (1024 * 1024)
        status.append(f"EXE: {exe_size:.1f}MB")
        print(f"\n✅ 打包完成！EXE 文件已生成")
        break
    
    if status:
        print(f"[{i*5}s] {' | '.join(status)}")
    else:
        print(f"[{i*5}s] 等待打包开始...")
    
    time.sleep(5)
else:
    print("\n⏰ 监控超时")

print("=" * 60)

