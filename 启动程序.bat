@echo off
echo ========================================
echo 启动 BDvideoTrans GUI
echo ========================================
echo.

REM 设置控制台编码为 UTF-8
chcp 65001 >nul

REM 清理 Python 缓存（每次启动时）
echo 清理 Python 缓存...
for /d /r videotrans %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 验证环境
echo 验证 Python 环境...
python -c "import sys; print('Python:', sys.executable)"
python -c "import qdrant_client; print('qdrant_client: OK')" 2>nul
if errorlevel 1 (
    echo.
    echo 错误: qdrant_client 未安装
    echo 正在安装...
    python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple qdrant-client chardet
)

echo.
echo 启动程序...
echo ========================================
echo.

REM 启动程序
python sp.py

pause
