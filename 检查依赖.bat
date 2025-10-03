@echo off
echo ========================================
echo 快速测试：检查依赖安装情况
echo ========================================
echo.

call venv\Scripts\activate.bat

echo [1] 检查 PySide6...
python -c "import PySide6; print('✅ PySide6 已安装:', PySide6.__version__)" 2>nul
if errorlevel 1 (
    echo ❌ PySide6 未安装
) else (
    echo.
)

echo [2] 检查 ChromaDB...
python -c "import chromadb; print('✅ ChromaDB 已安装:', chromadb.__version__)" 2>nul
if errorlevel 1 (
    echo ❌ ChromaDB 未安装或正在安装中...
    echo    请运行 "安装依赖.bat" 完成安装
) else (
    echo.
)

echo [3] 检查其他核心依赖...
python -c "import torch; print('✅ PyTorch 已安装')" 2>nul
if errorlevel 1 echo ⚠️ PyTorch 未安装

python -c "import requests; print('✅ requests 已安装')" 2>nul
if errorlevel 1 echo ⚠️ requests 未安装

echo.
echo ========================================
echo 检查完成！
echo ========================================
echo.
echo 如果有未安装的依赖，请运行：安装依赖.bat
echo.
pause
