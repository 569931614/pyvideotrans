@echo off
echo ========================================
echo 启动 BDvideoTrans GUI
echo ========================================
echo.

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 启动程序
python sp.py

pause
