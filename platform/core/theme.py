"""统一视觉风格：参考杜克大学官网的设计语言（深蓝、留白、卡片、流动感）。"""

DUKE_BLUE = "#012169"
DUKE_BLUE_LIGHT = "#00539B"
DUKE_ACCENT = "#C8102E"      # 杜克红，用于强调
INK = "#1A1A1A"
MUTED = "#5A6472"
SURFACE = "#FFFFFF"
CANVAS = "#F7F9FC"

CSS = f"""
<style>
/* ---------- 基础排版 ---------- */
html, body, [class*="css"] {{
    font-family: -apple-system, "SF Pro Text", "Helvetica Neue",
                 "PingFang SC", "Hiragino Sans GB", sans-serif;
    color: {INK};
}}
.stApp {{
    background:
      radial-gradient(1200px 600px at 12% -8%, rgba(1,33,105,0.10), transparent 60%),
      radial-gradient(900px 500px at 95% 0%, rgba(0,83,155,0.08), transparent 55%),
      {CANVAS};
}}
.block-container {{ padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1250px; }}

/* ---------- 标题：细体 + 蓝色强调条 ---------- */
h1, h2, h3 {{ letter-spacing: -0.02em; color: {DUKE_BLUE}; font-weight: 700; }}
h1 {{ font-size: 2.15rem !important; line-height: 1.2 !important; }}
h1::after {{
    content: ""; display: block; width: 68px; height: 4px; margin-top: 12px;
    background: linear-gradient(90deg, {DUKE_BLUE}, {DUKE_BLUE_LIGHT});
    border-radius: 2px;
}}
h2 {{ font-size: 1.35rem !important; margin-top: 1.6rem !important; }}
h3 {{ font-size: 1.05rem !important; color: {DUKE_BLUE_LIGHT}; }}

/* ---------- 侧边栏 ---------- */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {DUKE_BLUE} 0%, #01306b 55%, #012a5c 100%);
    border-right: none;
}}
section[data-testid="stSidebar"] * {{ color: #EAF0FA !important; }}
section[data-testid="stSidebar"] h3 {{ color: #FFFFFF !important; }}
section[data-testid="stSidebar"] a {{
    border-radius: 10px; transition: background 0.18s ease, transform 0.18s ease;
    padding: 6px 10px !important;
}}
section[data-testid="stSidebar"] a:hover {{
    background: rgba(255,255,255,0.14); transform: translateX(3px);
}}
section[data-testid="stSidebar"] a[aria-current="page"] {{
    background: rgba(255,255,255,0.20);
    box-shadow: inset 3px 0 0 {DUKE_ACCENT};
}}

/* ---------- 指标卡：白底 + 悬浮 ---------- */
div[data-testid="stMetric"] {{
    background: {SURFACE}; border: 1px solid rgba(1,33,105,0.10);
    border-radius: 14px; padding: 16px 18px;
    box-shadow: 0 2px 10px rgba(1,33,105,0.06);
    transition: transform 0.22s cubic-bezier(.2,.7,.3,1), box-shadow 0.22s ease;
}}
div[data-testid="stMetric"]:hover {{
    transform: translateY(-3px);
    box-shadow: 0 10px 26px rgba(1,33,105,0.14);
}}
div[data-testid="stMetricValue"] {{ color: {DUKE_BLUE}; font-weight: 700; }}

/* ---------- 标签页：下划线滑动感 ---------- */
button[data-baseweb="tab"] {{
    font-weight: 600; color: {MUTED}; transition: color 0.18s ease;
}}
button[data-baseweb="tab"]:hover {{ color: {DUKE_BLUE_LIGHT}; }}
button[data-baseweb="tab"][aria-selected="true"] {{ color: {DUKE_BLUE}; }}
div[data-baseweb="tab-highlight"] {{ background-color: {DUKE_ACCENT}; height: 3px; }}

/* ---------- 按钮 ---------- */
.stButton > button {{
    background: linear-gradient(135deg, {DUKE_BLUE}, {DUKE_BLUE_LIGHT});
    color: #fff; border: none; border-radius: 10px; font-weight: 600;
    padding: 0.5rem 1.3rem;
    transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}}
.stButton > button:hover {{
    transform: translateY(-2px); filter: brightness(1.08);
    box-shadow: 0 8px 20px rgba(1,33,105,0.28);
}}

/* ---------- 表格与展开面板 ---------- */
div[data-testid="stDataFrame"] {{
    border-radius: 12px; overflow: hidden;
    border: 1px solid rgba(1,33,105,0.10);
}}
details, div[data-testid="stExpander"] {{
    border-radius: 12px !important;
    border: 1px solid rgba(1,33,105,0.10) !important;
    background: {SURFACE};
}}

/* ---------- 提示框：左侧色条 ---------- */
div[data-testid="stAlert"] {{
    border-radius: 12px; border-left: 4px solid {DUKE_BLUE_LIGHT};
    background: {SURFACE};
}}

/* ---------- 代码块 ---------- */
pre {{ border-radius: 10px !important; }}

/* ---------- 首屏 Hero ---------- */
.dku-hero {{
    background: linear-gradient(120deg, {DUKE_BLUE} 0%, #013a86 45%, {DUKE_BLUE_LIGHT} 100%);
    border-radius: 20px; padding: 40px 44px; margin-bottom: 26px; color: #fff;
    box-shadow: 0 16px 40px rgba(1,33,105,0.26);
    position: relative; overflow: hidden;
}}
.dku-hero::after {{
    content: ""; position: absolute; right: -80px; top: -80px;
    width: 320px; height: 320px; border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,0.22), transparent 70%);
}}
.dku-hero h1 {{ color: #fff !important; margin: 0 0 10px 0; font-size: 2.1rem !important; }}
.dku-hero h1::after {{ background: {DUKE_ACCENT}; }}
.dku-hero p {{ color: rgba(255,255,255,0.92); font-size: 1.02rem; margin: 6px 0 0 0; }}
.dku-hero .tagline {{ font-size: 0.86rem; letter-spacing: 0.14em;
    text-transform: uppercase; color: rgba(255,255,255,0.75); margin-bottom: 6px; }}

/* ---------- 卡片 ---------- */
.dku-card {{
    background: {SURFACE}; border-radius: 16px; padding: 20px 22px; height: 100%;
    border: 1px solid rgba(1,33,105,0.10);
    box-shadow: 0 2px 12px rgba(1,33,105,0.06);
    transition: transform 0.24s cubic-bezier(.2,.7,.3,1), box-shadow 0.24s ease,
                border-color 0.24s ease;
}}
.dku-card:hover {{
    transform: translateY(-4px);
    border-color: rgba(0,83,155,0.35);
    box-shadow: 0 16px 34px rgba(1,33,105,0.16);
}}
.dku-card h4 {{ color: {DUKE_BLUE}; margin: 0 0 8px 0; font-size: 1.02rem; }}
.dku-card p {{ color: {MUTED}; font-size: 0.9rem; line-height: 1.55; margin: 0; }}
.dku-card .idx {{
    display:inline-block; font-size: 0.74rem; font-weight: 700; letter-spacing: 0.1em;
    color: {DUKE_BLUE_LIGHT}; background: rgba(0,83,155,0.10);
    border-radius: 999px; padding: 3px 10px; margin-bottom: 10px;
}}
.dku-src {{ color: {MUTED}; font-size: 0.82rem; margin-top: 10px; }}
.dku-rule {{ height: 1px; background: linear-gradient(90deg, rgba(1,33,105,0.18), transparent);
    margin: 30px 0; border: none; }}
</style>
"""


def hero(tagline: str, title: str, subtitle: str) -> str:
    return (f'<div class="dku-hero"><div class="tagline">{tagline}</div>'
            f'<h1>{title}</h1><p>{subtitle}</p></div>')


def card(index: str, title: str, body: str, source: str = "") -> str:
    src = f'<div class="dku-src">📄 {source}</div>' if source else ""
    return (f'<div class="dku-card"><span class="idx">{index}</span>'
            f'<h4>{title}</h4><p>{body}</p>{src}</div>')
