@echo off
title 优化版云内端上传工具 v5.1
echo ====================================
echo 启动优化版云内端上传工具 v5.1
echo ====================================
echo.
echo 优化特性:
echo  - 上下布局: 主功能区(75%%) + 活动日志(25%%)
echo  - 智能剪切板监听: 动态间隔调整(0.5-2秒)
echo  - 自动文件清理: 完成状态4秒延迟清理
echo  - 性能监控集成: 实时状态跟踪
echo  - 简化界面: 移除一键上传功能
echo.
echo 正在启动...

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境
    echo 请确保已安装Python 3.8+
    pause
    exit /b 1
)

REM 启动优化版应用
python intranet_gui_client_optimized.py

if errorlevel 1 (
    echo.
    echo 程序运行出现错误，请检查:
    echo 1. 是否已运行 config_setup.py 进行初始配置
    echo 2. 依赖包是否已安装: pip install -r requirements.txt
    echo 3. 系统凭据管理器中是否存在加密密钥
    echo.
    pause
)