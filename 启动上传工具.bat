@echo off
title 安全文件上传工具 - 启动程序

echo =========================================
echo  正在启动安全文件上传GUI工具...
echo =========================================
echo.

REM 切换到批处理文件所在的目录
cd /d "%~dp0"

REM 【核心更新】直接调用.venv环境中的python.exe来执行脚本
".\.venv\Scripts\python.exe" intranet_gui_client.py

echo.
echo =========================================
echo  GUI工具窗口已关闭。
echo =========================================
echo.

pause