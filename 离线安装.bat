@echo off
chcp 65001 >nul
echo.
echo ================================================
echo     upAndDown2 云剪切板工具 - 离线环境部署
echo ================================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未检测到Python
    echo 请先安装Python 3.8+
    echo 离线安装包通常包含在Windows应用商店或可从官网下载离线安装包
    echo.
    pause
    exit /b 1
)

echo ✅ 检测到Python环境
python --version
echo.

:: 检查是否存在离线依赖包目录
if not exist "offline_packages" (
    echo ❌ 错误：未找到离线依赖包目录 'offline_packages'
    echo.
    echo 💡 获取离线依赖包的方法：
    echo 1. 在有网络的环境中运行：pip download -r requirements.txt -d offline_packages
    echo 2. 将offline_packages目录复制到当前目录
    echo 3. 重新运行此脚本
    echo.
    pause
    exit /b 1
)

echo 📦 开始安装离线依赖包...
echo.

:: 从离线包目录安装
python -m pip install --no-index --find-links offline_packages -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ❌ 离线依赖安装失败！
    echo 请检查offline_packages目录中是否包含所有必需的wheel文件
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ 离线依赖安装完成！
echo.
echo 🔧 开始初始化配置...

:: 运行配置向导
python config_setup.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 配置初始化失败！
    echo 请检查配置向导输出的错误信息
    echo.
    pause
    exit /b 1
)

echo.
echo 🎉 离线部署完成！
echo.
echo 💡 使用说明：
echo   📥 云外端（下载）：双击 yunwai.bat
echo   📤 云内端（上传-现代化）：双击 start_modern_intranet.bat
echo   📤 云内端（上传-传统）：双击 启动上传工具.bat
echo   🌐 Cookie同步：双击 start_cookie_server.bat
echo.
echo 📖 详细使用说明请查看 README.md
echo.
pause