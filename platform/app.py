#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
医学影像 AI 学习平台 —— 入口
================================
把术语库、影像实验室、体模实验台、学习路线、工具链整合到一个网站里。

启动：
    conda activate medimg
    cd medical-imaging-notes/platform
    streamlit run app.py
"""
from pathlib import Path
import sys

import streamlit as st

# 让 views / core 可被导入
sys.path.insert(0, str(Path(__file__).resolve().parent))

from views import (home, glossary, imaging_lab, phantom_lab, roadmap, toolbox)  # noqa: E402

st.set_page_config(
    page_title="医学影像 AI 学习平台",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 注意：每个页面的渲染函数都叫 render()，Streamlit 会用函数名推断 URL 路径，
# 因此必须显式指定唯一的 url_path，否则报
# "Multiple Pages specified with URL pathname render"
pages = [
    st.Page(home.render, title="概览", icon="🏠", default=True, url_path="home"),
    st.Page(glossary.render, title="术语库", icon="📚", url_path="glossary"),
    st.Page(imaging_lab.render, title="影像实验室", icon="🔬", url_path="imaging-lab"),
    st.Page(phantom_lab.render, title="体模实验台", icon="🧪", url_path="phantom-lab"),
    st.Page(roadmap.render, title="学习路线", icon="🎯", url_path="roadmap"),
    st.Page(toolbox.render, title="工具与资源", icon="🧰", url_path="toolbox"),
]

nav = st.navigation(pages)

with st.sidebar:
    st.markdown("### 🧠 医学影像 AI 学习平台")
    st.caption("放射组学 · 医学影像分析 · 可解释 AI")
    st.divider()

nav.run()

with st.sidebar:
    st.divider()
    st.caption("目标方向：医学物理 / 放射组学 / 医学影像 AI")
    st.caption("本平台基于本地 `medimg` 环境运行")
