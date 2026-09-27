"""分割算法对比与不确定性量化（SPU-Net 范式）。"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from core.plotting import setup_cjk_font
from core.segmentation import (METHODS, evaluate, make_lesion_phantom,
                               perturbation_uncertainty, segment,
                               uncertainty_groups, uncertainty_vs_error)
from core.capabilities import require

setup_cjk_font()

CITE = """
**对应文献**
- Yang Z, et al. *Quantifying U-Net uncertainty … by spherical image projection.* Med Phys 2024;51(3):1931-1943（SPU-Net）
- Yang Z, et al. *A voxel-wise uncertainty-guided framework for glioma segmentation …* Med Phys 2026;53(3):e70360
- Wang L, …, Yang Z, et al. *Uncertainty quantification in … meningioma radiotherapy target segmentation.* Front Oncol 2025;15:1474590
- **国家自然科学基金青年项目**：放疗中腹部图像自动分割的不确定性量化与评估研究
"""


@st.cache_data(show_spinner="正在分割并计算不确定性…")
def _phantom(contrast, noise, bias, seed):
    return make_lesion_phantom(size=56, radius=9, contrast=contrast,
                               noise=noise, bias_strength=bias, seed=seed)


@st.cache_data(show_spinner=False)
def _seg(image, roi, method):
    return segment(image, method=method, roi=roi)


@st.cache_data(show_spinner="正在做多视角扰动（模拟 SPU-Net）…")
def _uq(image, roi, n_views, angle, noise, seed, method):
    return perturbation_uncertainty(image, method=method, n_views=n_views,
                                    max_angle=angle, noise=noise, roi=roi, seed=seed)


def _panel(ph, pred, uq=None, sl=28):
    n = 4 if uq is not None else 3
    fig, axes = plt.subplots(1, n, figsize=(4.6 * n, 4.6))
    axes[0].imshow(ph.image[sl], cmap="gray"); axes[0].set_title("输入影像", fontsize=11)
    axes[1].imshow(ph.lesion[sl], cmap="gray"); axes[1].set_title("真值病灶", fontsize=11)
    axes[2].imshow(ph.image[sl], cmap="gray")
    axes[2].imshow(np.ma.masked_where(~pred[sl], pred[sl]), cmap="autumn", alpha=0.45)
    axes[2].set_title("分割结果", fontsize=11)
    if uq is not None:
        im = axes[3].imshow(uq.entropy[sl], cmap="magma")
        axes[3].set_title("不确定性（信息熵）", fontsize=11)
        fig.colorbar(im, ax=axes[3], fraction=0.046)
    for ax in axes:
        ax.axis("off")
    fig.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def render() -> None:
    if not require("skimage", "分割与不确定性"):
        return
    if not require("sklearn", "分割与不确定性"):
        return
    if not require("scipy", "分割与不确定性"):
        return
    st.title("分割与不确定性量化")
    st.markdown(
        "分割 = 给每个体素贴标签。但**模型什么时候会错？** 这是杨老师当前最核心的方向："
        "让模型同时输出「结论」和「可信度」。"
    )
    with st.expander(" 对应文献"):
        st.markdown(CITE)

    with st.sidebar:
        st.markdown("#### 体模难度")
        contrast = st.slider("病灶对比度 (HU)", 10, 90, 60)
        noise = st.slider("噪声 σ", 5, 25, 14)
        bias = st.slider("强度不均匀度", 0.0, 0.7, 0.40, 0.05)
        st.caption("不均匀度越高，全局阈值法越容易失效 —— 这正是真实临床的困难。")

    ph = _phantom(int(contrast), int(noise), float(bias), 0)
    tab1, tab2 = st.tabs([" 七种分割算法对比", " 不确定性量化"])

    # ---------------- 算法对比 ----------------
    with tab1:
        rows = []
        for name in METHODS:
            pred = _seg(ph.image, ph.organ, name)
            ev = evaluate(pred, ph.lesion)
            rows.append({"算法": name, "说明": METHODS[name], **ev})
        df = pd.DataFrame(rows).sort_values("Dice", ascending=False).reset_index(drop=True)
        st.dataframe(df[["算法", "说明", "Dice", "HD95 (mm)", "mHD (mm)",
                         "灵敏度", "特异度", "准确率"]],
                     hide_index=True, width="stretch")

        best = df.iloc[0]["算法"]
        st.session_state["best_method"] = best
        c1, c2 = st.columns([1, 1])
        with c1:
            st.metric("最佳算法", f"{best}（Dice {df.iloc[0]['Dice']:.3f}）")
        with c2:
            st.metric("最差算法", f"{df.iloc[-1]['算法']}（Dice {df.iloc[-1]['Dice']:.3f}）")
        st.bar_chart(df.set_index("算法")["Dice"])
        st.caption(" 所有算法都在**器官 ROI 内**分割 —— 不限制 ROI 是初学者最常见的错误。")
        _panel(ph, _seg(ph.image, ph.organ, best))

    # ---------------- 不确定性 ----------------
    with tab2:
        c1, c2, c3, c4 = st.columns(4)
        method = c1.selectbox("基础分割算法", list(METHODS), index=0)
        n_views = c2.slider("扰动视角数", 4, 20, 12)
        angle = c3.slider("最大旋转角 (°)", 0, 25, 12)
        uq_noise = c4.slider("扰动噪声", 0.0, 10.0, 4.0)

        uq = _uq(ph.image, ph.organ, int(n_views), float(angle),
                 float(uq_noise), 1, method)
        single = evaluate(_seg(ph.image, ph.organ, method), ph.lesion)["Dice"]
        cons = evaluate(uq.consensus, ph.lesion)["Dice"]

        m1, m2, m3 = st.columns(3)
        m1.metric("单次分割 Dice", f"{single:.3f}")
        m2.metric("多视角共识 Dice", f"{cons:.3f}", delta=f"{cons - single:+.3f}")
        m3.metric("有分歧体素占比", f"{100*(uq.entropy > 1e-9).mean():.1f}%")

        _panel(ph, uq.consensus, uq)

        st.markdown("#### 核心命题：不确定性真的能预测错误吗？")
        groups = uncertainty_groups(uq, ph.lesion)
        if groups:
            gdf = pd.DataFrame(groups)
            st.dataframe(gdf, hide_index=True, width="stretch")
            if len(gdf) == 2:
                r0, r1 = gdf.iloc[0]["错误率"], gdf.iloc[1]["错误率"]
                st.success(
                    f"**一致体素错误率 {r0:.1%}，有分歧体素错误率 {r1:.1%}** —— "
                    f"不确定性确实标记出了模型不可靠的区域（相差 {r1/max(r0,1e-9):.0f} 倍）。"
                    if r1 > r0 else "本次设置下两者差异不明显，试试提高噪声或不均匀度。"
                )
        rows = uncertainty_vs_error(uq, ph.lesion, n_bins=5)
        if rows:
            st.markdown("**按不确定性分档看错误率**")
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            st.bar_chart(pd.DataFrame(rows).set_index("不确定性分位")["错误率"])

        st.info(
            "**这就是 SPU-Net 的全部思想**：用不同的「视角」得到多组预测，"
            "分歧越大越不可信；再把这些预测聚合起来，结果往往比任何单次预测都准。"
            "原论文用**球面投影**制造视角，这里用旋转 + 加噪模拟同一机制。",
            
        )
