"""概览页：平台首页。"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.env_check import check_tools, summary
from core.glossary_parser import load_terms

REPO = Path(__file__).resolve().parents[2]


def _git_commits() -> int | None:
    try:
        import subprocess
        out = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=REPO,
                             capture_output=True, text=True, timeout=5)
        return int(out.stdout.strip()) if out.returncode == 0 else None
    except Exception:
        return None


def render() -> None:
    st.title("🧠 医学影像 AI 学习平台")
    st.markdown(
        "把**术语库**、**影像实验室**、**体模实验台**、**学习路线**和**工具链**"
        "整合在一个界面上 —— 从看懂一个名词，到亲手提取一次放射组学特征。"
    )

    # ---------- 关键指标 ----------
    terms = load_terms()
    tools = check_tools()
    ok, total = summary(tools)
    commits = _git_commits()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("术语库词条", f"{len(terms)}", help="来自 glossary/ 目录，可全文搜索")
    c2.metric("科研工具就绪", f"{ok}/{total}", help="环境自检结果，详见「工具与资源」")
    c3.metric("平台页面", "6", help="概览 / 术语库 / 影像实验室 / 体模实验台 / 学习路线 / 工具与资源")
    c4.metric("仓库提交", commits if commits else "—", help="git rev-list --count HEAD")

    st.divider()

    # ---------- 快速入口 ----------
    st.subheader("从这里开始")
    a, b, c = st.columns(3)
    with a:
        st.markdown(
            "#### 📚 术语库\n"
            "177 条医学影像 AI 名词，支持中英文搜索、按难度与主题筛选。\n\n"
            "**建议**：先只看 `L1` 的条目，看懂 80% 再往下。"
        )
    with b:
        st.markdown(
            "#### 🧪 体模实验台\n"
            "拖动滑杆改变病灶大小、噪声、密度，**实时看放射组学特征怎么变**。\n\n"
            "**这是理解「特征在测什么」最快的方式。**"
        )
    with c:
        st.markdown(
            "#### 🔬 影像实验室\n"
            "载入体模或上传 NIfTI 影像 → 选阈值分割 → 提取 107 个特征 → 导出 CSV。\n\n"
            "**这就是真实放射组学研究的第一步。**"
        )

    st.divider()

    # ---------- 环境状态 ----------
    st.subheader("环境状态")
    bad = [t for t in tools if not t.ok]
    if not bad:
        st.success(f"✅ 全部 {total} 项科研工具已就绪（Python 3.11 · conda 环境 medimg）")
    else:
        st.warning("以下工具尚未就绪：" + "、".join(t.label for t in bad))

    cols = st.columns(3)
    order = ["数值计算", "可视化", "机器学习", "图像处理", "医学影像", "放射组学", "深度学习", "查看器", "平台"]
    for i, cat in enumerate(order):
        items = [t for t in tools if t.category == cat]
        if not items:
            continue
        with cols[i % 3]:
            st.markdown(f"**{cat}**")
            for t in items:
                mark = "✅" if t.ok else "⬜"
                st.caption(f"{mark} {t.label} {t.version}")

    st.divider()

    # ---------- 学习闭环 ----------
    st.subheader("学习闭环：这个平台怎么用")
    st.markdown(
        """
| 步骤 | 在哪做 | 你会得到什么 |
|---|---|---|
| 1. 建立词汇量 | **术语库** | 看懂论文里的每个名词 |
| 2. 建立直觉 | **体模实验台** | 知道每个特征对什么敏感 |
| 3. 走通流程 | **影像实验室** | 一份可导出的特征表 |
| 4. 按计划推进 | **学习路线** | 12 周的可勾选清单 |
| 5. 环境与工具 | **工具与资源** | 启动命令与参考链接 |
        """
    )

    st.info(
        "**配套仓库**：[medical-imaging-notes]"
        "(https://github.com/maka-baka0806/medical-imaging-notes) —— "
        "术语库、示例脚本、环境配置都在这份仓库里持续更新。",
        icon="📦",
    )
