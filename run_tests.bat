@echo off
chcp 65001 >nul
echo 🍪 Cookie同步功能测试工具
echo ========================================
echo.

echo 🔍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请确保Python已安装并添加到PATH
    pause
    exit /b 1
)

echo ✅ Python环境检查通过
echo.

echo 🔍 检查依赖库...
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo ❌ 缺少requests库，正在安装...
    pip install requests
    if errorlevel 1 (
        echo ❌ 安装requests失败，请手动运行: pip install requests
        pause
        exit /b 1
    )
)

echo ✅ 依赖库检查通过
echo.

echo 🚀 开始运行测试...
echo.

echo 📋 测试1: 基础功能测试
echo ----------------------------------------
python test_cookie_sync.py
echo.

echo 📋 测试2: 浏览器脚本模拟测试
echo ----------------------------------------
python test_browser_simulation.py
echo.

echo 🎉 所有测试完成！
echo.
echo 📊 请查看上面的测试结果
echo 💡 如果测试失败，请检查config_manager.py的修复是否正确
echo.

pause
