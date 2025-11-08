@echo off
chcp 65001 >nul
echo ============================================================
echo BDvideoTrans 一键打包工具
echo ============================================================
echo.
echo 此脚本将执行以下操作：
echo 1. 使用 PyInstaller 打包程序
echo 2. 创建发布压缩包
echo.
echo 注意：打包过程可能需要 5-10 分钟
echo.
pause

echo.
echo [1/2] 正在打包程序...
echo ============================================================
python build_exe.py
if errorlevel 1 (
    echo.
    echo × 打包失败！
    pause
    exit /b 1
)

echo.
echo [2/2] 正在创建发布包...
echo ============================================================
python create_release.py
if errorlevel 1 (
    echo.
    echo × 创建发布包失败！
    pause
    exit /b 1
)

echo.
echo ============================================================
echo ✓ 所有操作完成！
echo.
echo 打包结果：
echo - 可执行程序: dist\BDvideoTrans\
echo - 发布压缩包: release\
echo ============================================================
echo.
pause

