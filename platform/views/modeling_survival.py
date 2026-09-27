"""特征建模与预后：多共线性 → 降维 → 分类器 → 交叉验证 → 融合 → 生存分析。"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.modeling import (cv_predict, dissimilarity_select, fusion_experiment,
                           make_synthetic_cohort, pca_reduce,
                           permutation_importance_table, prune_collinear,
                           roc_points, vif_table)
from core.survival import (risk_stratification_table, simulate_survival,
                           stratified_analysis)
from core.capabilities import require

CITE = """
**对应文献**
- Yang Z, et al. *Development of a multi-feature-combined model … local failure prediction … NSCLC.* Front Oncol 2023;13:1185771（MFC：三源融合）
- Zhang R, …, Yang Z. *A dual-radiomics model for overall survival prediction in early-stage NSCLC.* Front Oncol 2024;14:1419621
- Hu Z, Yang Z, et al. *A Deep Learning Model with Radiomics Analysis Integration for Glioblastoma Post-Resection Survival Prediction.* arXiv:2203.05891
"""


@st.cache_data(show_spinner=False)
def _cohort(n, signal, seed):
    return make_synthetic_cohort(n=n, seed=seed, signal=signal)


@st.cache_data(show_spinner="正在做交叉验证…")
def _cv(model, scheme, n, signal, seed, cols):
    co = _cohort(n, signal, seed)
    return cv_predict(model, co.X[list(cols)].values, co.y, scheme=scheme,
                      n_repeats=30, seed=seed)


def _roc_fig(curves: dict):
    fig = go.Figure()
    for label, (fpr, tpr, auc) in curves.items():
        fig.add_trace(go.Scatter(x=fpr, y=tpr, mode="lines",
                                 name=f"{label} (AUC={auc:.3f})"))
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines",
                             line=dict(dash="dash", color="gray"), name="随机"))
    fig.update_layout(xaxis_title="假阳性率", yaxis_title="真阳性率",
                      height=440, margin=dict(l=10, r=10, t=30, b=10),
                      legend=dict(orientation="h", y=-0.2))
    return fig


def render() -> None:
    if not require("sklearn", "特征建模与预后"):
        return
    st.title("特征建模与预后")
    st.markdown(
        "从**特征矩阵**到**临床结论**的完整链路：多共线性评估 → 降维/特征选择 → "
        "分类器 → 交叉验证 → 融合对比 → 生存分层。这就是杨老师多数论文的方法学骨架。"
    )
    with st.expander(" 对应文献"):
        st.markdown(CITE)

    with st.sidebar:
        st.markdown("#### 数据与实验设置")
        n = st.slider("样本量", 60, 300, 160, 20)
        signal = st.slider("信号强度", 0.4, 2.0, 1.0, 0.1)
        seed = st.number_input("随机种子", 0, 99, 3)

    co = _cohort(int(n), float(signal), int(seed))
    st.caption(f"合成队列：**{co.X.shape[0]} 例 × {co.X.shape[1]} 特征**，"
               f"阳性 {int(co.y.sum())} 例（{co.y.mean():.1%}）。"
               "特征分三源：手工放射组学 / 深度特征 / 临床信息。")

    tab1, tab2, tab3, tab4 = st.tabs(
        [" 特征质量", " 模型与交叉验证", " 三源融合", "⏳ 生存分析"])

    # ---------------- 特征质量 ----------------
    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("**多共线性：方差膨胀因子 (VIF)**")
            keep = prune_collinear(co.X, 0.95)
            st.caption(f"|r| > 0.95 的冗余特征剔除后：{co.X.shape[1]} → **{len(keep)}** 个")
            st.dataframe(vif_table(co.X[keep]).head(10), hide_index=True, width="stretch")
        with c2:
            st.markdown("**PCA 降维**")
            comps, info = pca_reduce(co.X[keep], min(6, len(keep)))
            st.dataframe(info, hide_index=True, width="stretch")
            st.bar_chart(info.set_index("主成分")["解释方差比"])

        st.markdown("**差异性分析（按组间差异挑选特征）**")
        sel = dissimilarity_select(co.X, co.y, 6)
        st.code("  ".join(sel), language=None)
        st.caption("对应 GBM 论文里与 PCA 对比的另一种特征选择策略 —— 按效应量（Cohen's d）排序。")

    # ---------------- 模型与交叉验证 ----------------
    with tab2:
        c1, c2, c3 = st.columns(3)
        model = c1.selectbox("分类器", ["LR", "SVM", "RF"])
        scheme = c2.selectbox("交叉验证方案", ["kfold", "loocv", "mccv"],
                              format_func=lambda s: {"kfold": "k 折",
                                                     "loocv": "留一法 LOOCV",
                                                     "mccv": "蒙特卡洛 MCCV"}[s])
        use_cols = c3.multiselect("特征来源", list(co.sources),
                                  default=list(co.sources))
        cols = tuple(c for s in use_cols for c in co.sources[s]) or tuple(co.X.columns)

        res = _cv(model, scheme, int(n), float(signal), int(seed), cols)
        m = res["metrics"]
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("AUC", f"{m['AUC']:.3f}")
        k2.metric("准确率", f"{m['准确率']:.3f}")
        k3.metric("灵敏度", f"{m['灵敏度']:.3f}")
        k4.metric("特异度", f"{m['特异度']:.3f}")
        st.caption(f"混淆矩阵：TP {m['TP']} / FP {m['FP']} / FN {m['FN']} / TN {m['TN']}"
                   f"　·　方案：{scheme}　·　特征数 {len(cols)}")

        st.plotly_chart(_roc_fig({f"{model} · {scheme}": (*roc_points(res["y_true"], res["y_score"]), m["AUC"])}),
                        width="stretch")

        st.markdown("**置换重要性（可解释性）**")
        imp = permutation_importance_table(model, co.X[list(cols)], co.y)
        st.dataframe(imp.head(10), hide_index=True, width="stretch")
        st.caption("置换重要性 = 打乱该特征后 AUC 掉多少。"
                   "对应论文里的特征贡献分析（LRP 的经典替代方案）。")

    # ---------------- 三源融合 ----------------
    with tab3:
        st.markdown("**复现 MFC 论文的核心结论：多源融合是否优于单源？**")
        if st.button(" 运行融合对比实验", type="primary"):
            with st.spinner("正在跑 7 种特征组合 × 交叉验证…"):
                st.session_state["fusion"] = fusion_experiment(co, model=model, scheme="kfold")
        fdf = st.session_state.get("fusion")
        if fdf is not None:
            st.dataframe(fdf, hide_index=True, width="stretch")
            fig = go.Figure(go.Bar(x=fdf["特征来源"], y=fdf["AUC"],
                                   marker_color=["#012169" if "+" in s else "#7c9cd6"
                                                 for s in fdf["特征来源"]]))
            fig.update_layout(height=380, yaxis_title="AUC", xaxis_title="",
                              margin=dict(l=10, r=10, t=20, b=10))
            fig.update_xaxes(tickangle=-25)
            st.plotly_chart(fig, width="stretch")
            st.info("**深蓝 = 融合模型，浅蓝 = 单一来源。** "
                    "可以看到融合通常优于任何单一来源 —— 但边际收益会递减，"
"这正是原论文要讨论的问题。", icon="")

    # ---------------- 生存分析 ----------------
    with tab4:
        c1, c2 = st.columns(2)
        effect = c1.slider("风险分数对生存的影响强度", 0.3, 2.5, 1.2, 0.1)
        censor = c2.slider("删失比例", 0.0, 0.6, 0.25, 0.05)

        sd = simulate_survival(co.risk_score, effect=effect,
                               censor_rate=censor, seed=int(seed))
        st_res = stratified_analysis(sd)

        k1, k2, k3 = st.columns(3)
        k1.metric("低风险组中位生存", f"{st_res['低风险']['中位生存（月）']:.1f} 月",
                  help=f"n={st_res['低风险']['n']}，事件 {st_res['低风险']['事件数']}")
        k2.metric("高风险组中位生存", f"{st_res['高风险']['中位生存（月）']:.1f} 月",
                  help=f"n={st_res['高风险']['n']}，事件 {st_res['高风险']['事件数']}")
        lr = st_res["logrank"]
        k3.metric("log-rank p 值", f"{lr['p']:.2e}", help=f"χ² = {lr['chi2']}")

        fig = go.Figure()
        for label, color in [("低风险", "#012169"), ("高风险", "#c8102e")]:
            km = st_res[label]["KM"]
            fig.add_trace(go.Scatter(x=km["时间"], y=km["生存概率"] * 100,
                                     mode="lines", name=f"{label}（n={st_res[label]['n']}）",
                                     line=dict(color=color, shape="hv")))
        fig.update_layout(xaxis_title="随访时间（月）", yaxis_title="生存率 (%)",
                          height=440, margin=dict(l=10, r=10, t=30, b=10),
                          legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, width="stretch")

        st.markdown("**按风险三分位进一步分层**")
        st.dataframe(risk_stratification_table(sd.risk, sd.time, sd.event),
                     hide_index=True, width="stretch")
        st.caption("Kaplan-Meier 与 log-rank 检验均为本平台手工实现，"
                   "每个数字都能追溯到公式（见 core/survival.py）。")
