# 📱 佩宇Reader APP 构建指南

## 功能特点

✅ **书源导入** - 支持Legado格式书源JSON导入  
✅ **实时搜索** - 从书源实时搜索书籍  
✅ **在线阅读** - 直接从书源获取章节内容  
✅ **书架管理** - 添加、删除、管理书籍  
✅ **阅读设置** - 字体大小、背景颜色、翻页效果  
✅ **离线缓存** - 已读章节自动缓存  

---

## 快速构建

### 方式1：使用构建脚本（推荐）

```bash
# 运行构建脚本
build-app.bat
```

构建完成后，APK文件位于 `release/佩宇Reader-v2.0-debug.apk`

### 方式2：手动构建

```bash
# 1. 同步Web资源到Android项目
npx cap sync

# 2. 进入Android目录
cd android

# 3. 构建Debug APK
./gradlew assembleDebug

# 4. APK位置
# android/app/build/outputs/apk/debug/app-debug.apk
```

---

## 环境要求

- **Node.js** 16+ 
- **Android Studio** (用于完整的Android开发)
- **JDK** 11+
- **Android SDK**

### 安装Android Studio

1. 下载并安装 [Android Studio](https://developer.android.com/studio)
2. 安装时选择：
   - Android SDK
   - Android SDK Platform
   - Android Virtual Device (可选)

3. 配置环境变量：
```bash
# Windows
set ANDROID_SDK_ROOT=C:\Users\<用户名>\AppData\Local\Android\Sdk

# 添加到Path
%ANDROID_SDK_ROOT%\platform-tools
```

---

## 项目结构

```
legado_reader/
├── www/                    # Web应用代码
│   ├── index.html         # 主页面
│   ├── app.js             # 核心JavaScript
│   └── capacitor.js       # Capacitor桥接
├── android/               # Android原生项目
│   ├── app/
│   │   └── src/
│   │       └── main/
│   │           ├── AndroidManifest.xml
│   │           ├── java/          # Java/Kotlin代码
│   │           └── assets/public/ # Web资源
│   └── build.gradle
├── capacitor.config.json  # Capacitor配置
└── package.json
```

---

## 开发流程

### 1. 修改Web代码

编辑 `www/` 目录下的文件

### 2. 同步到Android

```bash
npx cap sync
```

### 3. 在Android Studio中打开

```bash
npx cap open android
```

### 4. 运行调试

- 连接手机或启动模拟器
- 点击 Run 按钮

---

## 如何使用书源

### 导入书源

1. 打开APP，点击底部"书源"标签
2. 点击"导入书源"按钮
3. 粘贴书源JSON内容（支持Legado格式）
4. 点击"导入"

### 书源格式示例

```json
[
  {
    "bookSourceName": "笔趣阁",
    "bookSourceUrl": "https://www.biquge.com.cn",
    "enabled": true,
    "ruleSearch": {
      "bookList": "$.data",
      "name": "name",
      "author": "author",
      "coverUrl": "cover",
      "intro": "intro",
      "bookUrl": "bookUrl"
    }
  }
]
```

### 搜索书籍

1. 点击底部"发现"标签
2. 输入书名或作者
3. 点击"搜索"
4. 点击书籍添加到书架

### 阅读书籍

1. 点击底部"书架"标签
2. 点击书籍封面
3. 使用"上一章"/"下一章"切换
4. 点击"设置"调整阅读参数

---

## 常见问题

### Q: 无法安装APK？
A: 需要在手机设置中允许"未知来源应用"安装

### Q: 搜索不到书籍？
A: 检查网络连接，或尝试导入其他书源

### Q: 章节内容加载失败？
A: 书源可能需要更新，尝试导入新的书源

### Q: 如何更新书源？
A: 在"书源"页面禁用旧书源，导入新书源

---

## 技术说明

### APP vs Web 的区别

| 功能 | Web版 | APP版 |
|------|-------|-------|
| 书源搜索 | ❌ 受限 | ✅ 完整支持 |
| 章节获取 | ❌ 静态数据 | ✅ 实时获取 |
| 离线阅读 | ❌ 不支持 | ✅ 支持 |
| 书源导入 | ❌ 不支持 | ✅ 支持 |
| 本地存储 | 浏览器限制 | 完整支持 |

### 核心技术

- **Capacitor** - 跨平台APP框架
- **原生HTTP** - 绕过CORS限制
- **Preferences** - 本地数据存储
- **WebView** - 渲染Web界面

---

## 发布到应用商店

### 构建Release版本

```bash
cd android
./gradlew assembleRelease
```

### 签名APK

```bash
# 生成密钥
keytool -genkey -v -keystore peiyu.keystore -alias peiyu -keyalg RSA -keysize 2048 -validity 10000

# 签名APK
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore peiyu.keystore app-release-unsigned.apk peiyu

# 优化APK
zipalign -v 4 app-release-unsigned.apk 佩宇Reader-release.apk
```

---

## 更新日志

### v2.0
- ✅ 新增书源导入功能
- ✅ 支持Legado格式书源
- ✅ 实时搜索和阅读
- ✅ 阅读设置（字体、背景、翻页）
- ✅ 书架管理和进度保存

---

## 技术支持

如有问题，请提交Issue到GitHub仓库。

**GitHub**: https://github.com/11223456789/peiyu
