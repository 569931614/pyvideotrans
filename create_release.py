"""
创建发布包脚本
将打包好的 BDvideoTrans 压缩成 zip 文件以便分发
"""

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parent.absolute()
DIST_DIR = ROOT_DIR / "dist" / "BDvideoTrans"
OUTPUT_DIR = ROOT_DIR / "release"

def create_zip():
    """创建 zip 压缩包"""
    if not DIST_DIR.exists():
        print(f"× 错误: 找不到打包目录 {DIST_DIR}")
        print("请先运行 build_exe.py 进行打包")
        return False
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # 生成文件名（包含日期）
    date_str = datetime.now().strftime("%Y%m%d")
    zip_filename = f"BDvideoTrans_v3.80_{date_str}.zip"
    zip_path = OUTPUT_DIR / zip_filename
    
    print(f"\n正在创建压缩包: {zip_filename}")
    print("这可能需要几分钟时间...\n")
    
    # 创建 zip 文件
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        total_files = 0
        for root, dirs, files in os.walk(DIST_DIR):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(DIST_DIR.parent)
                zipf.write(file_path, arcname)
                total_files += 1
                if total_files % 100 == 0:
                    print(f"  已压缩 {total_files} 个文件...")
    
    # 获取压缩包大小
    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    
    print(f"\n✓ 压缩完成！")
    print(f"  文件: {zip_path}")
    print(f"  大小: {zip_size_mb:.2f} MB")
    print(f"  包含文件数: {total_files}")
    
    return True

def create_readme():
    """创建发布说明"""
    readme_content = """# BDvideoTrans v3.80 发布包

## 下载说明

本压缩包包含 BDvideoTrans v3.80 的完整可执行版本。

## 安装步骤

1. 解压缩下载的 zip 文件到任意目录
2. 进入 BDvideoTrans 文件夹
3. 双击 BDvideoTrans.exe 或 启动.bat 运行程序

## 系统要求

- Windows 10/11 64位系统
- 至少 4GB 内存
- 至少 10GB 可用磁盘空间
- （可选）NVIDIA 显卡 + CUDA 12+ 用于 GPU 加速

## 重要说明

1. **首次使用需要下载模型**
   - 本版本不包含 Whisper 模型文件
   - 首次运行时请在程序中下载所需模型
   - 模型大小从几百MB到几GB不等

2. **无需安装 Python**
   - 本版本为独立可执行程序
   - 已包含所有必需的依赖

3. **杀毒软件提示**
   - 部分杀毒软件可能误报
   - 请添加到白名单或信任列表

## 功能特性

- 视频翻译和配音
- 支持多种语言互译
- 支持多种语音识别引擎（Faster-Whisper, OpenAI Whisper 等）
- 支持多种翻译引擎（ChatGPT, DeepL, Google 等）
- 支持多种TTS引擎（Edge TTS, Azure TTS, OpenAI TTS 等）
- 字幕生成和编辑
- 人声和背景音乐分离

## 文件说明

- BDvideoTrans.exe: 主程序
- 启动.bat: 启动脚本
- 使用说明.txt: 详细使用说明
- 打包说明.txt: 打包和分发说明
- README.md: 项目说明
- _internal/: 程序依赖文件（不要删除）

## 常见问题

**Q: 程序无法启动？**
A: 请检查：
- 系统是否为 Windows 10/11 64位
- 是否被杀毒软件拦截
- _internal 目录是否完整

**Q: 提示缺少模型？**
A: 首次使用需要在程序中下载模型，请按界面提示操作

**Q: 如何使用 GPU 加速？**
A: 需要 NVIDIA 显卡和 CUDA 12+，在程序设置中启用

## 技术支持

如遇到问题，请查看：
1. logs 目录中的日志文件
2. 使用说明.txt
3. README.md

## 许可证

本软件遵循 GPL-V3 许可证

## 更新日志

v3.80 (2025-10-04)
- 项目重命名为 BDvideoTrans
- 移除所有 pyvideotrans 相关引用
- 优化打包流程
- 不包含 Whisper 模型文件

---
感谢使用 BDvideoTrans！
"""
    
    readme_path = OUTPUT_DIR / "README_发布说明.md"
    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"✓ 已创建发布说明: {readme_path}")

def main():
    print("=" * 60)
    print("BDvideoTrans 发布包创建工具")
    print("=" * 60)
    
    # 创建压缩包
    if not create_zip():
        return False
    
    # 创建发布说明
    create_readme()
    
    print("\n" + "=" * 60)
    print("✓ 发布包创建完成！")
    print(f"输出目录: {OUTPUT_DIR}")
    print("\n可以将 release 目录中的文件分发给用户")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        input("\n按回车键退出...")
    except KeyboardInterrupt:
        print("\n\n× 用户中断")
    except Exception as e:
        print(f"\n× 发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")

