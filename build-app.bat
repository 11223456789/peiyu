@echo off
chcp 65001 >nul
echo ==========================================
echo     佩宇Reader APP 构建工具
echo ==========================================
echo.

echo [1/5] 正在同步Web资源...
call npx cap sync
if errorlevel 1 (
    echo 同步失败！
    pause
    exit /b 1
)

echo.
echo [2/5] 正在构建Android项目...
cd android

:: 检查Gradle是否存在
if not exist "gradlew.bat" (
    echo 错误：找不到gradlew.bat
    echo 请确保Android项目已正确初始化
    cd ..
    pause
    exit /b 1
)

:: 构建Debug版本
echo.
echo [3/5] 正在编译Debug APK...
call gradlew.bat assembleDebug
if errorlevel 1 (
    echo 编译失败！
    cd ..
    pause
    exit /b 1
)

echo.
echo [4/5] 正在复制APK文件...
if not exist "..\release" mkdir "..\release"
copy /Y "app\build\outputs\apk\debug\app-debug.apk" "..\release\佩宇Reader-v2.0-debug.apk"

echo.
echo [5/5] 构建完成！
cd ..
echo.
echo ==========================================
echo     ✅ 构建成功！
echo ==========================================
echo.
echo APK文件位置：
echo   release\佩宇Reader-v2.0-debug.apk
echo.
echo 安装方式：
echo   1. 将APK传输到手机
echo   2. 在手机上点击安装
echo   3. 允许未知来源应用安装
echo.
pause
