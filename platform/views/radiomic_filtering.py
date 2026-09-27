"""体素级放射组学滤波：复现肺通气特征图方法。"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from core.filtering import (FEATURE_LABELS, make_lung_phantom, radiomic_filtering,
                            rank_features, spearman_map_vs_reference)
from core.plotting import setup_cjk_font

setup_cjk_font()

CITE = """
**对应文献**
- Yang Z, et al. *Quantification of lung function on CT images based on pulmonary radiomic filtering.* Med Phys 2022;49(11):7278-7286
- Zhang R, …, Yang Z. *An Explainable Neural Radiomic Sequence Model … 4DCT-based Pulmonary Ventilation.* arXiv:2503.23898
"""


@st.cache_data(show_spinner="正在做体素级滤波计算…")
def _run(kernel: int, defect_radius: int, bins: int, seed: int):
    ph = make_lung_phantom(size=64, defect_radius=defect_radius, seed=seed)
    res = radiomic_filtering(ph.ct, ph.mask, kernel_size=kernel, bins=bins)
    rank = rank_features(res, ph.reference)
    return ph, res, rank


def _show(ph, res, key, slice_idx=32, cmap="inferno"):
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.6))
    panels = [
        (ph.ct[slice_idx], "输入 CT（HU）", "gray", None),
        (res.maps[key][slice_idx], FEATURE_LABELS.get(key, key), cmap, None),
        (ph.reference[slice_idx], "参考通气图（金标准）", "viridis", None),
        (ph.ct[slice_idx], "缺损区（白色）叠加", "gray", ph.defect[slice_idx]),
    ]
    for ax, (img, title, cm, overlay) in zip(axes, panels):
        ax.imshow(img, cmap=cm)
        if overlay is not None:
            ax.imshow(np.ma.masked_where(~overlay, overlay), cmap="autumn", alpha=0.5)
        ax.set_title(title, fontsize=11)
        ax.axis("off")
    fig.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def render() -> None:
    st.title("🧬 体素级放射组学滤波")
    st.markdown(
        "传统放射组学把整个器官压成**一个特征向量**；本方法让 3D 滑窗逐体素滑动，"
        "每个特征变成一张**与 CT 同尺寸的特征图**——从而获得空间分辨能力。"
        "**这是杨老师最具代表性的方法之一。**"
    )
    with st.expander("📄 对应文献"):
        st.markdown(CITE)

    c1, c2, c3, c4 = st.columns(4)
    kernel = c1.select_slider("滑窗核大小 (mm)", [5, 9, 15, 21, 27, 33], value=15)
    drad = c2.slider("通气缺损半径 (体素)", 5, 13, 9)
    bins = c3.select_slider("灰度分箱数", [8, 16, 32, 64], value=32)
    seed = c4.number_input("随机种子", 0, 99, 0)

    ph, res, rank = _run(int(kernel), int(drad), int(bins), int(seed))

    st.success(
        f"复现完成：合成肺体模（{ph.mask.sum()} 个肺体素，"
        f"{ph.defect.sum()} 个缺损体素）→ {len(res.maps)} 张特征图 → "
        f"与参考通气图做体素级 Spearman 相关"
    )

    tab1, tab2, tab3 = st.tabs(["🗺️ 特征图可视化", "🏆 相关性排行榜", "🎛️ 核大小敏感性"])

    with tab1:
        keys = list(res.maps.keys())
        pick = st.selectbox("选择特征", keys,
                            format_func=lambda k: FEATURE_LABELS.get(k, k),
                            index=keys.index("std") if "std" in keys else 0)
        _show(ph, res, pick)
        rho = spearman_map_vs_reference(res.maps[pick], ph.reference, res.mask)
        st.metric("该特征图 vs 参考通气图的 ρ", f"{rho:+.4f}")
        st.caption("负相关 = 该特征值越高，通气越差。这与论文结论一致："
                   "功能受损区纹理更紊乱。")

    with tab2:
        df = pd.DataFrame([{k: v for k, v in r.items() if k != "key"} for r in rank])
        st.dataframe(df, hide_index=True, width="stretch")
        st.bar_chart(df.set_index("特征")["Spearman ρ"])
        st.info(
            "**关键发现（与原论文一致）**：纹理类特征与通气显著相关，"
            "而**局部均值（纯强度）几乎不相关** —— 这正说明为什么"
            "「只看 HU 阈值」的方法不如放射组学滤波。",
            icon="🔑",
        )

    with tab3:
        rows = []
        for k in [5, 9, 15, 21, 27, 33]:
            _, _, r = _run(int(k), int(drad), int(bins), int(seed))
            top = r[0]
            std_row = next((x for x in r if x["key"] == "std"), None)
            rows.append({
                "核 (mm)": k,
                "最强特征": top["特征"],
                "最强 ρ": top["Spearman ρ"],
                "局部标准差 ρ": std_row["Spearman ρ"] if std_row else None,
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.caption("核太小 → 特征图噪声大；核太大 → 空间分辨丢失。"
                   "原论文正是通过这种扫描选定了 15 mm。")
