#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
医学影像 AI 学习平台 —— 入口
================================
依据杨振宇老师（昆山杜克大学医学物理）已发表工作构建的本地科研平台。

启动：
    conda activate medimg
    cd medical-imaging-notes/platform
    streamlit run app.py
"""
from pathlib import Path
import sys
import traceback

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.auth import check as auth_check  # noqa: E402
from core.theme import CSS  # noqa: E402
from views import (dosimetry_tools, glossary, home, imaging_lab,  # noqa: E402
                   modeling_survival, phantom_lab, publications,
                   radiomic_filtering, registration, replication, roadmap,
                   segmentation_uq, toolbox)

st.set_page_config(
    page_title="医学影像 AI 学习平台",
    page_icon="◧",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CSS, unsafe_allow_html=True)

# 每个页面的渲染函数都叫 render()，必须显式给出唯一 url_path
# 图标使用 Material Symbols（:material/xxx:），保持界面干净
pages = [
    st.Page(home.render, title="概览", icon=":material/space_dashboard:",
            default=True, url_path="home"),
    st.Page(replication.render, title="文献复现专栏",
            icon=":material/science:", url_path="replication"),
    st.Page(publications.render, title="文献收藏",
            icon=":material/library_books:", url_path="publications"),
    st.Page(radiomic_filtering.render, title="体素级放射组学滤波",
            icon=":material/grain:", url_path="radiomic-filtering"),
    st.Page(segmentation_uq.render, title="分割与不确定性",
            icon=":material/target:", url_path="segmentation-uq"),
    st.Page(modeling_survival.render, title="特征建模与预后",
            icon=":material/trending_up:", url_path="modeling"),
    st.Page(dosimetry_tools.render, title="放疗剂量学工具",
            icon=":material/radar:", url_path="dosimetry"),
    st.Page(registration.render, title="形变配准与物理合理性",
            icon=":material/compare_arrows:", url_path="registration"),
    st.Page(glossary.render, title="术语库",
            icon=":material/menu_book:", url_path="glossary"),
    st.Page(imaging_lab.render, title="影像实验室",
            icon=":material/biotech:", url_path="imaging-lab"),
    st.Page(phantom_lab.render, title="体模实验台",
            icon=":material/tune:", url_path="phantom-lab"),
    st.Page(roadmap.render, title="学习路线",
            icon=":material/route:", url_path="roadmap"),
    st.Page(toolbox.render, title="工具与资源",
            icon=":material/handyman:", url_path="toolbox"),
]

nav = st.navigation(
    {
        "开始": [pages[0]],
        "杨振宇老师专栏": pages[1:3],
        "复现他论文的方法": pages[3:8],
        "基础训练": pages[8:12],
        "参考": [pages[12]],
    }
)

with st.sidebar:
    st.markdown(
        '<div class="side-brand">'
        '<div class="side-brand-title">医学影像 AI 学习平台</div>'
        '<div class="side-brand-sub">放射组学 · 不确定性量化 · 放疗剂量学 · 可解释 AI</div>'
        '</div>',
        unsafe_allow_html=True,
    )

# ---------------- 访问口令（设置 PLATFORM_PASSWORD 时启用） ----------------
if not auth_check():
    st.stop()

# ---------------- 错误边界：任何页面出错都不会白屏 ----------------
try:
    nav.run()
except Exception:
    st.markdown('<div class="err-title">页面渲染出错</div>', unsafe_allow_html=True)
    st.caption("这不影响其他页面。可先点下方按钮重试，或切换到别的页面。")
    with st.expander("查看错误详情"):
        st.code(traceback.format_exc(), language="text")
    if st.button("重新加载"):
        st.rerun()

with st.sidebar:
    st.markdown('<div class="side-foot">', unsafe_allow_html=True)
    st.caption("依据杨振宇老师已发表工作构建 · 全部计算在本机完成")
    st.markdown('</div>', unsafe_allow_html=True)
