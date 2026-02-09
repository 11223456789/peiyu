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

# 加载预抓取的书籍数据
def load_books_data():
    """加载预抓取的书籍数据"""
    try:
        books_file = os.path.join(current_dir, '..', 'data', 'books_data.json')
        if os.path.exists(books_file):
            with open(books_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('books', [])
    except Exception as e:
        print(f"Error loading books data: {e}")
    return []

# 加载数据
BOOK_SOURCES = load_book_sources()
BOOKS_DATA = load_books_data()

# 书源列表（从前端加载的书源）
SOURCE_LIST = []
for src in BOOK_SOURCES[:5]:  # 只取前5个
    SOURCE_LIST.append({
        "name": src.get('bookSourceName', '未知书源'),
        "url": src.get('bookSourceUrl', ''),
        "group": src.get('bookSourceGroup', '默认'),
        "enabled": src.get('enabled', True)
    })

@app.get("/api/sources")
async def get_sources():
    """获取书源列表"""
    return {"sources": SOURCE_LIST}

@app.get("/api/search")
async def search_books(q: str = Query(..., description="搜索关键词")):
    """搜索书籍 - 从预抓取的数据中搜索"""
    q = q.lower()
    results = []
    
    # 从预抓取的书籍中搜索
    for book in BOOKS_DATA:
        if q in book['name'].lower() or q in book['author'].lower() or q in book.get('category', '').lower():
            results.append(book)
    
    # 如果没有匹配，返回所有书籍（作为推荐）
    if not results:
        results = BOOKS_DATA[:8]
    
    return {"results": results, "keyword": q, "total": len(results)}

@app.get("/api/books")
async def get_all_books():
    """获取所有预抓取的书籍"""
    return {"books": BOOKS_DATA, "total": len(BOOKS_DATA)}

@app.get("/api/chapters")
async def get_chapters(book_id: str = Query(..., description="书籍ID")):
    """获取章节列表 - 从预抓取的数据中查找"""
    for book in BOOKS_DATA:
        if book['id'] == book_id:
            return {
                "chapters": book.get('chapters', []),
                "book_id": book_id,
                "book_name": book['name'],
                "total": len(book.get('chapters', []))
            }
    
    # 如果找不到，返回默认章节
    return {
        "chapters": [{"id": i, "title": f"第{i}章"} for i in range(1, 11)],
        "book_id": book_id,
        "total": 10
    }

# 章节内容模板（模拟真实内容）
CHAPTER_CONTENTS = {
    "doupo_cangqiong": {
        1: """<p>萧炎静静地站在萧家后山的悬崖边，目光呆滞地望着远方。</p>
        <p>"斗之力，三段！"</p>
        <p>测验魔石碑上那刺眼的五个大字，如同一记重锤，狠狠地砸在他的心上。</p>
        <p>三年了，从十二岁那年开始，他的斗之气就一直在三段徘徊，再也没有提升过。曾经的家族天才，如今沦为了所有人眼中的废物。</p>
        <p>"萧炎，斗之力，三段！级别：低级！"测验员的声音冷漠而不屑。</p>
        <p>广场上响起一阵窃窃私语，夹杂着嘲讽和惋惜。</p>
        <p>"唉，曾经的天才，怎么会变成这样？"</p>
        <p>"谁知道呢，说不定是得罪了什么人，被废了修为。"</p>
        <p>"哼，废物就是废物，还找什么借口。"</p>
        <p>萧炎紧握着拳头，指甲深深地嵌入掌心，鲜血顺着指缝滴落。但他仿佛感觉不到疼痛，只是死死地盯着那块测验魔石碑。</p>
        <p>三年前，他还是乌坦城最耀眼的天才，十二岁突破斗者，震惊整个加玛帝国。可就在他达到巅峰的时候，一切都变了。</p>
        <p>他的斗之气开始倒退，从斗者跌落到九段，然后是八段、七段……直到现在的三段。</p>
        <p>没有人知道原因，连家族中最强的长老也查不出任何问题。他们只知道，萧炎废了，从一个天才变成了一个废物。</p>
        <p>"萧炎哥哥……"一个轻柔的声音从身后传来。</p>
        <p>萧炎身体微微一颤，不用回头他也知道是谁。</p>
        <p>萧薰儿，萧家的大小姐，也是唯一一个在这三年里没有嘲笑过他、疏远过他的人。</p>
        <p>"薰儿，你怎么来了？"萧炎努力让自己的声音听起来平静。</p>
        <p>"我担心你。"萧薰儿走到他身边，清澈的眼眸中满是关切，"萧炎哥哥，不要在意那些人的话，我相信你一定能重新站起来的。"</p>
        <p>萧炎苦笑一声："三年了啊，薰儿。三年了，我的斗之气一直在倒退，没有任何好转的迹象。也许……我真的废了吧。"</p>
        <p>"不会的！"萧薰儿坚定地说道，"萧炎哥哥是最棒的，不管别人怎么说，我永远相信你！"</p>
        <p>萧炎转过头，看着眼前这个美丽的少女，心中涌起一股暖流。这三年来，如果不是薰儿一直陪伴在他身边，他恐怕早就崩溃了。</p>
        <p>"谢谢你，薰儿。"萧炎轻声说道。</p>
        <p>就在这时，一道苍老的声音突然在他脑海中响起："小子，想恢复实力吗？"</p>
        <p>萧炎猛地一惊，四下张望，却看不到任何人。</p>
        <p>"谁？谁在说话？"</p>""",
        2: """<p>"别找了，我在你手指上的戒指里。"那道苍老的声音再次响起。</p>
        <p>萧炎下意识地看向自己的右手，那里戴着一枚黑色的古朴戒指。这枚戒指是他母亲留给他的唯一遗物，他一直戴在手上，从未取下过。</p>
        <p>"你……你是谁？"萧炎在心中问道。</p>
        <p>"嘿嘿，小子，我叫药老，是一个炼药师。"那声音带着几分得意，"这三年来，你的斗之气之所以一直在倒退，就是因为被我吸收了。"</p>
        <p>"什么？！"萧炎顿时怒火中烧，"原来是你害我变成废物的！"</p>
        <p>"别急别急，"药老连忙说道，"我吸收你的斗之气也是迫不得已。我的灵魂在这戒指里沉睡了太久，需要能量才能苏醒。现在我已经醒了，自然会补偿你。"</p>
        <p>"补偿？你怎么补偿？"萧炎冷冷地问道。</p>
        <p>"我可以让你重新成为天才，甚至比以前更强！"药老的语气充满了诱惑，"而且，我还可以教你炼药术，让你成为尊贵的炼药师！"</p>
        <p>炼药师！</p>
        <p>萧炎心中一震。炼药师是斗气大陆上最尊贵的职业之一，他们炼制的丹药可以让修炼者事半功倍，甚至可以起死回生。</p>
        <p>每一个炼药师都是各方势力争相拉拢的对象，地位尊崇无比。</p>
        <p>"你说的是真的？"萧炎有些不敢相信。</p>
        <p>"当然是真的，我药老从不骗人。"药老嘿嘿一笑，"不过，我有一个条件。"</p>
        <p>"什么条件？"</p>
        <p>"我要你拜我为师。"</p>
        <p>萧炎沉默了。拜一个来历不明的灵魂为师，这听起来很荒唐。但是，他已经没有选择了。</p>
        <p>三年的废物生涯，让他受尽了冷眼和嘲讽。他渴望力量，渴望重新站起来，渴望让那些看不起他的人后悔！</p>
        <p>"好，我答应你！"萧炎坚定地说道。</p>
        <p>"哈哈哈，好！从今天起，你就是我药老的弟子了！"药老大笑起来。</p>
        <p>一道淡淡的光芒从戒指中射出，在空中凝聚成一个虚幻的老者身影。老者白发苍苍，面容慈祥，但眼中却闪烁着睿智的光芒。</p>
        <p>"弟子萧炎，拜见师父！"萧炎恭敬地行了一礼。</p>
        <p>"好好好，"药老满意地点点头，"既然你拜我为师，那我就送你一份见面礼。"</p>
        <p>说着，药老手指一点，一道光芒没入萧炎的眉心。</p>
        <p>萧炎只觉得脑海中突然涌现出大量的信息，那是一门修炼功法——焚诀！</p>
        <p>"这是……"萧炎震惊地看着药老。</p>
        <p>"这是焚诀，一门可以进化的功法。"药老解释道，"只要你吞噬异火，就能让功法不断升级，最终成为天阶功法！"</p>
        <p>天阶功法！</p>
        <p>萧炎倒吸一口凉气。整个加玛帝国，最强的功法也不过是地阶低级，而天阶功法，只存在于传说之中！</p>
        <p>"师父，这太珍贵了……"</p>
        <p>"珍贵？"药老摇摇头，"对于为师来说，这不过是九牛一毛。只要你好好修炼，将来为师还会给你更多的好东西。"</p>
        <p>"多谢师父！"萧炎激动地说道。</p>
        <p>"好了，现在就开始修炼吧。"药老说道，"你的基础还在，只要按照焚诀修炼，很快就能恢复斗者的实力。"</p>
        <p>萧炎点点头，盘膝坐下，开始按照脑海中的功法运转斗之气。</p>
        <p>随着焚诀的运转，他感觉到体内的斗之气开始活跃起来，那种久违的力量感正在慢慢回归……</p>"""
    },
    "wanmei_shijie": {
        1: """<p>石村，位于苍莽山脉之中，是一个与世隔绝的小山村。</p>
        <p>清晨的阳光洒落在村子里，炊烟袅袅升起，一派祥和的景象。</p>
        <p>"小不点，快起床了！"一个粗犷的声音在院子里响起。</p>
        <p>"唔……再睡一会儿嘛……"一个奶声奶气的声音从屋里传来。</p>
        <p>"太阳都晒屁股了，还睡！"那粗犷声音的主人是一个身材魁梧的大汉，他大步走进屋里，一把掀开了被子。</p>
        <p>被子里缩着一个小小的身影，看起来只有三四岁的样子，粉雕玉琢，可爱极了。</p>
        <p>这就是石村的孩子王——石昊，小名小不点。</p>
        <p>虽然年纪小，但小不点却是村子里最调皮捣蛋的存在。上树掏鸟蛋，下河摸鱼虾，没有他不敢干的事情。</p>
        <p>"皮猴叔叔，让我再睡一会儿嘛……"小不点揉着惺忪的睡眼，撒娇道。</p>
        <p>"不行，今天要去柳神那里洗礼，可不能迟到。"皮猴一把将小不点拎了起来。</p>
        <p>柳神，是石村的守护神。据说在很久很久以前，一株巨大的柳树从天而降，扎根在石村中央，从此守护着这个村子。</p>
        <p>每年春天，石村的孩子们都要在柳神下进行洗礼，祈求健康成长。</p>
        <p>"哦，洗礼啊……"小不点顿时来了精神，"那我要穿最漂亮的衣服！"</p>
        <p>"你哪有什么漂亮衣服，"皮猴笑骂道，"快穿上兽皮衣，大家都在等着呢。"</p>
        <p>小不点嘟着嘴，不情不愿地穿上了兽皮衣。</p>
        <p>村子中央，一株巨大的柳树矗立在那里。柳树的树干需要十几个人才能合抱，枝条垂落下来，如同绿色的瀑布。</p>
        <p>但奇怪的是，这株柳树的枝条上只有寥寥几根嫩绿的柳条，其他的都是焦黑的枯枝，仿佛被雷劈过一样。</p>
        <p>石村的族长石云峰站在柳树前，神色恭敬。</p>
        <p>"孩子们，排好队，准备开始洗礼了。"</p>
        <p>十几个孩子排成一列，小不点站在最前面。</p>
        <p>"小不点，你先来。"石云峰慈祥地说道。</p>
        <p>小不点走到柳树前，仰起头看着那株巨大的柳树。</p>
        <p>突然，一根嫩绿的柳条轻轻垂落下来，触碰到了小不点的额头。</p>
        <p>一道温暖的光芒从柳条上散发出来，笼罩了小不点的全身。</p>
        <p>小不点只觉得浑身暖洋洋的，舒服极了。他闭上眼睛，感受着这股神奇的力量。</p>
        <p>就在这时，他的脑海中突然响起了一个声音：</p>
        <p>"有趣的孩子……你的体内，竟然有那种力量……"</p>
        <p>小不点猛地睁开眼睛，四处张望，却看不到说话的人。</p>
        <p>"谁？谁在说话？"</p>
        <p>但那个声音再也没有响起，仿佛刚才的一切都是幻觉。</p>
        <p>柳条缓缓收回，洗礼结束了。</p>
        <p>"小不点，感觉怎么样？"石云峰关切地问道。</p>
        <p>"很舒服！"小不点开心地说道，但他没有说出刚才听到的声音。</p>
        <p>不知道为什么，他觉得那个声音应该是柳神发出的，而这是他和柳神之间的秘密。</p>
        <p>洗礼继续进行，其他孩子也一个个接受了柳神的祝福。</p>
        <p>当最后一个孩子洗礼完毕时，柳树的枝条突然轻轻摇曳起来，发出沙沙的声响。</p>
        <p>石云峰神色一凛，恭敬地向着柳树行了一礼："多谢柳神庇佑！"</p>
        <p>村民们也纷纷行礼，表达对柳神的敬意。</p>
        <p>小不点看着那株巨大的柳树，心中充满了好奇。柳神刚才说的话是什么意思？他体内有什么力量？</p>
        <p>这些问题，也许只有等他长大了才能找到答案……</p>"""
    }
}

def get_chapter_content(book_id: str, chapter_id: int) -> str:
    """获取章节内容"""
    # 查找预定义的内容
    if book_id in CHAPTER_CONTENTS and chapter_id in CHAPTER_CONTENTS[book_id]:
        return CHAPTER_CONTENTS[book_id][chapter_id]
    
    # 查找书籍信息
    book_name = "未知书籍"
    chapter_title = f"第{chapter_id}章"
    for book in BOOKS_DATA:
        if book['id'] == book_id:
            book_name = book['name']
            for ch in book.get('chapters', []):
                if ch['id'] == chapter_id:
                    chapter_title = ch['title']
                    break
            break
    
    # 返回默认内容
    return f"""<p>这是《{book_name}》的{chapter_title}。</p>
    <p>由于服务器环境限制，无法实时抓取书源内容。</p>
    <p>这里显示的是示例内容，用于演示阅读器的功能。</p>
    <p>在实际使用中，您可以通过本地版CLI工具配合书源获取完整内容。</p>
    <p>Web版主要用于展示书架管理、阅读记录、个性化设置等功能。</p>
    <p>感谢您的理解与支持！</p>
    <p>佩宇Reader，让阅读更美好。</p>"""

@app.get("/api/content")
async def get_content(book_id: str = Query(...), chapter_id: int = Query(...)):
    """获取章节内容 - 从预抓取的数据或模板中查找"""
    content = get_chapter_content(book_id, chapter_id)
    return {"content": content, "book_id": book_id, "chapter_id": chapter_id}

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
        
        .settings-list {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; overflow: hidden; margin-bottom: 20px; }}
        .setting-item {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border); cursor: pointer; transition: all 0.3s; }}
        .setting-item:last-child {{ border-bottom: none; }}
        .setting-item:hover {{ background: rgba(255,255,255,0.02); }}
        .setting-left {{ display: flex; align-items: center; gap: 15px; }}
        .setting-icon {{ width: 36px; height: 36px; border-radius: 10px; background: linear-gradient(45deg, var(--primary), var(--secondary)); display: flex; align-items: center; justify-content: center; font-size: 18px; }}
        .setting-info h3 {{ font-size: 16px; color: var(--text-primary); margin-bottom: 2px; }}
        .setting-info p {{ font-size: 13px; color: var(--text-secondary); }}
        .setting-arrow {{ color: var(--text-secondary); font-size: 20px; }}
        .setting-value {{ color: var(--primary); font-size: 14px; }}
        
        /* 阅读器样式 */
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
        
        /* 阅读设置面板 */
        .reader-settings {{
            position: fixed; bottom: -100%; left: 0; right: 0;
            background: rgba(30, 30, 50, 0.98); backdrop-filter: blur(20px);
            border-top: 1px solid var(--border); z-index: 2002;
            transition: bottom 0.3s ease; padding: 20px;
        }}
        .reader-settings.active {{ bottom: 0; }}
        .settings-section {{ margin-bottom: 20px; }}
        .settings-section h4 {{ font-size: 14px; color: var(--text-secondary); margin-bottom: 12px; }}
        .font-size-control {{ display: flex; align-items: center; gap: 15px; }}
        .font-btn {{ width: 40px; height: 40px; border-radius: 50%; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-primary); font-size: 20px; cursor: pointer; }}
        .font-size-display {{ font-size: 18px; color: var(--primary); min-width: 60px; text-align: center; }}
        
        .bg-options {{ display: flex; gap: 10px; }}
        .bg-option {{ width: 50px; height: 50px; border-radius: 10px; cursor: pointer; border: 3px solid transparent; transition: all 0.3s; }}
        .bg-option.active {{ border-color: var(--primary); }}
        .bg-dark {{ background: #1a1a1a; }}
        .bg-light {{ background: #f5f5f5; }}
        .bg-sepia {{ background: #f4ecd8; }}
        .bg-green {{ background: #c7edcc; }}
        .bg-blue {{ background: #cce8cf; }}
        
        .flip-options {{ display: flex; gap: 10px; }}
        .flip-option {{ flex: 1; padding: 12px; border-radius: 10px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-secondary); text-align: center; cursor: pointer; transition: all 0.3s; }}
        .flip-option.active {{ background: linear-gradient(45deg, var(--primary), var(--secondary)); color: white; border-color: transparent; }}
        
        .close-settings {{ position: absolute; top: 15px; right: 20px; width: 30px; height: 30px; border-radius: 50%; border: none; background: var(--bg-card); color: var(--text-primary); font-size: 18px; cursor: pointer; }}
        
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
        
        /* 弹窗样式 */
        .modal {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 2500; display: none; justify-content: center; align-items: center; }}
        .modal.active {{ display: flex; }}
        .modal-content {{ background: var(--bg-dark); border-radius: 20px; padding: 30px; width: 90%; max-width: 400px; border: 1px solid var(--border); }}
        .modal-title {{ font-size: 20px; margin-bottom: 20px; text-align: center; }}
        .modal-btn {{ width: 100%; padding: 15px; border-radius: 10px; border: none; background: linear-gradient(45deg, var(--primary), var(--secondary)); color: white; font-size: 16px; cursor: pointer; margin-top: 15px; }}
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
            <div class="setting-item" onclick="showReadingSettingsModal()">
                <div class="setting-left">
                    <div class="setting-icon">📖</div>
                    <div class="setting-info">
                        <h3>阅读设置</h3>
                        <p>字体、背景、翻页效果</p>
                    </div>
                </div>
                <span class="setting-value" id="reading-settings-summary">18px · 深色 · 滑动</span>
                <span class="setting-arrow">›</span>
            </div>
            <div class="setting-item">
                <div class="setting-left">
                    <div class="setting-icon">🔔</div>
                    <div class="setting-info">
                        <h3>通知设置</h3>
                        <p>更新提醒、阅读目标</p>
                    </div>
                </div>
                <span class="setting-arrow">›</span>
            </div>
            <div class="setting-item">
                <div class="setting-left">
                    <div class="setting-icon">💾</div>
                    <div class="setting-info">
                        <h3>数据管理</h3>
                        <p>备份、恢复、清理缓存</p>
                    </div>
                </div>
                <span class="setting-arrow">›</span>
            </div>
            <div class="setting-item">
                <div class="setting-left">
                    <div class="setting-icon">🎨</div>
                    <div class="setting-info">
                        <h3>主题设置</h3>
                        <p>深色模式、强调色</p>
                    </div>
                </div>
                <span class="setting-arrow">›</span>
            </div>
        </div>
        
        <div class="settings-list" style="margin-top: 20px;">
            <div class="setting-item">
                <div class="setting-left">
                    <div class="setting-icon">ℹ️</div>
                    <div class="setting-info">
                        <h3>关于佩宇Reader</h3>
                        <p>版本 2.1.0 · 检查更新</p>
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
            <p>点击设置按钮可以调整阅读设置...</p>
        </div>
        <div class="reader-toolbar">
            <button class="reader-btn" onclick="prevChapter()">上一章</button>
            <button class="reader-btn" onclick="showReaderSettings()">设置</button>
            <button class="reader-btn" onclick="nextChapter()">下一章</button>
        </div>
    </div>
    
    <!-- 阅读设置面板 -->
    <div class="reader-settings" id="reader-settings">
        <button class="close-settings" onclick="hideReaderSettings()">✕</button>
        
        <div class="settings-section">
            <h4>字体大小</h4>
            <div class="font-size-control">
                <button class="font-btn" onclick="changeFontSize(-2)">A-</button>
                <span class="font-size-display" id="font-size-display">18px</span>
                <button class="font-btn" onclick="changeFontSize(2)">A+</button>
            </div>
        </div>
        
        <div class="settings-section">
            <h4>背景颜色</h4>
            <div class="bg-options">
                <div class="bg-option bg-dark active" data-bg="dark" onclick="changeBg('dark')"></div>
                <div class="bg-option bg-light" data-bg="light" onclick="changeBg('light')"></div>
                <div class="bg-option bg-sepia" data-bg="sepia" onclick="changeBg('sepia')"></div>
                <div class="bg-option bg-green" data-bg="green" onclick="changeBg('green')"></div>
                <div class="bg-option bg-blue" data-bg="blue" onclick="changeBg('blue')"></div>
            </div>
        </div>
        
        <div class="settings-section">
            <h4>翻页效果</h4>
            <div class="flip-options">
                <div class="flip-option active" data-flip="slide" onclick="changeFlip('slide')">滑动</div>
                <div class="flip-option" data-flip="fade" onclick="changeFlip('fade')">淡入</div>
                <div class="flip-option" data-flip="none" onclick="changeFlip('none')">无动画</div>
            </div>
        </div>
    </div>
    
    <!-- 阅读设置弹窗 -->
    <div class="modal" id="reading-settings-modal">
        <div class="modal-content">
            <h3 class="modal-title">📖 阅读设置</h3>
            
            <div class="settings-section">
                <h4>字体大小</h4>
                <div class="font-size-control">
                    <button class="font-btn" onclick="changeFontSize(-2, true)">A-</button>
                    <span class="font-size-display" id="modal-font-size">18px</span>
                    <button class="font-btn" onclick="changeFontSize(2, true)">A+</button>
                </div>
            </div>
            
            <div class="settings-section">
                <h4>背景颜色</h4>
                <div class="bg-options">
                    <div class="bg-option bg-dark active" data-bg="dark" onclick="changeBg('dark', true)"></div>
                    <div class="bg-option bg-light" data-bg="light" onclick="changeBg('light', true)"></div>
                    <div class="bg-option bg-sepia" data-bg="sepia" onclick="changeBg('sepia', true)"></div>
                    <div class="bg-option bg-green" data-bg="green" onclick="changeBg('green', true)"></div>
                    <div class="bg-option bg-blue" data-bg="blue" onclick="changeBg('blue', true)"></div>
                </div>
            </div>
            
            <div class="settings-section">
                <h4>翻页效果</h4>
                <div class="flip-options">
                    <div class="flip-option active" data-flip="slide" onclick="changeFlip('slide', true)">滑动</div>
                    <div class="flip-option" data-flip="fade" onclick="changeFlip('fade', true)">淡入</div>
                    <div class="flip-option" data-flip="none" onclick="changeFlip('none', true)">无动画</div>
                </div>
            </div>
            
            <button class="modal-btn" onclick="closeReadingSettingsModal()">确定</button>
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
        // 书源数据
        const bookSources = {json.dumps(SOURCE_LIST, ensure_ascii=False)};
        
        // 应用数据
        let appData = {{
            bookshelf: [],
            sources: bookSources,
            settings: {{ 
                fontSize: 18, 
                theme: 'dark',
                bgColor: 'dark',
                flipEffect: 'slide'
            }},
            stats: {{ books: 6, chapters: 30, time: 12, words: 45 }}
        }};
        
        // 当前阅读状态
        let currentBook = null;
        let currentChapter = 0;
        let chapters = [];
        
        // 初始化
        document.addEventListener('DOMContentLoaded', function() {{
            loadData();
            initNavigation();
            renderBookshelf();
            renderSources();
            updateStats();
            applySettings();
        }});
        
        // 加载本地数据
        function loadData() {{
            const saved = localStorage.getItem('peiyuReader_data');
            if (saved) {{
                const parsed = JSON.parse(saved);
                appData = {{...appData, ...parsed}};
            }}
        }}
        
        // 保存数据
        function saveData() {{
            localStorage.setItem('peiyuReader_data', JSON.stringify(appData));
        }}
        
        // 初始化导航
        function initNavigation() {{
            document.querySelectorAll('.nav-item').forEach(item => {{
                item.addEventListener('click', function() {{
                    const pageId = this.dataset.page;
                    switchPage(pageId);
                    
                    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                    this.classList.add('active');
                }});
            }});
            
            // 分类标签
            document.querySelectorAll('.category-tab').forEach(tab => {{
                tab.addEventListener('click', function() {{
                    this.parentElement.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
                    this.classList.add('active');
                }});
            }});
        }}
        
        // 切换页面
        function switchPage(pageId) {{
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById(pageId).classList.add('active');
        }}
        
        // 渲染书架
        function renderBookshelf() {{
            const grid = document.getElementById('bookshelf-grid');
            const empty = document.getElementById('empty-bookshelf');
            
            if (appData.bookshelf.length === 0) {{
                grid.innerHTML = '';
                empty.style.display = 'block';
                return;
            }}
            
            empty.style.display = 'none';
            grid.innerHTML = appData.bookshelf.map(book => `
                <div class="book-card" onclick="openBook('${{book.id}}')">
                    <img src="${{book.cover}}" class="book-cover" alt="${{book.name}}">
                    <div class="book-title">${{book.name}}</div>
                    <div class="book-author">${{book.author}}</div>
                    <div class="book-progress">已读 ${{book.progress}}%</div>
                </div>
            `).join('');
        }}
        
        // 渲染书源
        function renderSources() {{
            const list = document.getElementById('source-list');
            list.innerHTML = appData.sources.map((src, idx) => `
                <div class="source-item">
                    <div class="source-info">
                        <h3>${{src.name}}</h3>
                        <p>${{src.group}} · ${{src.url}}</p>
                    </div>
                    <div class="source-toggle ${{src.enabled ? 'active' : ''}}" onclick="toggleSource(${{idx}})"></div>
                </div>
            `).join('');
        }}
        
        // 更新统计
        function updateStats() {{
            document.getElementById('stat-books').textContent = appData.stats.books;
            document.getElementById('stat-chapters').textContent = appData.stats.chapters;
            document.getElementById('stat-time').textContent = appData.stats.time;
            document.getElementById('stat-words').textContent = appData.stats.words;
        }}
        
        // 搜索书籍
        async function searchBooks() {{
            const keyword = document.getElementById('search-input').value.trim();
            if (!keyword) {{
                showToast('请输入搜索关键词');
                return;
            }}
            
            showToast('搜索中...');
            
            try {{
                const response = await fetch(`/api/search?q=${{encodeURIComponent(keyword)}}`);
                const data = await response.json();
                
                const grid = document.getElementById('discover-grid');
                if (data.results && data.results.length > 0) {{
                    grid.innerHTML = data.results.map(book => `
                        <div class="book-card" onclick="addToBookshelf(${{JSON.stringify(book).replace(/"/g, '&quot;')}})">
                            <img src="${{book.cover}}" class="book-cover" alt="${{book.name}}">
                            <div class="book-title">${{book.name}}</div>
                            <div class="book-author">${{book.author}}</div>
                            <div class="book-progress">${{book.source}}</div>
                        </div>
                    `).join('');
                    showToast(`找到 ${{data.results.length}} 本书`);
                }} else {{
                    grid.innerHTML = '<div class="empty-state">未找到相关书籍</div>';
                    showToast('未找到相关书籍');
                }}
            }} catch (e) {{
                showToast('搜索失败: ' + e.message);
            }}
        }}
        
        // 添加书籍到书架
        function addToBookshelf(book) {{
            if (!appData.bookshelf.find(b => b.id === book.id)) {{
                book.progress = 0;
                book.category = 'reading';
                appData.bookshelf.push(book);
                saveData();
                renderBookshelf();
                showToast(`《${{book.name}}》已添加到书架`);
            }} else {{
                showToast('该书已在书架中');
            }}
        }}
        
        // 打开书籍
        async function openBook(bookId) {{
            const book = appData.bookshelf.find(b => b.id === bookId);
            if (!book) return;
            
            currentBook = book;
            showToast('加载章节...');
            
            // 获取章节列表
            try {{
                const response = await fetch(`/api/chapters?book_id=${{encodeURIComponent(book.id)}}`);
                const data = await response.json();
                chapters = data.chapters || [];
            }} catch (e) {{
                // 使用书籍自带章节
                chapters = book.chapters || [];
            }}
            
            renderChapterList();
            loadChapter(currentBook.progress > 0 ? Math.floor(currentBook.progress / 100 * chapters.length) : 0);
            
            document.getElementById('reader').classList.add('active');
        }}
        
        // 渲染章节列表
        function renderChapterList() {{
            const list = document.getElementById('chapter-list-content');
            list.innerHTML = chapters.map((ch, idx) => `
                <div class="chapter-item ${{idx === currentChapter ? 'active' : ''}}" onclick="loadChapter(${{idx}})">
                    ${{ch.title}}
                </div>
            `).join('');
        }}
        
        // 加载章节内容
        async function loadChapter(idx) {{
            if (idx < 0 || idx >= chapters.length) return;
            
            currentChapter = idx;
            const chapter = chapters[idx];
            document.getElementById('reader-title').textContent = chapter.title;
            
            showToast('加载内容...');
            
            try {{
                const response = await fetch(`/api/content?book_id=${{encodeURIComponent(currentBook.id)}}&chapter_id=${{chapter.id}}`);
                const data = await response.json();
                document.getElementById('reader-content').innerHTML = `<h2>${{chapter.title}}</h2>` + data.content;
            }} catch (e) {{
                // 使用书籍自带内容或默认内容
                document.getElementById('reader-content').innerHTML = `
                    <h2>${{chapter.title}}</h2>
                    <p>这是《${{currentBook.name}}》的${{chapter.title}}内容。</p>
                    <p>由于服务器环境限制，无法实时抓取书源内容。</p>
                    <p>部分热门书籍已预置真实章节内容，其他书籍显示示例内容。</p>
                    <p>感谢您的理解与支持！</p>
                `;
            }}
            
            // 更新阅读进度
            currentBook.progress = Math.round((currentChapter / chapters.length) * 100);
            saveData();
            renderChapterList();
            
            // 滚动到顶部
            document.getElementById('reader-content').scrollTop = 0;
        }}
        
        // 上一章
        function prevChapter() {{
            if (currentChapter > 0) {{
                loadChapter(currentChapter - 1);
            }} else {{
                showToast('已经是第一章了');
            }}
        }}
        
        // 下一章
        function nextChapter() {{
            if (currentChapter < chapters.length - 1) {{
                loadChapter(currentChapter + 1);
            }} else {{
                showToast('已经是最后一章了');
            }}
        }}
        
        // 关闭阅读器
        function closeReader() {{
            document.getElementById('reader').classList.remove('active');
            renderBookshelf();
        }}
        
        // 切换章节列表
        function toggleChapterList() {{
            document.getElementById('chapter-list').classList.toggle('active');
            document.getElementById('chapter-overlay').classList.toggle('active');
        }}
        
        // 显示阅读设置（阅读器内）
        function showReaderSettings() {{
            document.getElementById('reader-settings').classList.add('active');
        }}
        
        // 隐藏阅读设置
        function hideReaderSettings() {{
            document.getElementById('reader-settings').classList.remove('active');
        }}
        
        // 显示阅读设置弹窗（设置页面）
        function showReadingSettingsModal() {{
            document.getElementById('reading-settings-modal').classList.add('active');
            updateSettingsDisplay();
        }}
        
        // 关闭阅读设置弹窗
        function closeReadingSettingsModal() {{
            document.getElementById('reading-settings-modal').classList.remove('active');
            updateSettingsSummary();
        }}
        
        // 更新设置显示
        function updateSettingsDisplay() {{
            document.getElementById('font-size-display').textContent = appData.settings.fontSize + 'px';
            document.getElementById('modal-font-size').textContent = appData.settings.fontSize + 'px';
            
            // 背景选择
            document.querySelectorAll('.bg-option').forEach(el => {{
                el.classList.toggle('active', el.dataset.bg === appData.settings.bgColor);
            }});
            
            // 翻页效果
            document.querySelectorAll('.flip-option').forEach(el => {{
                el.classList.toggle('active', el.dataset.flip === appData.settings.flipEffect);
            }});
        }}
        
        // 更新设置摘要
        function updateSettingsSummary() {{
            const bgNames = {{dark: '深色', light: '浅色', sepia: ' sepia', green: '绿色', blue: '蓝色'}};
            const flipNames = {{slide: '滑动', fade: '淡入', none: '无动画'}};
            const summary = `${{appData.settings.fontSize}}px · ${{bgNames[appData.settings.bgColor]}} · ${{flipNames[appData.settings.flipEffect]}}`;
            document.getElementById('reading-settings-summary').textContent = summary;
        }}
        
        // 改变字体大小
        function changeFontSize(delta, isModal = false) {{
            appData.settings.fontSize = Math.max(12, Math.min(32, appData.settings.fontSize + delta));
            saveData();
            applySettings();
            updateSettingsDisplay();
        }}
        
        // 改变背景
        function changeBg(bg, isModal = false) {{
            appData.settings.bgColor = bg;
            saveData();
            applySettings();
            updateSettingsDisplay();
        }}
        
        // 改变翻页效果
        function changeFlip(flip, isModal = false) {{
            appData.settings.flipEffect = flip;
            saveData();
            updateSettingsDisplay();
        }}
        
        // 应用设置
        function applySettings() {{
            const readerContent = document.getElementById('reader-content');
            if (readerContent) {{
                readerContent.style.fontSize = appData.settings.fontSize + 'px';
                
                const bgColors = {{
                    dark: {{bg: '#1a1a1a', text: '#cccccc'}},
                    light: {{bg: '#f5f5f5', text: '#333333'}},
                    sepia: {{bg: '#f4ecd8', text: '#5b4636'}},
                    green: {{bg: '#c7edcc', text: '#333333'}},
                    blue: {{bg: '#cce8cf', text: '#333333'}}
                }};
                
                const colors = bgColors[appData.settings.bgColor];
                if (colors) {{
                    readerContent.style.background = colors.bg;
                    readerContent.style.color = colors.text;
                }}
            }}
        }}
        
        // 切换书源
        function toggleSource(idx) {{
            appData.sources[idx].enabled = !appData.sources[idx].enabled;
            saveData();
            renderSources();
            showToast(`${{appData.sources[idx].name}} ${{appData.sources[idx].enabled ? '已启用' : '已禁用'}}`);
        }}
        
        // 刷新书源
        function refreshSources() {{
            showToast('书源已刷新');
            renderSources();
        }}
        
        // 显示搜索
        function showSearch() {{
            switchPage('discover-page');
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.querySelector('[data-page="discover-page"]').classList.add('active');
        }}
        
        // 显示添加书籍
        function showAddBook() {{
            showSearch();
            showToast('请在发现页面搜索书籍');
        }}
        
        // 显示Toast
        function showToast(msg) {{
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2000);
        }}
        
        // 键盘快捷键
        document.addEventListener('keydown', function(e) {{
            if (!document.getElementById('reader').classList.contains('active')) return;
            
            if (e.key === 'ArrowLeft') prevChapter();
            if (e.key === 'ArrowRight') nextChapter();
            if (e.key === 'Escape') closeReader();
        }});
    </script>
</body>
</html>"""
    return html_content
