"""
佩宇Reader - Vercel Serverless部署入口
精简版Web服务
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import json
import os

# 创建FastAPI应用
app = FastAPI(
    title="佩宇Reader",
    description="AI智能阅读器 - Web版",
    version="2.0.0"
)

# 加载书源
def load_book_sources():
    """加载书源配置"""
    try:
        # Vercel环境下文件路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sources_file = os.path.join(current_dir, '..', 'sources', 'book_sources.json')
        
        if os.path.exists(sources_file):
            with open(sources_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading sources: {e}")
    return []

@app.get("/", response_class=HTMLResponse)
async def root():
    """首页"""
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>佩宇Reader - AI智能阅读器</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                min-height: 100vh;
                color: #fff;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                text-align: center;
            }
            h1 {
                font-size: 3rem;
                margin-bottom: 1rem;
                background: linear-gradient(45deg, #00d4ff, #7b2cbf);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .subtitle {
                font-size: 1.2rem;
                color: #a0a0a0;
                margin-bottom: 2rem;
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 2rem 0;
            }
            .feature-card {
                background: rgba(255,255,255,0.05);
                border-radius: 12px;
                padding: 20px;
                border: 1px solid rgba(255,255,255,0.1);
                transition: transform 0.3s;
            }
            .feature-card:hover {
                transform: translateY(-5px);
                background: rgba(255,255,255,0.08);
            }
            .feature-icon {
                font-size: 2.5rem;
                margin-bottom: 15px;
            }
            .feature-card h3 {
                font-size: 1.2rem;
                margin-bottom: 8px;
                color: #00d4ff;
            }
            .feature-card p {
                color: #888;
                font-size: 0.9rem;
            }
            .status {
                margin-top: 2rem;
                padding: 15px 30px;
                background: rgba(0,212,255,0.1);
                border-radius: 25px;
                border: 1px solid rgba(0,212,255,0.3);
                display: inline-block;
            }
            .status-dot {
                display: inline-block;
                width: 10px;
                height: 10px;
                background: #00ff88;
                border-radius: 50%;
                margin-right: 10px;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            .links {
                margin-top: 2rem;
            }
            .links a {
                color: #00d4ff;
                text-decoration: none;
                margin: 0 15px;
                padding: 8px 16px;
                border: 1px solid rgba(0,212,255,0.3);
                border-radius: 20px;
                transition: all 0.3s;
            }
            .links a:hover {
                background: rgba(0,212,255,0.1);
            }
            footer {
                margin-top: 3rem;
                color: #666;
                font-size: 0.85rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✨ 佩宇Reader</h1>
            <p class="subtitle">AI智能阅读器 - Web版 v2.0</p>
            
            <div class="features">
                <div class="feature-card">
                    <div class="feature-icon">📚</div>
                    <h3>海量书源</h3>
                    <p>支持Legado格式书源，内置多源</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🤖</div>
                    <h3>AI推荐</h3>
                    <p>智能个性化书籍推荐</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <h3>阅读统计</h3>
                    <p>数据化阅读分析</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🔊</div>
                    <h3>语音朗读</h3>
                    <p>TTS真人语音合成</p>
                </div>
            </div>
            
            <div class="status">
                <span class="status-dot"></span>
                🟢 服务运行正常
            </div>
            
            <div class="links">
                <a href="/api/status">API状态</a>
                <a href="/api/sources">书源列表</a>
                <a href="https://github.com/11223456789/peiyu" target="_blank">GitHub</a>
            </div>
            
            <footer>
                <p>完整功能请使用桌面版 CLI 版本</p>
                <p style="margin-top: 10px;">© 2025 佩宇Reader | Powered by FastAPI & Vercel</p>
            </footer>
        </div>
    </body>
    </html>
    """

@app.get("/api/status")
async def status():
    """API状态检查"""
    return {
        "status": "running",
        "version": "2.0.0",
        "name": "佩宇Reader",
        "description": "AI智能阅读器",
        "features": ["book_source", "ai_recommendation", "tts", "analytics"],
        "endpoints": {
            "/": "首页",
            "/api/status": "状态检查",
            "/api/sources": "书源列表"
        }
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

# Vercel handler
handler = app
