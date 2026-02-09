"""
佩宇Reader - Vercel Serverless部署入口
精简版Web服务，移除不兼容的依赖
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json

# 创建FastAPI应用
app = FastAPI(
    title="佩宇Reader",
    description="AI智能阅读器 - Web版",
    version="2.0.0"
)

# 静态文件和模板
static_dir = project_root / "web" / "static"
templates_dir = project_root / "web" / "static"

# 挂载静态文件
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 加载书源
def load_book_sources():
    """加载书源配置"""
    sources_file = project_root / "sources" / "book_sources.json"
    if sources_file.exists():
        with open(sources_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

@app.get("/", response_class=HTMLResponse)
async def root():
    """首页"""
    index_file = static_dir / "index.html"
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            return f.read()
    return """
    <!DOCTYPE html>
    <html>
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
            }
            .feature-icon {
                font-size: 2rem;
                margin-bottom: 10px;
            }
            .status {
                margin-top: 2rem;
                padding: 15px 30px;
                background: rgba(0,212,255,0.1);
                border-radius: 25px;
                border: 1px solid rgba(0,212,255,0.3);
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✨ 佩宇Reader</h1>
            <p class="subtitle">AI智能阅读器 - Web版</p>
            
            <div class="features">
                <div class="feature-card">
                    <div class="feature-icon">📚</div>
                    <h3>海量书源</h3>
                    <p>支持Legado格式书源</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🤖</div>
                    <h3>AI推荐</h3>
                    <p>智能个性化推荐</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <h3>阅读统计</h3>
                    <p>数据化阅读分析</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🔊</div>
                    <h3>语音朗读</h3>
                    <p>TTS真人语音</p>
                </div>
            </div>
            
            <div class="status">
                <span class="status-dot"></span>
                服务运行正常 | 版本 2.0.0
            </div>
            
            <p style="margin-top: 2rem; color: #666;">
                完整功能请使用桌面版或等待Web版功能完善
            </p>
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
        "features": ["book_source", "ai_recommendation", "tts", "analytics"]
    }

@app.get("/api/sources")
async def get_sources():
    """获取书源列表"""
    sources = load_book_sources()
    return {"sources": sources, "count": len(sources)}

# Vercel handler
handler = app
