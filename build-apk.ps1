# 构建APK脚本
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.18.8-hotspot"
$env:Path = "$env:JAVA_HOME\bin;$env:Path"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "    佩宇Reader APK 构建工具" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 验证Java版本
Write-Host "[1/5] 验证Java版本..." -ForegroundColor Yellow
java -version

# 同步Capacitor
Write-Host ""
Write-Host "[2/5] 同步Capacitor资源..." -ForegroundColor Yellow
cd "$PSScriptRoot"
npx cap sync

# 进入Android目录
Write-Host ""
Write-Host "[3/5] 构建Debug APK..." -ForegroundColor Yellow
cd android
.\gradlew.bat assembleDebug

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[4/5] 复制APK文件..." -ForegroundColor Yellow
    if (!(Test-Path "..\release")) {
        New-Item -ItemType Directory -Path "..\release" | Out-Null
    }
    Copy-Item "app\build\outputs\apk\debug\app-debug.apk" "..\release\佩宇Reader-v2.0-debug.apk" -Force
    
    Write-Host ""
    Write-Host "[5/5] 构建完成！" -ForegroundColor Green
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "    ✅ 构建成功！" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "APK文件位置：" -ForegroundColor White
    Write-Host "  release\佩宇Reader-v2.0-debug.apk" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "安装方式：" -ForegroundColor White
    Write-Host "  1. 将APK传输到手机" -ForegroundColor Gray
    Write-Host "  2. 在手机上点击安装" -ForegroundColor Gray
    Write-Host "  3. 允许未知来源应用安装" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "❌ 构建失败！" -ForegroundColor Red
}

Write-Host ""
Read-Host "按回车键退出"
