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

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.theme import CSS  # noqa: E402
from views import (dosimetry_tools, glossary, home, imaging_lab,  # noqa: E402
                   modeling_survival, phantom_lab, publications,
                   radiomic_filtering, registration, replication, roadmap,
                   segmentation_uq, toolbox)

st.set_page_config(
    page_title="医学影像 AI 学习平台",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CSS, unsafe_allow_html=True)

# 每个页面的渲染函数都叫 render()，必须显式给出唯一 url_path，
# 否则 Streamlit 会报 "Multiple Pages specified with URL pathname render"
pages = [
    st.Page(home.render, title="概览", icon="🏠", default=True, url_path="home"),
    st.Page(replication.render, title="文献复现专栏", icon="🔬", url_path="replication"),
    st.Page(publications.render, title="文献收藏", icon="📚", url_path="publications"),
    st.Page(radiomic_filtering.render, title="体素级放射组学滤波", icon="🧬",
            url_path="radiomic-filtering"),
    st.Page(segmentation_uq.render, title="分割与不确定性", icon="🎯",
            url_path="segmentation-uq"),
    st.Page(modeling_survival.render, title="特征建模与预后", icon="📈",
            url_path="modeling"),
    st.Page(dosimetry_tools.render, title="放疗剂量学工具", icon="☢️",
            url_path="dosimetry"),
    st.Page(registration.render, title="形变配准与物理合理性", icon="🫀",
            url_path="registration"),
    st.Page(glossary.render, title="术语库", icon="📖", url_path="glossary"),
    st.Page(imaging_lab.render, title="影像实验室", icon="🔬", url_path="imaging-lab"),
    st.Page(phantom_lab.render, title="体模实验台", icon="🧪", url_path="phantom-lab"),
    st.Page(roadmap.render, title="学习路线", icon="📅", url_path="roadmap"),
    st.Page(toolbox.render, title="工具与资源", icon="🧰", url_path="toolbox"),
]

nav = st.navigation(
    {
        "开始": [pages[0]],
        "杨老师专栏": pages[1:3],
        "复现他论文的方法": pages[3:8],
        "基础训练": pages[8:12],
        "参考": [pages[12]],
    }
)

with st.sidebar:
    st.markdown(
        '<div style="padding:6px 2px 14px 2px">'
        '<div style="font-size:1.05rem;font-weight:700">🧠 医学影像 AI 学习平台</div>'
        '<div style="font-size:0.8rem;opacity:0.8;margin-top:4px">'
        '放射组学 · 不确定性量化 · 放疗剂量学 · 可解释 AI</div></div>',
        unsafe_allow_html=True,
    )

nav.run()

with st.sidebar:
    st.markdown("---")
    st.caption("依据杨振宇老师（昆山杜克大学医学物理）已发表工作构建")
    st.caption("全部计算在本地完成 · conda 环境 `medimg`")
