@echo off
REM 现代化云内端启动脚本 v5.0
echo ===========================================
echo     现代化云内端 v5.0 启动中...
echo ===========================================
echo.
echo 特性说明:
echo - CustomTkinter现代化界面 + 传统Tkinter兼容
echo - MVP架构 + UI与业务逻辑分离
echo - 拖拽上传 + 一键上传
echo - 智能重复检测 + 文件分析
echo - 异步处理 + 事件驱动架构
echo - 性能监控 + 响应式布局
echo.
echo 启动应用...
echo.

python modern_intranet_client.py

if %errorlevel% neq 0 (
    echo.
    echo 启动失败，尝试兼容模式...
    echo 如果问题持续，请检查以下项目:
    echo 1. Python版本是否为3.8+
    echo 2. 是否已安装requirements.txt中的依赖
    echo 3. 是否已运行config_setup.py进行初始配置
    echo 4. CustomTkinter是否正确安装
    echo.
    
    REM 尝试使用原始版本
    echo 回退到原始版本...
    python intranet_gui_client.py
)

echo.
echo 应用已退出
pause