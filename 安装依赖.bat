@echo off
echo ========================================
echo 正在安装 BDvideoTrans 依赖...
echo ========================================
echo.

REM 激活虚拟环境
echo [1/3] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装基础依赖
echo.
echo [2/3] 安装基础依赖...
pip install -r requirements.txt

REM 安装 HearSight 向量库依赖
echo.
echo [3/3] 安装 HearSight 向量库依赖...
pip install chromadb

echo.
echo ========================================
echo 依赖安装完成！
echo ========================================
echo.
echo 现在可以运行：
echo   - python sp.py        (启动 GUI)
echo   - python api.py       (启动 API 服务)
echo   - python cli.py       (命令行模式)
echo.
pause
