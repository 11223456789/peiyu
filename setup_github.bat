@echo off
chcp 65001 >nul
echo ==========================================
echo  佩宇Reader - GitHub部署初始化脚本
echo ==========================================
echo.

REM 检查git是否安装
git --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未安装Git，请先安装Git
    echo 下载地址: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [1/5] 初始化Git仓库...
git init

echo [2/5] 添加所有文件...
git add .

echo [3/5] 提交代码...
git commit -m "🎉 佩宇Reader初始提交 - AI智能阅读器

功能特性:
- 支持Legado书源格式
- AI智能推荐系统
- 阅读统计与成就系统
- TTS语音朗读
- 数据备份与同步
- 多主题切换
- 全文搜索"

echo [4/5] 创建main分支...
git branch -M main

echo.
echo [5/5] 配置远程仓库...
echo.
echo 请先在GitHub创建仓库，然后输入仓库地址
echo 示例: https://github.com/用户名/peiyu-reader.git
echo.
set /p repo_url="GitHub仓库地址: "

git remote add origin %repo_url%
git push -u origin main

echo.
echo ==========================================
echo  ✅ GitHub仓库初始化完成！
echo ==========================================
echo.
echo 下一步: 访问 https://vercel.com 进行部署
echo.
pause
