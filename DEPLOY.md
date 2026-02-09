# 佩宇Reader 部署指南

## 🚀 快速开始

### 1. Web版本（已运行）
```bash
# 当前已在运行
http://localhost:8000
```

### 2. 打包为桌面应用
```bash
# 安装打包工具
pip install pyinstaller

# 打包为exe
pyinstaller --onefile --windowed --name "佩宇Reader" main.py
```

### 3. 打包为Android App
```bash
# 安装Kivy和Buildozer
pip install kivy buildozer

# 初始化配置
buildozer init

# 构建APK
buildozer android debug deploy run
```

---

## 🌐 永久Web部署（GitHub + Vercel）

### 步骤1: 创建GitHub仓库
1. 访问 https://github.com/new
2. 仓库名: `peiyu-reader`
3. 选择 "Public"
4. 创建仓库

### 步骤2: 上传代码
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的用户名/peiyu-reader.git
git push -u origin main
```

### 步骤3: Vercel部署
1. 访问 https://vercel.com
2. 用GitHub账号登录
3. 点击 "New Project"
4. 选择 `peiyu-reader` 仓库
5. 点击 "Deploy"

✅ 完成！获得永久域名：`https://peiyu-reader.vercel.app`

---

## 📱 移动端适配方案

### 方案1: PWA（渐进式Web应用）
- 无需安装，添加到主屏幕即可
- 支持离线阅读
- 自动更新

### 方案2: WebView封装
- 使用Cordova/Capacitor
- 快速生成iOS/Android应用
- 维护成本低

### 方案3: 原生开发（推荐）
- Flutter: 一套代码，多端运行
- React Native: 社区活跃
- 性能最好，用户体验佳

---

## 💰 成本对比

| 方案 | 月费用 | 维护难度 | 适合人群 |
|------|--------|----------|----------|
| GitHub+Vercel | 免费 | ⭐ | 个人用户 |
| 云服务器 | 50-100元 | ⭐⭐⭐ | 团队/商业 |
| 专业App开发 | 5000+元 | ⭐⭐⭐⭐⭐ | 商业化产品 |

---

## 🔧 当前项目结构

```
legado_reader/
├── core/           # 核心功能
├── ui/             # 界面组件
├── web/            # Web服务
├── sources/        # 书源配置
├── main.py         # CLI入口
├── web/main.py     # Web入口
└── requirements.txt # 依赖
```

---

## 📞 技术支持

如有问题，请查看：
- 项目文档: README.md
- 测试脚本: test_system.py
- 配置文件: ~/.peiyu_reader/
