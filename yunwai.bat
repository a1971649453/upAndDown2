@echo off
title 安全文件下载器 v5.8 - LocalSend风格

echo ==========================================================
echo  正在启动后台文件下载监控程序...
echo.
echo  这个窗口将会持续运行以监控和下载文件。
echo  请不要关闭此窗口，您可以随时将它最小化。
echo ==========================================================
echo.

REM 切换到批处理文件所在的目录
cd /d "%~dp0"

REM 检查虚拟环境是否存在，如果不存在则使用系统Python
if exist ".\.venv\Scripts\python.exe" (
    echo 使用虚拟环境Python...
    ".\.venv\Scripts\python.exe" external_client.py
) else (
    echo 虚拟环境不存在，使用系统Python...
    python external_client.py
)

REM 如果程序异常退出，暂停以查看错误信息
if errorlevel 1 (
    echo.
    echo 程序运行出现错误，请检查以上信息
    pause
)