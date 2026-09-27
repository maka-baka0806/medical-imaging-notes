"""形变配准与物理合理性评估（PhysMorph）。"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.plotting import setup_cjk_font
from core.registration import (METHODS, evaluate_registration, folding_stats,
                               jacobian_determinant, make_registration_case,
                               register)

setup_cjk_font()

CITE = """
**对应文献**
- Zhang Z, Guo D, …, Yang Z. *PhysMorph: A biomechanical and image-guided deep learning framework for real-time multi-modal liver image registration.* Phys Imaging Radiat Oncol 2026;37:100906（**代码已开源**）
- Sun P, Zhang C, Yang Z, et al. *An Implicit Registration Framework Integrating Kolmogorov-Arnold Networks with Velocity Regularization for IGRT.* Bioengineering 2025;12(9):1005
"""


@st.cache_data(show_spinner=False)
def _case(size, magnitude, seed):
    return make_registration_case(size=size, magnitude=magnitude, seed=seed)


@st.cache_data(show_spinner="正在执行形变配准…")
def _register(size, magnitude, seed, method, iters):
    case = _case(size, magnitude, seed)
    res = register(case, method=method, iterations=iters)
    return res, evaluate_registration(res, case)


def render() -> None:
    st.title("🫀 形变配准与物理合理性")
    st.markdown(
        "把治疗前影像与治疗中影像对齐。难点不是「对齐」，而是"
        "**对齐得是否物理合理** —— 器官不能被算法随意拉扯、折叠。"
    )
    with st.expander("📄 对应文献"):
        st.markdown(CITE)

    c1, c2, c3, c4 = st.columns(4)
    size = c1.select_slider("体数据尺寸", [40, 48, 56, 64], value=48)
    mag = c2.slider("真值形变幅度（体素）", 1.0, 8.0, 3.5, 0.5)
    seed = c3.number_input("随机种子", 0, 99, 1)
    iters = c4.slider("迭代次数", 10, 100, 40, 10)

    case = _case(int(size), float(mag), int(seed))

    st.markdown("#### 一、病例与真值")
    k1, k2, k3 = st.columns(3)
    k1.metric("标志点数", len(case.landmarks_fixed))
    k2.metric("器官体素数", int(case.organ.sum()))
    k3.metric("真值形变幅度", f"~{mag:.1f} 体素")

    sl = case.fixed.shape[0] // 2
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6))
    for ax, (img, title) in zip(axes, [
        (case.fixed[sl], "参考图像（治疗前）"),
        (case.moving[sl], "待配准图像（治疗中）"),
        (np.linalg.norm(case.dvf_true, axis=0)[sl], "真值形变幅度"),
    ]):
        im = ax.imshow(img, cmap="gray" if "形变" not in title else "viridis")
        ax.set_title(title, fontsize=11); ax.axis("off")
        if "形变" in title:
            fig.colorbar(im, ax=ax, fraction=0.046, label="体素")
    fig.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close(fig)

    st.markdown("#### 二、执行配准（调用 SimpleITK 现成算法）")
    rows = []
    results = {}
    for method in METHODS:
        res, ev = _register(int(size), float(mag), int(seed), method, int(iters))
        results[method] = (res, ev)
        rows.append({"方法": METHODS[method], **ev})
    df = pd.DataFrame(rows)
    st.dataframe(df[["方法", "TRE (mm)", "MSD (mm)", "DVF 端点误差 (mm)",
                     "耗时 (s)", "负 Jacobian 比例", "判断"]],
                 hide_index=True, width="stretch")

    st.markdown("#### 三、物理合理性：Jacobian 行列式")
    c1, c2 = st.columns([1, 1])
    pick = st.selectbox("查看哪个方法的结果", list(METHODS),
                        format_func=lambda m: METHODS[m])
    res, ev = results[pick]
    det = jacobian_determinant(res["dvf"])

    with c1:
        fig = go.Figure(go.Heatmap(z=det[sl], colorscale="RdBu_r",
                                   zmid=1.0, colorbar=dict(title="det(J)")))
        fig.update_layout(title="Jacobian 行列式（红 = 膨胀，蓝 = 压缩）",
                          height=400, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.markdown(f"**{METHODS[pick]}**")
        st.dataframe(pd.DataFrame([{"指标": k, "数值": v} for k, v in ev.items()]),
                     hide_index=True, width="stretch")
        st.caption("**det(J) ≤ 0 = 组织自我折叠**，物理上不可能。"
                   "PhysMorph 论文正是用「负 Jacobian 体素比例」来证明"
                   "深度学习配准也能保持物理合理性。")

    st.markdown("#### 四、配准前后对比")
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6))
    for ax, (img, title) in zip(axes, [
        (case.moving[sl], "配准前"),
        (res["warped"][sl], f"配准后（{pick}）"),
        (case.fixed[sl], "参考（目标）"),
    ]):
        ax.imshow(img, cmap="gray"); ax.set_title(title, fontsize=11); ax.axis("off")
    fig.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close(fig)

    st.info(
        "**为什么 PhysMorph 要在深度学习里嵌入有限元？** "
        "纯图像相似度驱动的配准容易产生「看起来像、但物理上不可能」的形变。"
        "杨老师团队的做法是：用有限元仿真生成生物力学合理的形变作为监督信号，"
        "再用网络把它加速到毫秒级（原论文：10 分钟 → 103 毫秒）。",
        icon="💡",
    )
