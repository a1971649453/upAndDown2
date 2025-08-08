@echo off
title Cookie服务 - [后台运行中]
echo 正在启动本地Cookie接收服务...请保持此窗口运行。
cd /d "%~dp0"
".\.venv\Scripts\python.exe" cookie_server.py