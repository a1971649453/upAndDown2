@echo off
chcp 65001 >nul
echo.
echo ================================================
echo     upAndDown2 - 离线依赖包下载器
echo ================================================
echo.
echo 💡 此脚本用于在有网络的环境中下载离线依赖包
echo    然后可将依赖包复制到离线环境使用
echo.

:: 检查Python和pip
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未检测到Python
    pause
    exit /b 1
)

echo ✅ 检测到Python环境
python --version
echo.

:: 创建离线包目录
if not exist "offline_packages" mkdir offline_packages

echo 📦 开始下载依赖包到 offline_packages 目录...
echo.

:: 下载所有依赖包及其依赖
python -m pip download -r requirements.txt -d offline_packages

if %errorlevel% neq 0 (
    echo.
    echo ❌ 依赖包下载失败！
    echo 请检查网络连接和requirements.txt文件
    pause
    exit /b 1
)

echo.
echo ✅ 依赖包下载完成！
echo.
echo 📁 离线包存储位置：%cd%\offline_packages
echo.
echo 💡 使用方法：
echo 1. 将整个 offline_packages 目录复制到离线环境
echo 2. 在离线环境中运行 离线安装.bat
echo.
echo 📊 离线包统计：
dir /b offline_packages | find /c /v "" && echo 个文件已下载

echo.
pause