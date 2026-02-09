"""
佩宇Reader - Vercel Serverless部署入口
"""
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
import json
import os

app = FastAPI(
    title="佩宇Reader",
    description="AI智能阅读器 - Web版",
    version="2.0.0"
)

# 加载书源
def load_book_sources():
    """加载书源配置"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sources_file = os.path.join(current_dir, '..', 'sources', 'book_sources.json')
        
        if os.path.exists(sources_file):
            with open(sources_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error: {e}")
    return []

# 示例书籍数据（实际应从书源获取）
SAMPLE_BOOKS = [
    {
        "id": "1",
        "name": "斗破苍穹",
        "author": "天蚕土豆",
        "cover": "https://via.placeholder.com/150x200/4a90e2/ffffff?text=斗破苍穹",
        "intro": "这里是斗气大陆，没有花俏艳丽的魔法，有的，仅仅是繁衍到巅峰的斗气！",
        "source": "笔趣阁",
        "chapters": [
            {"title": "第一章 陨落的天才", "url": "#"},
            {"title": "第二章 斗之气，三段！", "url": "#"},
            {"title": "第三章 客人", "url": "#"},
            {"title": "第四章 云岚宗", "url": "#"},
            {"title": "第五章 聚气散", "url": "#"},
        ]
    },
    {
        "id": "2",
        "name": "完美世界",
        "author": "辰东",
        "cover": "https://via.placeholder.com/150x200/e74c3c/ffffff?text=完美世界",
        "intro": "一粒尘可填海，一根草斩尽日月星辰，弹指间天翻地覆。",
        "source": "起点",
        "chapters": [
            {"title": "第一章 朝气蓬勃", "url": "#"},
            {"title": "第二章 柳神", "url": "#"},
            {"title": "第三章 药浴", "url": "#"},
            {"title": "第四章 宝术", "url": "#"},
            {"title": "第五章 凶兽", "url": "#"},
        ]
    },
    {
        "id": "3",
        "name": "遮天",
        "author": "辰东",
        "cover": "https://via.placeholder.com/150x200/27ae60/ffffff?text=遮天",
        "intro": "冰冷与黑暗并存的宇宙深处，九具庞大的龙尸拉着一口青铜古棺，亘古长存。",
        "source": "番茄小说",
        "chapters": [
            {"title": "第一章 星空中的青铜巨棺", "url": "#"},
            {"title": "第二章 荒古禁地", "url": "#"},
            {"title": "第三章 神泉", "url": "#"},
            {"title": "第四章 道经", "url": "#"},
            {"title": "第五章 妖帝坟冢", "url": "#"},
        ]
    },
    {
        "id": "4",
        "name": "凡人修仙传",
        "author": "忘语",
        "cover": "https://via.placeholder.com/150x200/f39c12/ffffff?text=凡人修仙传",
        "intro": "一个普通山村小子，偶然下进入到当地江湖小门派，成了一名记名弟子。",
        "source": "笔趣阁",
        "chapters": [
            {"title": "第一章 七玄门", "url": "#"},
            {"title": "第二章 墨大夫", "url": "#"},
            {"title": "第三章 长春功", "url": "#"},
            {"title": "第四章 炼气", "url": "#"},
            {"title": "第五章 出山", "url": "#"},
        ]
    },
    {
        "id": "5",
        "name": "仙逆",
        "author": "耳根",
        "cover": "https://via.placeholder.com/150x200/9b59b6/ffffff?text=仙逆",
        "intro": "顺为凡，逆则仙，只在心中一念间。",
        "source": "起点",
        "chapters": [
            {"title": "第一章 铁柱", "url": "#"},
            {"title": "第二章 恒岳派", "url": "#"},
            {"title": "第三章 入门", "url": "#"},
            {"title": "第四章 凝气", "url": "#"},
            {"title": "第五章 天逆", "url": "#"},
        ]
    },
    {
        "id": "6",
        "name": "我欲封天",
        "author": "耳根",
        "cover": "https://via.placeholder.com/150x200/1abc9c/ffffff?text=我欲封天",
        "intro": "我命如妖欲封天，踏破苍穹九重天。",
        "source": "番茄小说",
        "chapters": [
            {"title": "第一章 书生孟浩", "url": "#"},
            {"title": "第二章 靠山宗", "url": "#"},
            {"title": "第三章 造化", "url": "#"},
            {"title": "第四章 完美筑基", "url": "#"},
            {"title": "第五章 封天诀", "url": "#"},
        ]
    }
]

@app.get("/", response_class=HTMLResponse)
async def root():
    """首页 - 书籍列表"""
    books_html = ""
    for book in SAMPLE_BOOKS:
        books_html += f"""
        <div class="book-card" onclick="showBookDetail('{book['id']}')">
            <img src="{book['cover']}" alt="{book['name']}" class="book-cover">
            <div class="book-info">
                <h3 class="book-title">{book['name']}</h3>
                <p class="book-author">👤 {book['author']}</p>
                <p class="book-source">📚 {book['source']}</p>
                <p class="book-intro">{book['intro'][:60]}...</p>
            </div>
        </div>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>佩宇Reader - AI智能阅读器</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                min-height: 100vh;
                color: #fff;
            }}
            .header {{
                text-align: center;
                padding: 30px 20px;
                background: rgba(0,0,0,0.2);
            }}
            .header h1 {{
                font-size: 2.5rem;
                background: linear-gradient(45deg, #00d4ff, #7b2cbf);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 10px;
            }}
            .header p {{
                color: #888;
                font-size: 1rem;
            }}
            .nav {{
                display: flex;
                justify-content: center;
                gap: 20px;
                padding: 15px;
                background: rgba(0,0,0,0.1);
                flex-wrap: wrap;
            }}
            .nav a {{
                color: #00d4ff;
                text-decoration: none;
                padding: 8px 16px;
                border: 1px solid rgba(0,212,255,0.3);
                border-radius: 20px;
                transition: all 0.3s;
            }}
            .nav a:hover {{
                background: rgba(0,212,255,0.1);
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 30px 20px;
            }}
            .section-title {{
                font-size: 1.5rem;
                margin-bottom: 20px;
                color: #00d4ff;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .books-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
            }}
            .book-card {{
                background: rgba(255,255,255,0.05);
                border-radius: 12px;
                padding: 15px;
                border: 1px solid rgba(255,255,255,0.1);
                display: flex;
                gap: 15px;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .book-card:hover {{
                transform: translateY(-3px);
                background: rgba(255,255,255,0.08);
                border-color: rgba(0,212,255,0.3);
            }}
            .book-cover {{
                width: 80px;
                height: 110px;
                border-radius: 8px;
                object-fit: cover;
            }}
            .book-info {{
                flex: 1;
            }}
            .book-title {{
                font-size: 1.1rem;
                color: #fff;
                margin-bottom: 8px;
            }}
            .book-author, .book-source {{
                font-size: 0.85rem;
                color: #888;
                margin-bottom: 5px;
            }}
            .book-intro {{
                font-size: 0.8rem;
                color: #666;
                line-height: 1.4;
            }}
            .footer {{
                text-align: center;
                padding: 30px;
                color: #666;
                font-size: 0.85rem;
            }}
            /* 详情弹窗 */
            .modal {{
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
                z-index: 1000;
                overflow-y: auto;
            }}
            .modal-content {{
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                max-width: 800px;
                margin: 50px auto;
                padding: 30px;
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.1);
            }}
            .modal-header {{
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
            }}
            .modal-cover {{
                width: 120px;
                height: 160px;
                border-radius: 8px;
            }}
            .modal-info h2 {{
                color: #00d4ff;
                margin-bottom: 10px;
            }}
            .modal-info p {{
                color: #888;
                margin-bottom: 8px;
            }}
            .chapters-list {{
                max-height: 400px;
                overflow-y: auto;
            }}
            .chapter-item {{
                padding: 12px;
                border-bottom: 1px solid rgba(255,255,255,0.05);
                cursor: pointer;
                transition: all 0.2s;
            }}
            .chapter-item:hover {{
                background: rgba(0,212,255,0.1);
                padding-left: 20px;
            }}
            .close-btn {{
                position: absolute;
                top: 20px;
                right: 30px;
                font-size: 2rem;
                color: #fff;
                cursor: pointer;
                background: none;
                border: none;
            }}
            .read-btn {{
                background: linear-gradient(45deg, #00d4ff, #7b2cbf);
                color: #fff;
                border: none;
                padding: 12px 30px;
                border-radius: 25px;
                font-size: 1rem;
                cursor: pointer;
                margin-top: 15px;
            }}
            @media (max-width: 768px) {{
                .books-grid {{
                    grid-template-columns: 1fr;
                }}
                .modal-header {{
                    flex-direction: column;
                    align-items: center;
                    text-align: center;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>✨ 佩宇Reader</h1>
            <p>AI智能阅读器 - Web版 v2.0</p>
        </div>
        
        <div class="nav">
            <a href="/">📚 书架</a>
            <a href="/api/status">📊 状态</a>
            <a href="/api/sources">🔌 书源</a>
            <a href="https://github.com/11223456789/peiyu" target="_blank">GitHub</a>
        </div>
        
        <div class="container">
            <h2 class="section-title">📖 热门书籍</h2>
            <div class="books-grid">
                {books_html}
            </div>
        </div>
        
        <div class="footer">
            <p>💡 提示：点击书籍查看详情和章节列表</p>
            <p style="margin-top: 10px;">© 2025 佩宇Reader | Powered by FastAPI & Vercel</p>
        </div>
        
        <!-- 书籍详情弹窗 -->
        <div id="bookModal" class="modal">
            <div class="modal-content">
                <button class="close-btn" onclick="closeModal()">&times;</button>
                <div id="modalBody"></div>
            </div>
        </div>
        
        <script>
            const books = {json.dumps(SAMPLE_BOOKS, ensure_ascii=False)};
            
            function showBookDetail(bookId) {{
                const book = books.find(b => b.id === bookId);
                if (!book) return;
                
                let chaptersHtml = '';
                book.chapters.forEach((ch, index) => {{
                    chaptersHtml += `<div class="chapter-item" onclick="readChapter('${{book.name}}', '${{ch.title}}')">${{index + 1}}. ${{ch.title}}</div>`;
                }});
                
                document.getElementById('modalBody').innerHTML = `
                    <div class="modal-header">
                        <img src="${{book.cover}}" class="modal-cover" alt="${{book.name}}">
                        <div class="modal-info">
                            <h2>${{book.name}}</h2>
                            <p>👤 作者：${{book.author}}</p>
                            <p>📚 来源：${{book.source}}</p>
                            <p>📖 章节数：${{book.chapters.length}}章</p>
                            <p style="margin-top: 15px; color: #aaa;">${{book.intro}}</p>
                            <button class="read-btn" onclick="startReading('${{book.name}}')">📖 开始阅读</button>
                        </div>
                    </div>
                    <h3 style="color: #00d4ff; margin: 20px 0 15px;">📑 章节目录</h3>
                    <div class="chapters-list">
                        ${{chaptersHtml}}
                    </div>
                `;
                
                document.getElementById('bookModal').style.display = 'block';
            }}
            
            function closeModal() {{
                document.getElementById('bookModal').style.display = 'none';
            }}
            
            function readChapter(bookName, chapterTitle) {{
                alert(`📖 ${{bookName}}\\n\\n${{chapterTitle}}\\n\\n（演示模式：实际内容需要从书源获取）`);
            }}
            
            function startReading(bookName) {{
                alert(`📖 开始阅读《${{bookName}}》\\n\\n（演示模式：实际阅读功能需要后端书源解析支持）`);
            }}
            
            // 点击弹窗外部关闭
            window.onclick = function(event) {{
                const modal = document.getElementById('bookModal');
                if (event.target === modal) {{
                    modal.style.display = 'none';
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/api/status")
async def status():
    """API状态检查"""
    return {
        "status": "running",
        "version": "2.0.0",
        "name": "佩宇Reader",
        "books_count": len(SAMPLE_BOOKS),
        "features": ["book_list", "chapter_view", "book_source"]
    }

@app.get("/api/sources")
async def get_sources():
    """获取书源列表"""
    sources = load_book_sources()
    return {
        "sources": sources,
        "count": len(sources),
        "message": "书源加载成功" if sources else "暂无书源"
    }

@app.get("/api/books")
async def get_books():
    """获取书籍列表"""
    return {
        "books": SAMPLE_BOOKS,
        "count": len(SAMPLE_BOOKS)
    }

@app.get("/api/book/{book_id}")
async def get_book(book_id: str):
    """获取单本书籍详情"""
    book = next((b for b in SAMPLE_BOOKS if b["id"] == book_id), None)
    if book:
        return book
    return JSONResponse(status_code=404, content={"error": "书籍不存在"})
