"""
统一视觉系统 —— 干净、大气、克制
==================================
设计原则（参考 Canva 的简洁语言 + 杜克的学术气质）：
  1. 大量留白，元素之间呼吸感优先
  2. 用色克制：主色只用于强调，其余靠层级与间距
  3. 边框极细、阴影柔和，不用重色块
  4. 字号与字重建立层级，而不是靠颜色和图标
  5. 动效只用于反馈（悬浮、切换），不做装饰
"""

# ---------------- 设计令牌 ----------------
INK        = "#14171F"   # 正文
INK_SOFT   = "#5B6472"   # 次要文字
LINE       = "#E8ECF2"   # 细边框
CANVAS     = "#FBFCFE"   # 页面底色
SURFACE    = "#FFFFFF"   # 卡片
PRIMARY    = "#012169"   # 主色（杜克蓝）
PRIMARY_2  = "#1B4F9C"   # 主色浅阶
ACCENT     = "#C8102E"   # 强调（杜克红）
OK         = "#0F7B5F"
WARN       = "#B45309"

CSS = f"""
<style>
:root {{
  --ink:{INK}; --ink-soft:{INK_SOFT}; --line:{LINE}; --canvas:{CANVAS};
  --surface:{SURFACE}; --primary:{PRIMARY}; --primary2:{PRIMARY_2};
  --accent:{ACCENT}; --radius:14px;
}}

/* ---------- 基础 ---------- */
html, body, [class*="css"] {{
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI",
               "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  color: var(--ink);
  -webkit-font-smoothing: antialiased;
}}
.stApp {{ background: var(--canvas); }}
.block-container {{
  padding-top: 2.6rem; padding-bottom: 5rem;
  max-width: 1180px; line-height: 1.75;
}}
#MainMenu, footer, header [data-testid="stToolbar"] {{ visibility: hidden; }}

/* ---------- 标题层级 ---------- */
h1, h2, h3, h4 {{ color: var(--ink); font-weight: 650; letter-spacing: -0.015em; }}
h1 {{ font-size: 2.0rem !important; line-height: 1.25 !important; margin-bottom: .2rem !important; }}
h2 {{ font-size: 1.22rem !important; margin: 2.2rem 0 .7rem !important; }}
h3 {{ font-size: 1.02rem !important; margin: 1.4rem 0 .5rem !important; font-weight: 600; }}
p, li {{ color: var(--ink); }}
hr {{ border: none; border-top: 1px solid var(--line); margin: 2.4rem 0; }}

/* ---------- 侧边栏：浅色、干净 ---------- */
section[data-testid="stSidebar"] {{
  background: var(--surface);
  border-right: 1px solid var(--line);
}}
section[data-testid="stSidebar"] > div {{ padding-top: 1.4rem; }}
.side-brand {{ padding: .2rem .1rem 1.5rem; border-bottom: 1px solid var(--line); margin-bottom: 1rem; }}
.side-brand-title {{ font-size: 1.0rem; font-weight: 680; color: var(--primary); letter-spacing: -.01em; }}
.side-brand-sub {{ font-size: .74rem; color: var(--ink-soft); margin-top: .35rem; line-height: 1.5; }}
.side-foot {{ border-top: 1px solid var(--line); padding-top: .9rem; margin-top: 1rem; }}

section[data-testid="stSidebar"] a {{
  border-radius: 9px; padding: 7px 11px !important; margin: 1px 0;
  color: var(--ink) !important; font-size: .875rem;
  transition: background .15s ease, color .15s ease;
}}
section[data-testid="stSidebar"] a:hover {{ background: #F2F5FA; }}
section[data-testid="stSidebar"] a[aria-current="page"] {{
  background: #EEF3FB; color: var(--primary) !important; font-weight: 620;
}}
section[data-testid="stSidebar"] a[aria-current="page"] svg {{ color: var(--primary); }}
section[data-testid="stSidebar"] svg {{ color: var(--ink-soft); }}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ font-size: .8rem; }}

/* ---------- 指标：极简卡片 ---------- */
div[data-testid="stMetric"] {{
  background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius); padding: 18px 20px;
  transition: border-color .2s ease, box-shadow .2s ease;
}}
div[data-testid="stMetric"]:hover {{
  border-color: #D3DDEC; box-shadow: 0 6px 20px rgba(20,23,31,.06);
}}
div[data-testid="stMetricLabel"] p {{
  color: var(--ink-soft) !important; font-size: .78rem !important;
  letter-spacing: .01em; font-weight: 500;
}}
div[data-testid="stMetricValue"] {{
  color: var(--primary) !important; font-weight: 660 !important;
  font-size: 1.45rem !important; letter-spacing: -.02em;
}}

/* ---------- 标签页 ---------- */
button[data-baseweb="tab"] {{
  font-weight: 560; color: var(--ink-soft); font-size: .9rem;
  padding: 8px 2px; margin-right: 26px; transition: color .15s ease;
}}
button[data-baseweb="tab"]:hover {{ color: var(--ink); }}
button[data-baseweb="tab"][aria-selected="true"] {{ color: var(--primary); }}
div[data-baseweb="tab-highlight"] {{ background: var(--primary); height: 2px; }}
div[data-baseweb="tab-border"] {{ background: var(--line); }}

/* ---------- 按钮 ---------- */
.stButton > button, .stDownloadButton > button {{
  background: var(--primary); color: #fff; border: 1px solid var(--primary);
  border-radius: 9px; font-weight: 560; font-size: .88rem;
  padding: .48rem 1.05rem;
  transition: background .15s ease, transform .15s ease, box-shadow .15s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
  background: var(--primary2); border-color: var(--primary2);
  transform: translateY(-1px); box-shadow: 0 6px 16px rgba(1,33,105,.18);
}}
.stButton > button:disabled {{ background: #EDF0F5; border-color: #EDF0F5; color: #9AA3B2; }}

/* ---------- 输入控件 ---------- */
div[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input {{
  border-radius: 9px !important; border-color: var(--line) !important;
}}
div[data-testid="stSlider"] [role="slider"] {{ background: var(--primary); }}

/* ---------- 数据表 / 展开面板 ---------- */
div[data-testid="stDataFrame"] {{
  border: 1px solid var(--line); border-radius: 11px; overflow: hidden;
}}
div[data-testid="stExpander"] {{
  border: 1px solid var(--line) !important; border-radius: 11px !important;
  background: var(--surface); box-shadow: none !important;
}}
div[data-testid="stExpander"] summary {{ font-size: .9rem; font-weight: 560; }}
div[data-testid="stExpander"] summary:hover {{ color: var(--primary); }}

/* ---------- 提示条：细边 + 左侧色线 ---------- */
div[data-testid="stAlert"] {{
  border: 1px solid var(--line); border-left: 3px solid var(--primary2);
  border-radius: 10px; background: var(--surface); box-shadow: none;
}}
div[data-testid="stAlert"] p {{ font-size: .875rem; }}

/* ---------- 代码块 ---------- */
pre, code {{ border-radius: 9px !important; font-size: .84rem !important; }}
div[data-testid="stCode"] {{ border: 1px solid var(--line); border-radius: 10px; }}

/* ---------- 进度条 ---------- */
div[data-testid="stProgress"] > div > div {{ background: var(--line); }}
div[data-testid="stProgress"] > div > div > div {{ background: var(--primary); }}

/* ================= 自定义组件 ================= */

/* Hero：一整块浅色，不用重渐变 */
.hero {{
  padding: 8px 0 30px; border-bottom: 1px solid var(--line); margin-bottom: 34px;
}}
.hero .eyebrow {{
  font-size: .72rem; letter-spacing: .16em; text-transform: uppercase;
  color: var(--primary2); font-weight: 620; margin-bottom: 14px;
}}
.hero h1 {{ font-size: 2.25rem !important; margin: 0 0 14px 0 !important; max-width: 20ch; }}
.hero .lede {{
  font-size: 1.0rem; color: var(--ink-soft); max-width: 62ch; line-height: 1.7; margin: 0;
}}
.hero .rule {{
  width: 44px; height: 3px; background: var(--accent);
  border-radius: 2px; margin: 22px 0 0;
}}

/* 卡片：极简 */
.card {{
  background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius); padding: 22px 24px; height: 100%;
  transition: border-color .2s ease, box-shadow .2s ease, transform .2s ease;
}}
.card:hover {{
  border-color: #D3DDEC; box-shadow: 0 10px 28px rgba(20,23,31,.07);
  transform: translateY(-2px);
}}
.card .kicker {{
  font-size: .72rem; font-weight: 660; letter-spacing: .1em;
  color: var(--primary2); margin-bottom: 10px;
}}
.card h4 {{ margin: 0 0 9px 0; font-size: 1.0rem; font-weight: 640; }}
.card p {{ margin: 0; color: var(--ink-soft); font-size: .865rem; line-height: 1.65; }}
.card .src {{
  margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--line);
  font-size: .78rem; color: var(--ink-soft);
}}

/* 文献条目 */
.paper {{
  background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius); padding: 20px 24px; margin-bottom: 14px;
}}
.paper .meta {{
  font-size: .76rem; color: var(--ink-soft); letter-spacing: .02em; margin-bottom: 8px;
}}
.paper .meta .tag {{
  display: inline-block; padding: 2px 9px; border-radius: 999px;
  background: #EEF3FB; color: var(--primary); font-weight: 600; margin-right: 8px;
}}
.paper .meta .tag.warn {{ background: #FDF3E7; color: {WARN}; }}
.paper h4 {{ margin: 0 0 10px 0; font-size: 1.0rem; font-weight: 640; line-height: 1.45; }}
.paper .goal {{ color: var(--ink-soft); font-size: .87rem; line-height: 1.7; margin: 0 0 10px; }}
.paper .diff {{
  font-size: .84rem; color: {WARN}; background: #FDFAF5;
  border-left: 3px solid #E9C08A; border-radius: 0 8px 8px 0;
  padding: 10px 14px; line-height: 1.65;
}}
.paper .goal b, .paper .diff b {{ color: var(--ink); }}

/* 步骤状态点 */
.step-dot {{
  display: inline-block; width: 7px; height: 7px; border-radius: 50%;
  margin-right: 9px; vertical-align: middle;
}}
.dot-done {{ background: {OK}; }}
.dot-now  {{ background: {PRIMARY_2}; }}
.dot-todo {{ background: #CFD7E3; }}

/* 出错面板 */
.err-title {{ font-size: 1.05rem; font-weight: 640; color: {ACCENT}; margin-bottom: .4rem; }}

/* 分区小标题 */
.section-label {{
  font-size: .74rem; letter-spacing: .14em; text-transform: uppercase;
  color: var(--ink-soft); font-weight: 620; margin: 2.4rem 0 .9rem;
  padding-bottom: .55rem; border-bottom: 1px solid var(--line);
}}

/* 键值列表 */
.kv {{ margin: 0; }}
.kv .row {{
  display: flex; justify-content: space-between; gap: 20px;
  padding: 9px 0; border-bottom: 1px solid var(--line); font-size: .875rem;
}}
.kv .row:last-child {{ border-bottom: none; }}
.kv .k {{ color: var(--ink-soft); }}
.kv .v {{ font-weight: 600; }}
</style>
"""


def hero(eyebrow: str, title: str, lede: str) -> str:
    return (f'<div class="hero"><div class="eyebrow">{eyebrow}</div>'
            f'<h1>{title}</h1><p class="lede">{lede}</p>'
            f'<div class="rule"></div></div>')


def card(kicker: str, title: str, body: str, source: str = "") -> str:
    src = f'<div class="src">{source}</div>' if source else ""
    return (f'<div class="card"><div class="kicker">{kicker}</div>'
            f'<h4>{title}</h4><p>{body}</p>{src}</div>')


def paper_block(meta_tags: list[str], title: str, goal: str, diff: str,
                tags_warn: list[str] | None = None) -> str:
    warn = set(tags_warn or [])
    tags = "".join(
        f'<span class="tag{" warn" if t in warn else ""}">{t}</span>' for t in meta_tags
    )
    return (f'<div class="paper"><div class="meta">{tags}</div>'
            f'<h4>{title}</h4>'
            f'<p class="goal"><b>复现目标　</b>{goal}</p>'
            f'<div class="diff"><b>与原论文的差异　</b>{diff}</div></div>')


def section(label: str) -> str:
    return f'<div class="section-label">{label}</div>'


def kv_table(rows: list[tuple[str, str]]) -> str:
    body = "".join(f'<div class="row"><span class="k">{k}</span>'
                   f'<span class="v">{v}</span></div>' for k, v in rows)
    return f'<div class="kv">{body}</div>'


def step_marker(state: str) -> str:
    """state: done | now | todo"""
    cls = {"done": "dot-done", "now": "dot-now", "todo": "dot-todo"}.get(state, "dot-todo")
    return f'<span class="step-dot {cls}"></span>'


# ---------------- 向后兼容别名（早期页面使用） ----------------
DUKE_BLUE = PRIMARY
DUKE_BLUE_LIGHT = PRIMARY_2
DUKE_ACCENT = ACCENT
MUTED = INK_SOFT
SURFACE_ALT = "#F2F5FA"
