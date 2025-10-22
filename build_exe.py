"""
BDvideoTrans 打包脚本
使用 PyInstaller 将项目打包成可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.absolute()
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"

# 需要包含的数据文件和目录
INCLUDE_DATA = [
    ('videotrans/styles', 'videotrans/styles'),
    ('videotrans/language', 'videotrans/language'),
    ('videotrans/webui', 'videotrans/webui'),
    ('videotrans/configure', 'videotrans/configure'),
    ('videotrans/*.txt', 'videotrans'),
    ('videotrans/*.json', 'videotrans'),
    ('videotrans/*.ini', 'videotrans'),
    ('ffmpeg/ffmpeg.exe', 'ffmpeg'),
    ('ffmpeg/ffprobe.exe', 'ffmpeg'),
    ('version.json', '.'),
    ('azure_voice_list.json', '.'),
    ('voice_list.json', '.'),
    ('elevenlabs.json', '.'),
]

# 动态添加 faster-whisper 的资源文件
try:
    import faster_whisper
    import os
    from pathlib import Path
    fw_path = Path(faster_whisper.__file__).parent
    fw_assets = fw_path / 'assets'
    if fw_assets.exists():
        # 使用 as_posix() 确保路径使用正斜杠
        INCLUDE_DATA.append((fw_assets.as_posix(), 'faster_whisper/assets'))
        print(f"✓ 将包含 faster-whisper 资源文件: {fw_assets.as_posix()}")
except ImportError:
    print("× faster-whisper 未安装，跳过资源文件")

# 需要排除的模块（减小体积）
EXCLUDE_MODULES = [
    'matplotlib',
    'scipy',
    'pandas',
    'IPython',
    'jupyter',
    'notebook',
    'pytest',
    # 'setuptools',  # 不排除 setuptools，因为 pkg_resources 需要它
]

# 隐藏导入（PyInstaller 可能检测不到的模块）
HIDDEN_IMPORTS = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'shiboken6',
    'edge_tts',
    'flask',
    'waitress',
    'anthropic',
    'openai',
    'deepl',
    'gtts',
    'azure.cognitiveservices.speech',
    'elevenlabs',
    'deepgram',
    'funasr',
    'modelscope',
    'google.cloud.texttospeech',
    'google.genai',
    'tencentcloud',
    'alibabacloud_alimt20181012',
    # 修复 pkg_resources 依赖问题
    'pkg_resources',
    'pkg_resources.py2_warn',
    'jaraco.text',
    'jaraco.functools',
    'jaraco.context',
    'more_itertools',
    # 修复 config 模块动态导入问题
    'videotrans.configure._config_loader',
    'videotrans.configure._base',
    'videotrans.configure._except',
    'videotrans.configure._guiexcept',
    # 修复 ChromaDB 依赖问题
    'chromadb',
    'chromadb.api',
    'chromadb.api.client',
    'chromadb.api.models',
    'chromadb.api.types',
    'chromadb.config',
    'chromadb.db',
    'chromadb.db.impl',
    'chromadb.db.impl.sqlite',
    'chromadb.telemetry',
    'chromadb.telemetry.product',
    'chromadb.telemetry.product.posthog',
    'chromadb.utils',
    'chromadb.utils.embedding_functions',
    'chromadb.api.rust',
    'chromadb.api.fastapi',
    'chromadb.api.segment',
    'chromadb.segment',
    'chromadb.segment.impl',
    'chromadb.segment.impl.manager',
    'chromadb.segment.impl.metadata',
    'chromadb.segment.impl.vector',
]

def check_pyinstaller():
    """检查并安装 PyInstaller"""
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
        return True
    except ImportError:
        print("× PyInstaller 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✓ PyInstaller 安装完成")
        return True

def clean_build():
    """清理之前的构建文件"""
    print("\n清理旧的构建文件...")
    for dir_path in [BUILD_DIR, DIST_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  已删除: {dir_path}")
    
    # 删除 spec 文件
    spec_file = ROOT_DIR / "BDvideoTrans.spec"
    if spec_file.exists():
        spec_file.unlink()
        print(f"  已删除: {spec_file}")

def create_spec_file():
    """创建 PyInstaller spec 文件"""
    print("\n创建 spec 文件...")

    # 构建 datas 参数
    datas_str = "[\n"
    for src, dst in INCLUDE_DATA:
        datas_str += f"        ('{src}', '{dst}'),\n"
    datas_str += "    ]"

    # 构建 excludes 参数
    excludes_str = str(EXCLUDE_MODULES)

    # 构建 hiddenimports 参数
    hiddenimports_str = str(HIDDEN_IMPORTS)

    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# 获取 Python DLL 路径
python_dll = os.path.join(sys.base_prefix, 'python310.dll')
python3_dll = os.path.join(sys.base_prefix, 'python3.dll')

# 准备 binaries 列表
binaries_list = []
if os.path.exists(python_dll):
    binaries_list.append((python_dll, '.'))
if os.path.exists(python3_dll):
    binaries_list.append((python3_dll, '.'))

a = Analysis(
    ['sp.py'],
    pathex=[],
    binaries=binaries_list,
    datas={datas_str},
    hiddenimports={hiddenimports_str},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={excludes_str},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BDvideoTrans',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 临时启用控制台窗口以便调试
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='videotrans/styles/icon.ico' if os.path.exists('videotrans/styles/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BDvideoTrans',
)
"""

    spec_file = ROOT_DIR / "BDvideoTrans.spec"
    spec_file.write_text(spec_content, encoding='utf-8')
    print(f"✓ Spec 文件已创建: {spec_file}")
    return spec_file

def build_exe(spec_file):
    """使用 PyInstaller 构建可执行文件"""
    print("\n开始构建可执行文件...")
    print("这可能需要几分钟时间，请耐心等待...\n")
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--clean",
        str(spec_file)
    ]
    
    result = subprocess.run(cmd, cwd=ROOT_DIR)
    
    if result.returncode == 0:
        print("\n✓ 构建成功！")
        return True
    else:
        print("\n× 构建失败！")
        return False

def copy_additional_files():
    """复制额外需要的文件到 dist 目录"""
    print("\n复制额外文件...")
    
    dist_app_dir = DIST_DIR / "BDvideoTrans"
    if not dist_app_dir.exists():
        print("× 找不到输出目录")
        return False
    
    # 创建必要的目录
    additional_dirs = [
        'tmp',
        'cache',
        'ffmpeg',  # 添加 ffmpeg 目录
    ]

    for dir_name in additional_dirs:
        dir_path = dist_app_dir / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"  已创建目录: {dir_name}")

    # 复制 ffmpeg 文件到正确的位置
    ffmpeg_src_dir = ROOT_DIR / "ffmpeg"
    ffmpeg_dst_dir = dist_app_dir / "ffmpeg"
    if ffmpeg_src_dir.exists():
        for exe_name in ['ffmpeg.exe', 'ffprobe.exe']:
            src_file = ffmpeg_src_dir / exe_name
            if src_file.exists():
                dst_file = ffmpeg_dst_dir / exe_name
                shutil.copy2(src_file, dst_file)
                print(f"  已复制: {exe_name} ({src_file.stat().st_size / 1024 / 1024:.1f} MB)")
            else:
                print(f"  警告: 找不到 {exe_name}")
    else:
        print(f"  警告: 找不到 ffmpeg 源目录")
    
    # 复制 README
    readme_src = ROOT_DIR / "README.md"
    if readme_src.exists():
        shutil.copy2(readme_src, dist_app_dir / "README.md")
        print(f"  已复制: README.md")
    
    # 创建启动说明文件
    usage_file = dist_app_dir / "使用说明.txt"
    usage_content = """BDvideoTrans 使用说明

1. 双击 BDvideoTrans.exe 启动程序

2. 首次使用需要下载语音识别模型：
   - 在设置中选择并下载所需的 Whisper 模型
   - 模型会自动下载到 models 目录

3. 注意事项：
   - 请确保有足够的磁盘空间用于临时文件
   - 视频处理需要较长时间，请耐心等待
   - 如遇到问题，请查看 logs 目录中的日志文件

4. 目录说明：
   - tmp: 临时文件目录
   - cache: 缓存目录
   - logs: 日志文件目录
   - models: 模型文件目录（需要自行下载）

更多信息请参考 README.md
"""
    usage_file.write_text(usage_content, encoding='utf-8')
    print(f"  已创建: 使用说明.txt")
    
    return True

def create_installer_script():
    """创建安装脚本"""
    print("\n创建安装脚本...")
    
    dist_app_dir = DIST_DIR / "BDvideoTrans"
    if not dist_app_dir.exists():
        return False
    
    # 创建启动脚本
    start_script = dist_app_dir / "启动.bat"
    start_content = """@echo off
chcp 65001 >nul
echo 正在启动 BDvideoTrans...
start "" "BDvideoTrans.exe"
"""
    start_script.write_text(start_content, encoding='utf-8')
    print(f"  已创建: 启动.bat")
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("BDvideoTrans 打包工具")
    print("=" * 60)
    
    # 检查 PyInstaller
    if not check_pyinstaller():
        print("\n× 无法安装 PyInstaller，打包终止")
        return False
    
    # 清理旧文件
    clean_build()
    
    # 创建 spec 文件
    spec_file = create_spec_file()
    
    # 构建可执行文件
    if not build_exe(spec_file):
        return False
    
    # 复制额外文件
    if not copy_additional_files():
        print("\n警告: 复制额外文件时出现问题")
    
    # 创建安装脚本
    if not create_installer_script():
        print("\n警告: 创建安装脚本时出现问题")
    
    # 完成
    print("\n" + "=" * 60)
    print("✓ 打包完成！")
    print(f"输出目录: {DIST_DIR / 'BDvideoTrans'}")
    print("\n注意:")
    print("1. 可执行文件位于 dist/BDvideoTrans 目录")
    print("2. 不包含 Whisper 模型文件，用户需要在首次使用时下载")
    print("3. 建议将整个 BDvideoTrans 文件夹打包分发")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n× 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n× 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

