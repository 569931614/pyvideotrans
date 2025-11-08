@echo off
echo ========================================
echo 修复 Qdrant Client 问题
echo ========================================
echo.

echo [1/4] 检查 venv 环境...
if not exist "venv\Scripts\python.exe" (
    echo 错误: venv 不存在！
    pause
    exit /b 1
)

echo [2/4] 清理 Python 缓存...
rmdir /s /q videotrans\__pycache__ 2>nul
rmdir /s /q videotrans\hearsight\__pycache__ 2>nul
rmdir /s /q videotrans\qdrant_export\__pycache__ 2>nul
for /d /r videotrans %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
echo 缓存已清理

echo [3/4] 重新安装 qdrant-client 和 chardet...
venv\Scripts\python.exe -m pip uninstall -y qdrant-client chardet portalocker h2 hpack hyperframe
venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple qdrant-client chardet

echo [4/4] 验证安装...
venv\Scripts\python.exe -c "import qdrant_client; import chardet; print('✓ 安装成功')" 2>&1
if errorlevel 1 (
    echo.
    echo 安装失败，请检查网络连接！
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✓ 修复完成！
echo ========================================
echo.
echo 现在可以运行 "启动程序.bat" 了
echo.
pause
