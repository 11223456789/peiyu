"""
佩宇Reader - Vercel Serverless部署入口
完整的Web版阅读器 - 支持书源解析
"""
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
import json
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(
    title="佩宇Reader",
    description="AI智能阅读器 - Web版（支持书源解析）",
    version="2.1.0"
)

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 加载书源配置
def load_book_sources():
    """加载书源配置"""
    try:
        sources_file = os.path.join(current_dir, '..', 'sources', 'book_sources.json')
        if os.path.exists(sources_file):
            with open(sources_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading sources: {e}")
    return []

# 示例书籍数据（用于演示）
SAMPLE_BOOKS = [
    {
        "id": "1",
        "name": "斗破苍穹",
        "author": "天蚕土豆",
        "cover": "https://via.placeholder.com/150x200/4a90e2/ffffff?text=斗破苍穹",
        "intro": "这里是斗气大陆，没有花俏艳丽的魔法，有的，仅仅是繁衍到巅峰的斗气！",
        "source": "笔趣阁",
        "category": "reading",
        "progress": 35,
        "chapters": [
            {"id": 1, "title": "第一章 陨落的天才"},
            {"id": 2, "title": "第二章 斗之气，三段！"},
            {"id": 3, "title": "第三章 客人"},
            {"id": 4, "title": "第四章 云岚宗"},
            {"id": 5, "title": "第五章 聚气散"},
        ]
    },
    {
        "id": "2",
        "name": "完美世界",
        "author": "辰东",
        "cover": "https://via.placeholder.com/150x200/e74c3c/ffffff?text=完美世界",
        "intro": "一粒尘可填海，一根草斩尽日月星辰，弹指间天翻地覆。",
        "source": "起点",
        "category": "reading",
        "progress": 0,
        "chapters": [
            {"id": 1, "title": "第一章 朝气蓬勃"},
            {"id": 2, "title": "第二章 柳神"},
            {"id": 3, "title": "第三章 药浴"},
            {"id": 4, "title": "第四章 宝术"},
            {"id": 5, "title": "第五章 凶兽"},
        ]
    },
    {
        "id": "3",
        "name": "遮天",
        "author": "辰东",
        "cover": "https://via.placeholder.com/150x200/27ae60/ffffff?text=遮天",
        "intro": "冰冷与黑暗并存的宇宙深处，九具庞大的龙尸拉着一口青铜古棺，亘古长存。",
        "source": "番茄小说",
        "category": "completed",
        "progress": 100,
        "chapters": [
            {"id": 1, "title": "第一章 星空中的青铜巨棺"},
            {"id": 2, "title": "第二章 荒古禁地"},
            {"id": 3, "title": "第三章 神泉"},
            {"id": 4, "title": "第四章 道经"},
            {"id": 5, "title": "第五章 妖帝坟冢"},
        ]
    },
]

# 示例章节内容
SAMPLE_CONTENT = """
<p>这是示例章节内容。在实际部署中，这里将显示从书源获取的真实章节内容。</p>
<p>Web版佩宇Reader支持以下功能：</p>
<p>1. <strong>书架管理</strong> - 添加、删除、分类管理书籍，支持阅读进度记录</p>
<p>2. <strong>书源搜索</strong> - 从多个书源搜索书籍，支持关键词搜索</p>
<p>3. <strong>在线阅读</strong> - 支持章节切换、阅读进度保存、字体调整</p>
<p>4. <strong>阅读统计</strong> - 记录阅读时长、完成章节、阅读字数等数据</p>
<p>5. <strong>个性化设置</strong> - 字体大小、背景颜色、翻页效果自定义</p>
<p>6. <strong>书源管理</strong> - 启用/禁用书源，支持多源切换</p>
<p>7. <strong>数据同步</strong> - 支持本地存储，数据不丢失</p>
<p>这是一个演示段落，展示阅读器的排版效果。文字清晰，行间距适中，阅读体验舒适。</p>
<p>点击下方的"上一章"和"下一章"按钮可以切换章节。点击右上角的目录按钮可以查看章节目录。</p>
<p>感谢您的使用！如需完整功能，请使用桌面版CLI版本。</p>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    """首页 - 完整的APP界面"""
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>佩宇Reader - AI智能阅读器</title>
    <meta name="theme-color" content="#1a1a2e">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
        
        :root {{
            --primary: #00d4ff;
            --secondary: #7b2cbf;
            --bg-dark: #1a1a2e;
            --bg-card: rgba(255,255,255,0.05);
            --text-primary: #ffffff;
            --text-secondary: #888888;
            --border: rgba(255,255,255,0.1);
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: var(--text-primary);
            overflow-x: hidden;
        }}
        
        .bottom-nav {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(26, 26, 46, 0.95);
            backdrop-filter: blur(20px);
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-around;
            padding: 8px 0;
            z-index: 1000;
        }}
        
        .nav-item {{ display: flex; flex-direction: column; align-items: center; padding: 5px 20px; cursor: pointer; transition: all 0.3s; color: var(--text-secondary); }}
        .nav-item.active {{ color: var(--primary); }}
        .nav-item i {{ font-size: 24px; margin-bottom: 4px; }}
        .nav-item span {{ font-size: 12px; }}
        
        .page {{ display: none; padding: 20px; padding-bottom: 80px; min-height: 100vh; animation: fadeIn 0.3s ease; }}
        .page.active {{ display: block; }}
        
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-top: 10px; }}
        .header h1 {{ font-size: 28px; background: linear-gradient(45deg, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .header-actions {{ display: flex; gap: 15px; }}
        
        .icon-btn {{
            width: 40px; height: 40px; border-radius: 50%; background: var(--bg-card);
            border: 1px solid var(--border); color: var(--text-primary);
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; font-size: 20px; transition: all 0.3s;
        }}
        .icon-btn:hover {{ background: rgba(0, 212, 255, 0.1); border-color: var(--primary); }}
        
        .search-bar {{ display: flex; gap: 10px; margin-bottom: 20px; }}
        .search-input {{
            flex: 1; padding: 12px 20px; border-radius: 25px; border: 1px solid var(--border);
            background: var(--bg-card); color: var(--text-primary); font-size: 16px;
            outline: none; transition: all 0.3s;
        }}
        .search-input:focus {{ border-color: var(--primary); box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1); }}
        .search-input::placeholder {{ color: var(--text-secondary); }}
        
        .search-btn {{
            padding: 12px 25px; border-radius: 25px; border: none;
            background: linear-gradient(45deg, var(--primary), var(--secondary));
            color: white; font-size: 16px; cursor: pointer; transition: all 0.3s;
        }}
        .search-btn:hover {{ transform: scale(1.05); box-shadow: 0 5px 20px rgba(0, 212, 255, 0.3); }}
        
        .category-tabs {{ display: flex; gap: 10px; margin-bottom: 20px; overflow-x: auto; padding-bottom: 5px; }}
        .category-tab {{
            padding: 8px 20px; border-radius: 20px; background: var(--bg-card);
            border: 1px solid var(--border); color: var(--text-secondary);
            cursor: pointer; white-space: nowrap; transition: all 0.3s;
        }}
        .category-tab.active {{ background: linear-gradient(45deg, var(--primary), var(--secondary)); color: white; border-color: transparent; }}
        
        .books-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }}
        @media (min-width: 768px) {{ .books-grid {{ grid-template-columns: repeat(4, 1fr); }} }}
        @media (min-width: 1024px) {{ .books-grid {{ grid-template-columns: repeat(5, 1fr); }} }}
        
        .book-card {{ cursor: pointer; transition: all 0.3s; }}
        .book-card:hover {{ transform: translateY(-5px); }}
        .book-cover {{ width: 100%; aspect-ratio: 3/4; border-radius: 8px; object-fit: cover; box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 8px; }}
        .book-title {{ font-size: 14px; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 4px; }}
        .book-author {{ font-size: 12px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .book-progress {{ font-size: 11px; color: var(--primary); margin-top: 4px; }}
        
        .empty-state {{ text-align: center; padding: 60px 20px; color: var(--text-secondary); }}
        
        .stats-cards {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; padding: 20px; text-align: center; }}
        .stat-value {{ font-size: 32px; font-weight: bold; background: linear-gradient(45deg, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 5px; }}
        .stat-label {{ font-size: 14px; color: var(--text-secondary); }}
        
        .settings-list {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; overflow: hidden; }}
        .setting-item {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border); cursor: pointer; transition: all 0.3s; }}
        .setting-item:last-child {{ border-bottom: none; }}
        .setting-item:hover {{ background: rgba(255,255,255,0.02); }}
        .setting-left {{ display: flex; align-items: center; gap: 15px; }}
        .setting-icon {{ width: 36px; height: 36px; border-radius: 10px; background: linear-gradient(45deg, var(--primary), var(--secondary)); display: flex; align-items: center; justify-content: center; font-size: 18px; }}
        .setting-info h3 {{ font-size: 16px; color: var(--text-primary); margin-bottom: 2px; }}
        .setting-info p {{ font-size: 13px; color: var(--text-secondary); }}
        .setting-arrow {{ color: var(--text-secondary); font-size: 20px; }}
        
        .reader-page {{
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: #1a1a1a; z-index: 2000; display: none; flex-direction: column;
        }}
        .reader-page.active {{ display: flex; }}
        .reader-header {{ display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: rgba(0,0,0,0.8); backdrop-filter: blur(10px); }}
        .reader-title {{ font-size: 16px; color: var(--text-primary); }}
        .reader-content {{ flex: 1; overflow-y: auto; padding: 20px; line-height: 1.8; font-size: 18px; color: #ccc; }}
        .reader-content h2 {{ color: var(--text-primary); margin-bottom: 20px; font-size: 22px; }}
        .reader-content p {{ margin-bottom: 15px; text-indent: 2em; }}
        .reader-toolbar {{ display: flex; justify-content: space-around; padding: 15px; background: rgba(0,0,0,0.8); backdrop-filter: blur(10px); }}
        .reader-btn {{ padding: 10px 30px; border-radius: 25px; border: 1px solid var(--border); background: transparent; color: var(--text-primary); cursor: pointer; transition: all 0.3s; }}
        .reader-btn:hover {{ background: var(--bg-card); border-color: var(--primary); }}
        
        .chapter-list {{
            position: fixed; top: 0; right: -100%; width: 80%; max-width: 400px;
            height: 100%; background: var(--bg-dark); z-index: 2001;
            transition: right 0.3s ease; display: flex; flex-direction: column;
        }}
        .chapter-list.active {{ right: 0; }}
        .chapter-header {{ padding: 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }}
        .chapter-list-content {{ flex: 1; overflow-y: auto; padding: 10px 0; }}
        .chapter-item {{ padding: 15px 20px; border-bottom: 1px solid var(--border); cursor: pointer; transition: all 0.2s; color: var(--text-secondary); }}
        .chapter-item:hover, .chapter-item.active {{ background: rgba(0, 212, 255, 0.1); color: var(--primary); padding-left: 30px; }}
        
        .overlay {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 2000; display: none; }}
        .overlay.active {{ display: block; }}
        
        .loading {{ display: flex; justify-content: center; align-items: center; padding: 40px; }}
        .loading-spinner {{ width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--primary); border-radius: 50%; animation: spin 1s linear infinite; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        
        .source-list {{ display: flex; flex-direction: column; gap: 10px; }}
        .source-item {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; }}
        .source-info h3 {{ font-size: 16px; color: var(--text-primary); margin-bottom: 4px; }}
        .source-info p {{ font-size: 13px; color: var(--text-secondary); }}
        .source-toggle {{ width: 50px; height: 28px; border-radius: 14px; background: var(--bg-card); border: 2px solid var(--border); position: relative; cursor: pointer; transition: all 0.3s; }}
        .source-toggle.active {{ background: linear-gradient(45deg, var(--primary), var(--secondary)); border-color: transparent; }}
        .source-toggle::after {{ content: ''; position: absolute; width: 20px; height: 20px; border-radius: 50%; background: white; top: 2px; left: 2px; transition: all 0.3s; }}
        .source-toggle.active::after {{ left: 26px; }}
        
        .toast {{
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: rgba(0,0,0,0.9); color: white; padding: 15px 30px;
            border-radius: 10px; z-index: 3000; display: none;
        }}
        .toast.show {{ display: block; }}
    </style>
</head>
<body>
    <!-- 书架页面 -->
    <div class="page active" id="bookshelf-page">
        <div class="header">
            <h1>📚 我的书架</h1>
            <div class="header-actions">
                <button class="icon-btn" onclick="showSearch()">🔍</button>
                <button class="icon-btn" onclick="showAddBook()">➕</button>
            </div>
        </div>
        
        <div class="category-tabs">
            <div class="category-tab active" data-category="all">全部</div>
            <div class="category-tab" data-category="reading">在读</div>
            <div class="category-tab" data-category="completed">已读完</div>
            <div class="category-tab" data-category="favorite">收藏</div>
        </div>
        
        <div class="books-grid" id="bookshelf-grid"></div>
        
        <div class="empty-state" id="empty-bookshelf" style="display: none;">
            <div style="font-size: 64px; margin-bottom: 20px;">📖</div>
            <p>书架是空的</p>
            <p style="margin-top: 10px; font-size: 14px;">点击右上角 + 添加书籍</p>
        </div>
    </div>
    
    <!-- 发现页面 -->
    <div class="page" id="discover-page">
        <div class="header">
            <h1>🔍 发现</h1>
        </div>
        
        <div class="search-bar">
            <input type="text" class="search-input" id="search-input" placeholder="搜索书名、作者...">
            <button class="search-btn" onclick="searchBooks()">搜索</button>
        </div>
        
        <div class="category-tabs">
            <div class="category-tab active" data-type="hot">热门</div>
            <div class="category-tab" data-type="new">新书</div>
            <div class="category-tab" data-type="rank">排行榜</div>
            <div class="category-tab" data-type="recommend">推荐</div>
        </div>
        
        <div class="books-grid" id="discover-grid"></div>
    </div>
    
    <!-- 书源页面 -->
    <div class="page" id="sources-page">
        <div class="header">
            <h1>🔌 书源管理</h1>
            <div class="header-actions">
                <button class="icon-btn" onclick="refreshSources()">🔄</button>
            </div>
        </div>
        
        <div class="source-list" id="source-list"></div>
    </div>
    
    <!-- 统计页面 -->
    <div class="page" id="stats-page">
        <div class="header">
            <h1>📊 阅读统计</h1>
        </div>
        
        <div class="stats-cards">
            <div class="stat-card">
                <div class="stat-value" id="stat-books">0</div>
                <div class="stat-label">阅读书籍</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-chapters">0</div>
                <div class="stat-label">完成章节</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-time">0</div>
                <div class="stat-label">阅读小时</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-words">0</div>
                <div class="stat-label">阅读万字</div>
            </div>
        </div>
        
        <div class="settings-list">
            <div class="setting-item">
                <div class="setting-left">
                    <div class="setting-icon">📅</div>
                    <div class="setting-info">
                        <h3>阅读日历</h3>
                        <p>查看每日阅读记录</p>
                    </div>
                </div>
                <span class="setting-arrow">›</span>
            </div>
            <div class="setting-item">
                <div class="setting-left">
                    <div class="setting-icon">🏆</div>
                    <div class="setting-info">
                        <h3>阅读成就</h3>
                        <p>解锁阅读里程碑</p>
                    </div>
                </div>
                <span class="setting-arrow">›</span>
            </div>
            <div class="setting-item">
                <div class="setting-left">
                    <div class="setting-icon">📈</div>
                    <div class="setting-info">
                        <h3>阅读趋势</h3>
                        <p>分析阅读习惯</p>
                    </div>
                </div>
                <span class="setting-arrow">›</span>
            </div>
        </div>
    </div>
    
    <!-- 设置页面 -->
    <div class="page" id="settings-page">
        <div class="header">
            <h1>⚙️ 设置</h1>
        </div>
        
        <div class="settings-list">
            <div class="setting-item" onclick="showReadingSettings()">
                <div class="setting-left">
                    <div class="setting-icon">📖</div>
                    <div class="setting-info">
                        <h3>阅读设置</h3>
                        <p>字体、背景、翻页效果</p>
                    </div>
                </div>
                <span class="setting-arrow">›</span>
            </div>
            <div class="setting-item" onclick="showDownloadSettings()">
                <div class="setting-left">
                    <div class="setting-icon">💾</div>
                    <div class="setting-info">
                        <h3>下载管理</h3>
                        <p>缓存和下载设置</p>
                    </div>
                </div>
                <span class="setting-arrow">›</span>
            </div>
            <div class="setting-item" onclick="showThemeSettings()">
                <div class="setting-left">
                    <div class="setting-icon">🎨</div>
                    <div class="setting-info">
                        <h3>主题设置</h3>
                        <p>切换外观主题</p>
                    </div>
                </div>
                <span class="setting-arrow">›</span>
            </div>
            <div class="setting-item" onclick="showDataSettings()">
                <div class="setting-left">
                    <div class="setting-icon">☁️</div>
                    <div class="setting-info">
                        <h3>数据同步</h3>
                        <p>备份和恢复数据</p>
                    </div>
                </div>
                <span class="setting-arrow">›</span>
            </div>
            <div class="setting-item" onclick="showAbout()">
                <div class="setting-left">
                    <div class="setting-icon">ℹ️</div>
                    <div class="setting-info">
                        <h3>关于</h3>
                        <p>版本信息和反馈</p>
                    </div>
                </div>
                <span class="setting-arrow">›</span>
            </div>
        </div>
    </div>
    
    <!-- 底部导航 -->
    <nav class="bottom-nav">
        <div class="nav-item active" data-page="bookshelf-page">
            <i>📚</i>
            <span>书架</span>
        </div>
        <div class="nav-item" data-page="discover-page">
            <i>🔍</i>
            <span>发现</span>
        </div>
        <div class="nav-item" data-page="sources-page">
            <i>🔌</i>
            <span>书源</span>
        </div>
        <div class="nav-item" data-page="stats-page">
            <i>📊</i>
            <span>统计</span>
        </div>
        <div class="nav-item" data-page="settings-page">
            <i>⚙️</i>
            <span>设置</span>
        </div>
    </nav>
    
    <!-- 阅读器 -->
    <div class="reader-page" id="reader">
        <div class="reader-header">
            <button class="icon-btn" onclick="closeReader()">←</button>
            <span class="reader-title" id="reader-title">章节标题</span>
            <button class="icon-btn" onclick="toggleChapterList()">☰</button>
        </div>
        <div class="reader-content" id="reader-content">
            <h2>第一章 示例章节</h2>
            {SAMPLE_CONTENT}
        </div>
        <div class="reader-toolbar">
            <button class="reader-btn" onclick="prevChapter()">上一章</button>
            <button class="reader-btn" onclick="showReaderSettings()">设置</button>
            <button class="reader-btn" onclick="nextChapter()">下一章</button>
        </div>
    </div>
    
    <!-- 章节列表 -->
    <div class="overlay" id="chapter-overlay" onclick="toggleChapterList()"></div>
    <div class="chapter-list" id="chapter-list">
        <div class="chapter-header">
            <h3>章节目录</h3>
            <button class="icon-btn" onclick="toggleChapterList()">✕</button>
        </div>
        <div class="chapter-list-content" id="chapter-list-content"></div>
    </div>
    
    <!-- Toast提示 -->
    <div class="toast" id="toast"></div>

    <script>
        // 书籍数据
        const booksData = {json.dumps(SAMPLE_BOOKS, ensure_ascii=False)};
        
        // 应用数据
        let appData = {{
            bookshelf: [],
            sources: [
                {{ name: '笔趣阁', url: 'biquge.com', enabled: true }},
                {{ name: '起点中文', url: 'qidian.com', enabled: true }},
                {{ name: '番茄小说', url: 'fanqie.com', enabled: false }},
            ],
            settings: {{ fontSize: 18, theme: 'dark' }},
            stats: {{ books: 3, chapters: 15, time: 8, words: 25 }}
        }};
        
        // 当前阅读状态
        let currentBook = null;
        let currentChapter = 0;
        
        // Toast提示
        function showToast(message) {{
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2000);
        }}
        
        // 初始化
        document.addEventListener('DOMContentLoaded', function() {{
            initApp();
        }});
        
        function initApp() {{
            loadData();
            
            if (appData.bookshelf.length === 0) {{
                appData.bookshelf = booksData.filter(b => b.category === 'reading');
                saveData();
            }}
            
            renderBookshelf('all');
            renderDiscover();
            renderSources();
            updateStats();
            
            bindNavigation();
            bindCategoryTabs();
            
            document.getElementById('search-input')?.addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') searchBooks();
            }});
        }}
        
        function bindNavigation() {{
            document.querySelectorAll('.nav-item').forEach(item => {{
                item.addEventListener('click', function() {{
                    const pageId = this.dataset.page;
                    showPage(pageId);
                    document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
                    this.classList.add('active');
                }});
            }});
        }}
        
        function showPage(pageId) {{
            document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
            document.getElementById(pageId).classList.add('active');
            window.scrollTo(0, 0);
        }}
        
        function bindCategoryTabs() {{
            document.querySelectorAll('.category-tabs').forEach(tabs => {{
                tabs.querySelectorAll('.category-tab').forEach(tab => {{
                    tab.addEventListener('click', function() {{
                        tabs.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
                        this.classList.add('active');
                        if (tabs.closest('#bookshelf-page')) {{
                            renderBookshelf(this.dataset.category);
                        }}
                    }});
                }});
            }});
        }}
        
        function renderBookshelf(category) {{
            const grid = document.getElementById('bookshelf-grid');
            const empty = document.getElementById('empty-bookshelf');
            
            let books = appData.bookshelf;
            if (category !== 'all') {{
                books = books.filter(b => b.category === category);
            }}
            
            if (books.length === 0) {{
                grid.innerHTML = '';
                empty.style.display = 'block';
                return;
            }}
            
            empty.style.display = 'none';
            grid.innerHTML = books.map(book => `
                <div class="book-card" onclick="openBook('${{book.id}}')">
                    <img src="${{book.cover}}" alt="${{book.name}}" class="book-cover">
                    <div class="book-title">${{book.name}}</div>
                    <div class="book-author">${{book.author}}</div>
                    ${{book.progress > 0 ? `<div class="book-progress">已读 ${{book.progress}}%</div>` : ''}}
                </div>
            `).join('');
        }}
        
        function renderDiscover() {{
            const grid = document.getElementById('discover-grid');
            grid.innerHTML = booksData.map(book => `
                <div class="book-card" onclick="addToBookshelf('${{book.id}}')">
                    <img src="${{book.cover}}" alt="${{book.name}}" class="book-cover">
                    <div class="book-title">${{book.name}}</div>
                    <div class="book-author">${{book.author}}</div>
                </div>
            `).join('');
        }}
        
        function renderSources() {{
            const list = document.getElementById('source-list');
            list.innerHTML = appData.sources.map((source, index) => `
                <div class="source-item">
                    <div class="source-info">
                        <h3>${{source.name}}</h3>
                        <p>${{source.url}}</p>
                    </div>
                    <div class="source-toggle ${{source.enabled ? 'active' : ''}}" onclick="toggleSource(${{index}})"></div>
                </div>
            `).join('');
        }}
        
        // 搜索书籍（调用后端API）
        async function searchBooks() {{
            const keyword = document.getElementById('search-input').value.trim();
            if (!keyword) {{
                showToast('请输入搜索关键词');
                return;
            }}
            
            const grid = document.getElementById('discover-grid');
            grid.innerHTML = '<div class="loading"><div class="loading-spinner"></div></div>';
            
            try {{
                // 调用后端API搜索
                const response = await fetch(`/api/search?q=${{encodeURIComponent(keyword)}}`);
                const data = await response.json();
                
                if (data.books && data.books.length > 0) {{
                    grid.innerHTML = data.books.map(book => `
                        <div class="book-card" onclick="addToBookshelfFromSearch(${{JSON.stringify(book).replace(/"/g, '&quot;')}})">
                            <img src="${{book.cover || 'https://via.placeholder.com/150x200/333/fff?text=No+Cover'}}" alt="${{book.name}}" class="book-cover">
                            <div class="book-title">${{book.name}}</div>
                            <div class="book-author">${{book.author || '未知作者'}}</div>
                        </div>
                    `).join('');
                }} else {{
                    grid.innerHTML = `
                        <div class="empty-state" style="grid-column: 1/-1;">
                            <div style="font-size: 48px; margin-bottom: 15px;">🔍</div>
                            <p>未找到相关书籍</p>
                        </div>
                    `;
                }}
            }} catch (error) {{
                console.error('Search error:', error);
                // 降级到本地搜索
                const results = booksData.filter(b => 
                    b.name.includes(keyword) || b.author.includes(keyword)
                );
                
                if (results.length === 0) {{
                    grid.innerHTML = `
                        <div class="empty-state" style="grid-column: 1/-1;">
                            <div style="font-size: 48px; margin-bottom: 15px;">🔍</div>
                            <p>未找到相关书籍</p>
                        </div>
                    `;
                }} else {{
                    grid.innerHTML = results.map(book => `
                        <div class="book-card" onclick="addToBookshelf('${{book.id}}')">
                            <img src="${{book.cover}}" alt="${{book.name}}" class="book-cover">
                            <div class="book-title">${{book.name}}</div>
                            <div class="book-author">${{book.author}}</div>
                        </div>
                    `).join('');
                }}
            }}
        }}
        
        function toggleSource(index) {{
            appData.sources[index].enabled = !appData.sources[index].enabled;
            renderSources();
            saveData();
        }}
        
        function refreshSources() {{
            showToast('正在刷新书源...');
            renderSources();
        }}
        
        // 打开书籍
        async function openBook(bookId) {{
            currentBook = booksData.find(b => b.id === bookId) || appData.bookshelf.find(b => b.id === bookId);
            if (!currentBook) return;
            
            currentChapter = 0;
            document.getElementById('reader-title').textContent = currentBook.name;
            document.getElementById('reader').classList.add('active');
            document.body.style.overflow = 'hidden';
            
            // 如果有真实URL，尝试从后端获取章节
            if (currentBook.url) {{
                await loadChaptersFromAPI(currentBook.url, currentBook.source);
            }} else {{
                loadChapter(0);
                renderChapterList();
            }}
        }}
        
        // 从API加载章节
        async function loadChaptersFromAPI(bookUrl, sourceName) {{
            try {{
                const response = await fetch(`/api/chapters?url=${{encodeURIComponent(bookUrl)}}&source=${{encodeURIComponent(sourceName)}}`);
                const data = await response.json();
                
                if (data.chapters && data.chapters.length > 0) {{
                    currentBook.chapters = data.chapters;
                    loadChapter(0);
                    renderChapterList();
                }} else {{
                    loadChapter(0);
                    renderChapterList();
                }}
            }} catch (error) {{
                console.error('Load chapters error:', error);
                loadChapter(0);
                renderChapterList();
            }}
        }}
        
        // 加载章节内容
        async function loadChapter(index) {{
            if (!currentBook || !currentBook.chapters[index]) return;
            
            currentChapter = index;
            const chapter = currentBook.chapters[index];
            
            // 显示加载中
            document.getElementById('reader-content').innerHTML = `
                <h2>${{chapter.title}}</h2>
                <div class="loading"><div class="loading-spinner"></div></div>
            `;
            
            // 如果有真实URL，从API获取内容
            if (chapter.url) {{
                try {{
                    const response = await fetch(`/api/content?url=${{encodeURIComponent(chapter.url)}}&source=${{encodeURIComponent(currentBook.source)}}`);
                    const data = await response.json();
                    
                    if (data.content) {{
                        document.getElementById('reader-content').innerHTML = `
                            <h2>${{chapter.title}}</h2>
                            ${{data.content}}
                        `;
                    }} else {{
                        document.getElementById('reader-content').innerHTML = `
                            <h2>${{chapter.title}}</h2>
                            <p>内容加载失败，请稍后重试</p>
                        `;
                    }}
                }} catch (error) {{
                    console.error('Load content error:', error);
                    document.getElementById('reader-content').innerHTML = `
                        <h2>${{chapter.title}}</h2>
                        <p>内容加载失败</p>
                    `;
                }}
            }} else {{
                // 使用示例内容
                document.getElementById('reader-content').innerHTML = `
                    <h2>${{chapter.title}}</h2>
                    {SAMPLE_CONTENT}
                `;
            }}
            
            // 更新章节列表高亮
            document.querySelectorAll('.chapter-item').forEach((item, i) => {{
                item.classList.toggle('active', i === index);
            }});
        }}
        
        function renderChapterList() {{
            if (!currentBook) return;
            
            const content = document.getElementById('chapter-list-content');
            content.innerHTML = currentBook.chapters.map((ch, index) => `
                <div class="chapter-item ${{index === currentChapter ? 'active' : ''}}" onclick="selectChapter(${{index}})">
                    ${{index + 1}}. ${{ch.title}}
                </div>
            `).join('');
        }}
        
        function selectChapter(index) {{
            loadChapter(index);
            toggleChapterList();
        }}
        
        function prevChapter() {{
            if (currentChapter > 0) {{
                loadChapter(currentChapter - 1);
            }} else {{
                showToast('已经是第一章了');
            }}
        }}
        
        function nextChapter() {{
            if (currentBook && currentChapter < currentBook.chapters.length - 1) {{
                loadChapter(currentChapter + 1);
            }} else {{
                showToast('已经是最后一章了');
            }}
        }}
        
        function closeReader() {{
            document.getElementById('reader').classList.remove('active');
            document.body.style.overflow = '';
            currentBook = null;
        }}
        
        function toggleChapterList() {{
            document.getElementById('chapter-list').classList.toggle('active');
            document.getElementById('chapter-overlay').classList.toggle('active');
        }}
        
        function addToBookshelf(bookId) {{
            const book = booksData.find(b => b.id === bookId);
            if (!book) return;
            
            if (appData.bookshelf.find(b => b.id === bookId)) {{
                showToast('《' + book.name + '》已在书架中');
                return;
            }}
            
            appData.bookshelf.push({{...book, progress: 0, category: 'reading'}});
            saveData();
            showToast('《' + book.name + '》已添加到书架');
        }}
        
        function addToBookshelfFromSearch(book) {{
            if (!book || !book.name) return;
            
            // 生成唯一ID
            book.id = 'search_' + Date.now();
            
            if (appData.bookshelf.find(b => b.name === book.name && b.author === book.author)) {{
                showToast('《' + book.name + '》已在书架中');
                return;
            }}
            
            appData.bookshelf.push({{...book, progress: 0, category: 'reading'}});
            saveData();
            showToast('《' + book.name + '》已添加到书架');
        }}
        
        function showSearch() {{
            showPage('discover-page');
            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
            document.querySelector('[data-page="discover-page"]').classList.add('active');
            document.getElementById('search-input').focus();
        }}
        
        function showAddBook() {{
            showSearch();
        }}
        
        function updateStats() {{
            document.getElementById('stat-books').textContent = appData.stats.books;
            document.getElementById('stat-chapters').textContent = appData.stats.chapters;
            document.getElementById('stat-time').textContent = appData.stats.time;
            document.getElementById('stat-words').textContent = appData.stats.words;
        }}
        
        function showReadingSettings() {{ showToast('阅读设置：字体大小、背景颜色、翻页效果'); }}
        function showDownloadSettings() {{ showToast('下载管理：自动下载、缓存清理'); }}
        function showThemeSettings() {{ showToast('主题设置：深色/浅色模式'); }}
        function showDataSettings() {{ showToast('数据同步：备份和恢复'); }}
        function showReaderSettings() {{ showToast('阅读器设置'); }}
        function showAbout() {{ showToast('佩宇Reader v2.1 - 支持书源解析'); }}
        
        function saveData() {{
            localStorage.setItem('peiyu_reader_data', JSON.stringify(appData));
        }}
        
        function loadData() {{
            const data = localStorage.getItem('peiyu_reader_data');
            if (data) {{
                appData = JSON.parse(data);
            }}
        }}
    </script>
</body>
</html>"""
    return html_content

# API端点
@app.get("/api/status")
async def status():
    """API状态检查"""
    sources = load_book_sources()
    return {
        "status": "running",
        "version": "2.1.0",
        "name": "佩宇Reader",
        "features": ["bookshelf", "reader", "search", "sources", "stats", "settings", "source_parsing"],
        "books_count": len(SAMPLE_BOOKS),
        "sources_count": len(sources)
    }

@app.get("/api/books")
async def get_books():
    """获取书籍列表"""
    return {
        "books": SAMPLE_BOOKS,
        "count": len(SAMPLE_BOOKS)
    }

@app.get("/api/book/{{book_id}}")
async def get_book(book_id: str):
    """获取单本书籍详情"""
    book = next((b for b in SAMPLE_BOOKS if b["id"] == book_id), None)
    if book:
        return book
    return JSONResponse(status_code=404, content={"error": "书籍不存在"})

@app.get("/api/sources")
async def get_sources():
    """获取书源列表"""
    sources = load_book_sources()
    return {
        "sources": sources,
        "count": len(sources)
    }

# 书源解析API
@app.get("/api/search")
async def search_books(q: str = Query(..., description="搜索关键词")):
    """从书源搜索书籍"""
    try:
        # 尝试使用书源解析器搜索
        sources_file = os.path.join(current_dir, '..', 'sources', 'book_sources.json')
        if os.path.exists(sources_file):
            from source_parser import BookSourceManager
            manager = BookSourceManager(sources_file)
            results = manager.search_all(q)
            if results:
                return {"books": results, "count": len(results), "source": "live"}
    except Exception as e:
        print(f"Live search error: {e}")
    
    # 降级到示例数据搜索
    results = [b for b in SAMPLE_BOOKS if q.lower() in b["name"].lower() or q.lower() in b["author"].lower()]
    return {"books": results, "count": len(results), "source": "sample"}

@app.get("/api/chapters")
async def get_chapters(url: str = Query(..., description="书籍URL"), source: str = Query(..., description="书源名称")):
    """获取章节列表"""
    try:
        sources_file = os.path.join(current_dir, '..', 'sources', 'book_sources.json')
        if os.path.exists(sources_file):
            from source_parser import BookSourceManager
            manager = BookSourceManager(sources_file)
            parser = manager.get_parser(source)
            if parser:
                chapters = parser.get_chapters(url)
                if chapters:
                    return {"chapters": chapters, "count": len(chapters)}
    except Exception as e:
        print(f"Get chapters error: {e}")
    
    return JSONResponse(status_code=404, content={"error": "无法获取章节列表"})

@app.get("/api/content")
async def get_content(url: str = Query(..., description="章节URL"), source: str = Query(..., description="书源名称")):
    """获取章节内容"""
    try:
        sources_file = os.path.join(current_dir, '..', 'sources', 'book_sources.json')
        if os.path.exists(sources_file):
            from source_parser import BookSourceManager
            manager = BookSourceManager(sources_file)
            parser = manager.get_parser(source)
            if parser:
                content = parser.get_content(url)
                if content:
                    return {"content": content}
    except Exception as e:
        print(f"Get content error: {e}")
    
    return JSONResponse(status_code=404, content={"error": "无法获取章节内容"})
