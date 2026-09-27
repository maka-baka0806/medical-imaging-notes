"""
能力检测与优雅降级
====================
不同环境（本地 conda / 云端 Streamlit Cloud）安装的依赖不同。
本模块负责检测可选依赖，并在缺失时给出**干净的提示**而不是崩溃。

用法：
    from core.capabilities import require
    def render():
        if not require("radiomics", "体素级放射组学滤波"):
            return
        ...
"""
from __future__ import annotations

import importlib

import streamlit as st

# 能力 → (显示名, 说明, 安装方式)
CAPABILITIES = {
    "radiomics": ("PyRadiomics", "放射组学特征提取（107 个特征）",
                  "需要 C 编译器从源码编译，云端环境可能不支持"),
    "SimpleITK": ("SimpleITK", "医学影像读写与配准", "pip install SimpleITK"),
    "torch": ("PyTorch", "神经常微分方程与深度学习", "conda install -c conda-forge pytorch"),
    "skimage": ("scikit-image", "分割算法与形态学", "pip install scikit-image"),
    "sklearn": ("scikit-learn", "经典机器学习与交叉验证", "pip install scikit-learn"),
    "scipy": ("SciPy", "滤波、插值、数值计算", "pip install scipy"),
    "plotly": ("Plotly", "交互式图表", "pip install plotly"),
}

_cache: dict[str, bool] = {}


def has(name: str) -> bool:
    """检测某个包是否可用（结果缓存）。"""
    if name not in _cache:
        try:
            importlib.import_module(name)
            _cache[name] = True
        except Exception:
            _cache[name] = False
    return _cache[name]


def require(name: str, page: str) -> bool:
    """页面级能力门禁：缺失时渲染干净提示并返回 False。"""
    if has(name):
        return True

    label, purpose, hint = CAPABILITIES.get(name, (name, "", ""))
    st.markdown(
        f'<div class="paper"><div class="meta">'
        f'<span class="tag warn">依赖缺失</span></div>'
        f'<h4>{page}</h4>'
        f'<p class="goal">本页需要 <b>{label}</b>（{purpose}），'
        f'当前运行环境未安装该依赖。</p>'
        f'<div class="diff">{hint}。'
        f'平台其余页面不受影响，可正常使用。</div></div>',
        unsafe_allow_html=True,
    )
    return False


def summary() -> dict[str, bool]:
    """返回全部能力的可用状态。"""
    return {k: has(k) for k in CAPABILITIES}


def missing() -> list[str]:
    return [k for k, ok in summary().items() if not ok]
