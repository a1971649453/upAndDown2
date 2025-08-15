@echo off
chcp 65001 >nul
echo.
echo ================================================
echo     upAndDown2 云剪切板工具 - 一键安装脚本
echo ================================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未检测到Python
    echo 请先安装Python 3.8+，下载地址：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ 检测到Python环境
python --version

echo.
echo 📦 开始安装依赖包...
echo.

:: 升级pip
echo 🔧 升级pip到最新版本...
python -m pip install --upgrade pip

:: 安装依赖包
echo 📚 安装必需依赖...
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ❌ 依赖安装失败！
    echo 可能的解决方案：
    echo 1. 检查网络连接
    echo 2. 尝试使用国内镜像：pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
    echo 3. 手动安装各个依赖包
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ 依赖安装完成！
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
echo 🎉 安装完成！
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