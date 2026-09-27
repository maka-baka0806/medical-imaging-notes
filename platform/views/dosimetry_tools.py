"""放疗剂量学：DVH、Gamma 指数、球形投影（SCNN）。"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.dosimetry import (dvh_curve, gamma_index, make_simt_case, simt_metrics,
                            sphere_feature_vector, spherical_projection)
from core.plotting import setup_cjk_font
from core.capabilities import require

setup_cjk_font()

CITE = """
**对应文献**
- Yang Z, et al. *Total brain dose estimation in SIMT radiosurgery via a novel deep neural network with spherical convolutions.* Med Phys 2025;52(6):4266-4277
- Li Z†, Chen K†, Yang Z, et al. *A personalized DVH prediction model for HDR brachytherapy in cervical cancer.* Front Oncol 2022;12:967436
- Shu X, …, Yang Z, et al. *Knowledge-based DRU for synthetic CT generation …* J Appl Clin Med Phys 2026（Gamma 指数验证）
"""


@st.cache_data(show_spinner=False)
def _case(n_targets, seed, prescription):
    return make_simt_case(size=64, n_targets=n_targets, prescription=prescription, seed=seed)


def render() -> None:
    if not require("scipy", "放疗剂量学工具"):
        return
    if not require("plotly", "放疗剂量学工具"):
        return
    st.title("放疗剂量学工具")
    st.markdown(
        "放疗研究离不开三件工具：**DVH 剂量指标**、**Gamma 指数验证**、"
        "以及杨老师 SCNN 论文的独门变换——**球形投影**。"
    )
    with st.expander(" 对应文献"):
        st.markdown(CITE)

    c1, c2, c3 = st.columns(3)
    n_t = c1.slider("靶点数量（SIMT）", 1, 8, 4)
    pres = c2.select_slider("处方剂量 (Gy)", [15, 18, 20, 24], value=20)
    seed = c3.number_input("随机种子", 0, 99, 2)

    case = _case(int(n_t), int(seed), float(pres))
    tab1, tab2, tab3 = st.tabs([" DVH 与剂量指标", " Gamma 指数", " 球形投影"])

    # ---------------- DVH ----------------
    with tab1:
        m = simt_metrics(case)
        cols = st.columns(6)
        for i, k in enumerate(["靶点数", "靶区总体积 (cc)", "脑体积 (cc)",
                               "V50% (cc)", "V60% (cc)", "V12Gy (cc)"]):
            cols[i].metric(k, m.get(k, "—"))

        grid, cum = dvh_curve(case.dose, case.brain)
        fig = go.Figure(go.Scatter(x=grid, y=cum, mode="lines",
                                   line=dict(color="#012169", width=3),
                                   fill="tozeroy", fillcolor="rgba(1,33,105,0.12)"))
        for lvl, name in [(pres * 0.5, "V50%"), (pres * 0.6, "V60%"),
                          (10.0, "V10Gy"), (12.0, "V12Gy")]:
            if lvl <= grid[-1]:
                fig.add_vline(x=lvl, line_dash="dot", line_color="#c8102e",
                              annotation_text=name, annotation_position="top")
        fig.update_layout(xaxis_title="剂量 (Gy)", yaxis_title="接受 ≥ 该剂量的脑体积 (%)",
                          height=420, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, width="stretch")

        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("**完整剂量指标表**")
            st.dataframe(pd.DataFrame([
                {"指标": k, "数值": str(v)} for k, v in m.items()
            ]), hide_index=True, width="stretch")
        with c2:
            sl = 32
            fig2, ax = plt.subplots(figsize=(5.6, 5.0))
            im = ax.imshow(case.dose[sl], cmap="jet")
            ax.contour(case.brain[sl], colors="white", linewidths=0.6)
            ax.set_title("剂量分布（白线 = 脑轮廓）", fontsize=11)
            ax.axis("off")
            fig2.colorbar(im, ax=ax, label="Gy")
            fig2.tight_layout()
            st.pyplot(fig2, width="stretch")
            plt.close(fig2)

    # ---------------- Gamma ----------------
    with tab2:
        st.markdown("**Gamma 指数：判断两个剂量分布是否「等效」**")
        c1, c2, c3 = st.columns(3)
        dose_tol = c1.select_slider("剂量容差 (%)", [1, 2, 3, 5], value=3)
        dist_tol = c2.select_slider("距离容差 (mm)", [1, 2, 3], value=2)
        shift = c3.slider("人为引入的剂量偏移 (体素)", 0, 4, 1)

        eval_dose = np.roll(case.dose, shift, axis=0) * (1 + 0.02 * shift)
        g = gamma_index(case.dose, eval_dose, case.spacing,
                        dose_tol_pct=float(dose_tol), dist_tol_mm=float(dist_tol))

        k1, k2, k3 = st.columns(3)
        k1.metric("Gamma 通过率", f"{g['通过率']*100:.1f}%",
                  help="TG-218 通常要求 ≥95%")
        k2.metric("最大 Gamma 值", f"{g['最大 gamma']:.2f}", help=">1 即不通过")
        k3.metric("评估体素数", f"{g['评估体素数']}")
        st.progress(min(max(g["通过率"], 0.0), 1.0))

        sl = 32
        fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
        for ax, (img, title, cm) in zip(axes, [
            (case.dose[sl], "参考剂量", "jet"),
            (eval_dose[sl], f"待评剂量（偏移 {shift} 体素）", "jet"),
            (g["gamma"][sl], f"Gamma 图（{dose_tol}%/{dist_tol}mm）", "RdYlGn_r"),
        ]):
            im = ax.imshow(img, cmap=cm, vmin=0 if "Gamma" not in title else 0,
                           vmax=None if "Gamma" not in title else 2)
            ax.set_title(title, fontsize=11); ax.axis("off")
            fig.colorbar(im, ax=ax, fraction=0.046)
        fig.tight_layout()
        st.pyplot(fig, width="stretch")
        plt.close(fig)
        st.caption("Gamma > 1 的区域（红）就是不通过的地方。"
                   "合成 CT 论文正是用这个指标验证「假 CT 能不能算准剂量」。")

    # ---------------- 球形投影 ----------------
    with tab3:
        st.markdown(
            "**SCNN 的核心变换**：把大脑「装进一个球」，3D 靶区分布用球坐标"
            "（方位角 × 极角）表示成一张 **2D 球面图** —— 于是可以用球面卷积处理，"
            "参数量比 3D U-Net 少一个数量级。"
        )
        sp = spherical_projection(case.targets)
        feats = sphere_feature_vector(case.targets)

        c1, c2 = st.columns([1.2, 1])
        with c1:
            fig = go.Figure(go.Heatmap(z=sp.density, colorscale="Blues",
                                       colorbar=dict(title="靶区密度")))
            fig.update_layout(xaxis_title="方位角 θ 分箱", yaxis_title="极角 φ 分箱",
                              height=420, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, width="stretch")
        with c2:
            st.markdown("**球面几何特征**")
            st.dataframe(pd.DataFrame([{"特征": k, "数值": v} for k, v in feats.items()]),
                         hide_index=True, width="stretch")
            st.caption("原论文把整张球面图送进球面卷积网络预测 V10Gy/V12Gy；"
                       "这里给出可解释的汇总量，便于理解「球面图到底编码了什么」。")

        sl = 32
        fig2, axes = plt.subplots(1, 2, figsize=(10, 4.6))
        axes[0].imshow(case.targets[sl], cmap="gray")
        axes[0].set_title("靶区（3D 中的一层）", fontsize=11); axes[0].axis("off")
        axes[1].imshow(sp.density, cmap="Blues", aspect="auto")
        axes[1].set_title("同一批靶区的球面投影", fontsize=11)
        axes[1].set_xlabel("方位角 θ"); axes[1].set_ylabel("极角 φ")
        fig2.tight_layout()
        st.pyplot(fig2, width="stretch")
        plt.close(fig2)

        st.info(
            "**为什么这样能省算力？** 3D 卷积的参数量随体积增长，而球面图是固定大小的 2D 图像；"
            "同时球坐标天然匹配「脑近似球形」这一几何先验 —— "
            "这正是杨老师偏爱的「把几何结构显式写进模型」的思路。",
            
        )
