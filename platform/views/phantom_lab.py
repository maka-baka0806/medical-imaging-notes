"""体模实验台：交互式参数实验，理解每个放射组学特征对什么敏感。"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.phantom import (FEATURE_FAMILIES, extract_features, group_features,
                          make_sphere_phantom, to_sitk)
from core.plotting import setup_cjk_font

setup_cjk_font()   # 让图中中文正常显示

# 参与扫描的特征（覆盖各家族，便于观察敏感性差异）
WATCH_FEATURES = [
    "original_shape_MeshVolume",
    "original_shape_SurfaceArea",
    "original_shape_Sphericity",
    "original_firstorder_Mean",
    "original_firstorder_Entropy",
    "original_firstorder_Uniformity",
    "original_glcm_Contrast",
    "original_glcm_Correlation",
    "original_glrlm_RunLengthNonUniformity",
    "original_glszm_ZoneEntropy",
    "original_ngtdm_Busyness",
    "original_ngtdm_Coarseness",
]

PRETTY = {
    "original_shape_MeshVolume": "形状 · 网格体积",
    "original_shape_SurfaceArea": "形状 · 表面积",
    "original_shape_Sphericity": "形状 · 球形度",
    "original_firstorder_Mean": "一阶 · 均值",
    "original_firstorder_Entropy": "一阶 · 熵",
    "original_firstorder_Uniformity": "一阶 · 均匀度",
    "original_glcm_Contrast": "GLCM · 对比度",
    "original_glcm_Correlation": "GLCM · 相关性",
    "original_glrlm_RunLengthNonUniformity": "GLRLM · 游程不均匀度",
    "original_glszm_ZoneEntropy": "GLSZM · 区域熵",
    "original_ngtdm_Busyness": "NGTDM · 繁忙度",
    "original_ngtdm_Coarseness": "NGTDM · 粗糙度",
}


@st.cache_data(show_spinner=False)
def _features(radius: int, noise: float, tissue: float, shape: str,
              seed: int, bin_width: float, size: int = 48) -> dict:
    ph = make_sphere_phantom(size=size, radius=radius, tissue_hu=tissue,
                             noise_sd=noise, shape=shape, seed=seed)
    img, msk = to_sitk(ph)
    return extract_features(img, msk, bin_width=bin_width)


def render() -> None:
    st.title("🧪 体模实验台")
    st.markdown(
        "在一个**答案已知**的合成病灶上做实验：拖动滑杆，实时观察 107 个放射组学特征"
        "如何随之改变。**这是理解「特征到底在测什么」最快的途径。**"
    )

    tab1, tab2 = st.tabs(["🎛️ 单点实验", "📈 参数敏感性扫描"])

    # ============================================================
    # 单点实验
    # ============================================================
    with tab1:
        c1, c2, c3, c4, c5 = st.columns(5)
        shape_cn = c1.selectbox("形状", ["球 sphere", "椭球 ellipsoid", "立方 cube"])
        shape = {"球 sphere": "sphere", "椭球 ellipsoid": "ellipsoid",
                 "立方 cube": "cube"}[shape_cn]
        radius = c2.slider("半径", 4, 16, 8)
        noise = c3.slider("噪声 σ (HU)", 0.0, 40.0, 10.0, 1.0)
        tissue = c4.slider("组织密度 (HU)", -200, 300, 100, 10)
        binw = c5.select_slider("binWidth", [5, 10, 15, 20, 25, 50], value=25)

        ph = make_sphere_phantom(size=48, radius=radius, tissue_hu=float(tissue),
                                 noise_sd=float(noise), shape=shape)
        feats = _features(radius, float(noise), float(tissue), shape, 0, float(binw))
        grouped = group_features(feats)

        left, right = st.columns([1, 1.4])
        with left:
            img2d, m2d = ph.image[24], ph.mask[24]
            fig, ax = plt.subplots(figsize=(4.6, 4.6))
            ax.imshow(img2d, cmap="gray")
            ax.imshow(np.ma.masked_where(~m2d, m2d), cmap="autumn", alpha=0.3)
            ax.set_title(f"中心层 ｜ {shape} ｜ r={radius} ｜ σ={noise:.0f}", fontsize=10)
            ax.axis("off")
            fig.tight_layout()
            st.pyplot(fig, width="stretch")
            plt.close(fig)

            mv = grouped["shape"]["MeshVolume"]
            st.metric("网格体积", f"{mv:.1f} mm³",
                      delta=f"{100*(mv-ph.true_volume_mm3)/ph.true_volume_mm3:+.2f}% vs 理论")
            st.metric("球形度 Sphericity", f"{grouped['shape']['Sphericity']:.4f}",
                      help="完美球体 = 1.0；越不规则越小")

        with right:
            st.markdown("**关键特征实时值**")
            rows = []
            for k in WATCH_FEATURES:
                if k in feats:
                    rows.append({"特征": PRETTY[k], "数值": feats[k]})
            st.dataframe(pd.DataFrame(rows), hide_index=True,
                         width="stretch", height=420)

        st.divider()
        st.markdown("#### 🤔 试试看：这几个问题你能答上来吗？")
        q1, q2 = st.columns(2)
        with q1:
            st.markdown(
                "- 把**噪声 σ 从 0 调到 40**：哪些特征几乎不变？哪些剧烈变化？\n"
                "- 把**半径从 4 调到 16**：体积按什么规律变？（提示：r³）\n"
                "- 把**组织密度从 0 调到 200**：球形度会变吗？为什么？"
            )
        with q2:
            st.markdown(
                "- 把**形状从球改成椭球**：Sphericity 怎么变？\n"
                "- 把 **binWidth 从 5 调到 50**：纹理特征变化大还是一阶特征变化大？\n"
                "- **结论**：形状特征只对几何敏感，纹理特征对噪声和分箱都敏感。"
            )

    # ============================================================
    # 参数扫描
    # ============================================================
    with tab2:
        st.markdown(
            "选一个参数，让它连续变化，观察**每个特征对它有多敏感** —— "
            "这就是放射组学「特征稳健性」研究的核心方法（对应 2020 年数字体模那篇论文）。"
        )

        c1, c2, c3 = st.columns(3)
        param = c1.selectbox("扫描参数", ["半径 radius", "噪声 σ", "组织密度 HU"])
        n_points = c2.slider("采样点数", 5, 15, 9)
        binw2 = c3.select_slider("binWidth", [5, 10, 15, 20, 25, 50], value=25, key="binw2")

        if param == "半径 radius":
            values = np.linspace(4, 16, n_points).round().astype(int)
            fixed = dict(noise=10.0, tissue=100.0, shape="sphere")
            xlabel = "半径（体素）"
        elif param == "噪声 σ":
            values = np.linspace(0, 40, n_points).round(1)
            fixed = dict(radius=8, tissue=100.0, shape="sphere")
            xlabel = "噪声 σ（HU）"
        else:
            values = np.linspace(0, 300, n_points).round().astype(int)
            fixed = dict(radius=8, noise=10.0, shape="sphere")
            xlabel = "组织密度（HU）"

        if st.button("▶️ 开始扫描", type="primary"):
            curves: dict[str, list[float]] = {k: [] for k in WATCH_FEATURES}
            progress = st.progress(0.0, text="计算中…")
            for i, v in enumerate(values):
                kw = dict(fixed)
                if param == "半径 radius":
                    kw["radius"] = int(v)
                elif param == "噪声 σ":
                    kw["noise"] = float(v)
                else:
                    kw["tissue"] = float(v)
                f = _features(int(kw["radius"]), float(kw["noise"]),
                              float(kw["tissue"]), str(kw["shape"]), 0, float(binw2))
                for k in WATCH_FEATURES:
                    curves[k].append(f.get(k, np.nan))
                progress.progress((i + 1) / len(values), text=f"计算中… {i+1}/{len(values)}")
            progress.empty()
            st.session_state["sweep"] = {
                "values": list(values), "curves": curves,
                "param": param, "xlabel": xlabel,
            }

        sweep = st.session_state.get("sweep")
        if sweep:
            st.success(f"扫描完成：{sweep['param']} 共 {len(sweep['values'])} 个取值")

            # —— 敏感性排序：用变异系数衡量 ——
            rows = []
            for k, ys in sweep["curves"].items():
                arr = np.array(ys, dtype=float)
                arr = arr[np.isfinite(arr)]
                if arr.size == 0 or abs(arr.mean()) < 1e-12:
                    continue
                cv = arr.std() / abs(arr.mean())          # 变异系数
                rows.append({
                    "特征": PRETTY[k],
                    "变异系数 CV": round(float(cv), 4),
                    "最小": round(float(arr.min()), 4),
                    "最大": round(float(arr.max()), 4),
                    "相对变化": f"{(arr.max()-arr.min())/abs(arr.mean())*100:.1f}%",
                })
            sens = pd.DataFrame(rows).sort_values("变异系数 CV", ascending=False)

            st.markdown("#### 敏感性排行榜（变异系数越大越敏感）")
            st.dataframe(sens, hide_index=True, width="stretch")

            st.markdown("#### 特征随参数的变化曲线")
            picks = st.multiselect(
                "选择要画的特征（建议选 3–5 个）",
                list(PRETTY.values()),
                default=[PRETTY[k] for k in
                         ["original_shape_MeshVolume", "original_firstorder_Entropy",
                          "original_glcm_Contrast", "original_ngtdm_Busyness"]],
            )
            rev = {v: k for k, v in PRETTY.items()}
            fig = go.Figure()
            for label in picks:
                k = rev[label]
                fig.add_trace(go.Scatter(x=sweep["values"], y=sweep["curves"][k],
                                         mode="lines+markers", name=label))
            fig.update_layout(
                xaxis_title=sweep["xlabel"],
                yaxis_title="特征值（原始量纲，故用对数轴便于同图比较）",
                yaxis_type="log",
                height=460, margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            st.plotly_chart(fig, width="stretch")

            st.info(
                "**读数提示**：曲线平坦 = 该特征对参数不敏感（稳健）；曲线陡峭 = 敏感（不可靠）。"
                "临床研究要挑**稳健**的特征，否则换台机器结论就翻了。",
                icon="📌",
            )
