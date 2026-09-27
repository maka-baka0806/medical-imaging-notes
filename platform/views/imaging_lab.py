"""影像实验室：载入影像 → 分割 → 提取放射组学特征 → 导出。"""
from __future__ import annotations

import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from core.phantom import (FEATURE_FAMILIES, extract_features, group_features,
                          make_sphere_phantom, slice_view, to_records, to_sitk)
from core.plotting import setup_cjk_font

setup_cjk_font()   # 让图中中文正常显示

AXES = {"轴位 (Axial)": 0, "冠状位 (Coronal)": 1, "矢状位 (Sagittal)": 2}


@st.cache_data(show_spinner=False)
def _load_nifti(data: bytes) -> np.ndarray:
    import SimpleITK as sitk
    img = sitk.ReadImage(data)
    return sitk.GetArrayFromImage(img)


@st.cache_data(show_spinner="正在提取放射组学特征…")
def _extract(image: np.ndarray, mask: np.ndarray, spacing: tuple, bin_width: float):
    from core.phantom import Phantom
    ph = Phantom(image=image, mask=mask.astype(bool), radius=0, spacing=spacing)
    img, msk = to_sitk(ph)
    return extract_features(img, msk, bin_width=bin_width)


def _show_slice(volume: np.ndarray, mask: np.ndarray | None, axis: int, index: int,
                title: str = "") -> None:
    img2d, m2d = slice_view(volume, mask, axis=axis, index=index)
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    ax.imshow(img2d, cmap="gray", aspect="equal")
    if m2d is not None:
        overlay = np.ma.masked_where(~m2d, m2d)
        ax.imshow(overlay, cmap="autumn", alpha=0.35, aspect="equal")
    ax.set_title(f"{title} ｜ 第 {index} 层", fontsize=11)
    ax.axis("off")
    fig.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def render() -> None:
    st.title("🔬 影像实验室")
    st.markdown(
        "完整走一遍放射组学流程：**影像 → 分割（勾画 ROI）→ 特征提取 → 导出**。"
        "这是所有放射组学论文的骨架。"
    )

    # ---------------- 数据来源 ----------------
    st.subheader("① 选择影像")
    source = st.radio("数据来源", ["内置合成体模", "上传 NIfTI 文件 (.nii / .nii.gz)"],
                      horizontal=True, label_visibility="collapsed")

    if source == "内置合成体模":
        c1, c2, c3, c4 = st.columns(4)
        shape_cn = c1.selectbox("病灶形状", ["球 sphere", "椭球 ellipsoid", "立方 cube"])
        radius = c2.slider("半径（体素）", 4, 18, 8)
        noise = c3.slider("噪声 σ（HU）", 0.0, 40.0, 10.0, 1.0)
        tissue = c4.slider("组织密度（HU）", -200, 300, 100, 10)
        size = 48
        shape = {"球 sphere": "sphere", "椭球 ellipsoid": "ellipsoid",
                 "立方 cube": "cube"}[shape_cn]
        ph = make_sphere_phantom(size=size, radius=radius, tissue_hu=float(tissue),
                                 noise_sd=float(noise), shape=shape)
        volume, spacing = ph.image, ph.spacing
        st.caption(f"体模：{size}³ 体素 · 间距 {spacing[0]} mm · "
                   f"理论体积 {ph.true_volume_mm3:.1f} mm³")
    else:
        up = st.file_uploader("上传影像（支持 NIfTI；MRI/CT 均可）", type=["nii", "gz"])
        if up is None:
            st.info("请上传一个 .nii 或 .nii.gz 文件。没有数据？可先用「内置合成体模」熟悉流程。")
            return
        try:
            volume = _load_nifti(up.getvalue()).astype(np.float32)
        except Exception as e:
            st.error(f"读取失败：{e}")
            return
        spacing = (1.0, 1.0, 1.0)
        st.success(f"读取成功：形状 {volume.shape}，强度范围 {volume.min():.1f} ~ {volume.max():.1f}")

    # ---------------- 显示 ----------------
    st.subheader("② 查看影像")
    c1, c2, c3 = st.columns([1, 1, 2])
    axis_name = c1.selectbox("视角", list(AXES), index=0)
    axis = AXES[axis_name]
    idx = c2.slider("层号", 0, volume.shape[axis] - 1, volume.shape[axis] // 2)

    mask = None
    if source == "内置合成体模":
        mask = ph.mask
        _show_slice(volume, mask, axis, idx, "已知的真值掩膜（金色）")
        st.caption("金色区域是体模的**真值掩膜** —— 相当于医生勾画的 ROI。")
    else:
        _show_slice(volume, None, axis, idx, "原始影像")

    # ---------------- 分割 ----------------
    st.subheader("③ 分割（定义 ROI）")
    if source == "内置合成体模":
        seg_mode = "使用真值掩膜"
        st.radio("分割方式", ["使用真值掩膜", "改用阈值法"],
                 horizontal=True, label_visibility="collapsed", key="seg_mode_builtin")
        seg_mode = st.session_state.get("seg_mode_builtin", "使用真值掩膜")
    else:
        seg_mode = "阈值法"
        st.caption("上传的影像用阈值法做简易分割（临床研究里这一步通常由医生勾画或 AI 自动分割）。")

    if seg_mode == "阈值法":
        lo, hi = float(np.percentile(volume, 1)), float(np.percentile(volume, 99))
        thr = st.slider("强度阈值（≥ 该值的体素判为 ROI）", lo, hi, (lo + hi) / 2)
        mask = volume >= thr
        st.caption(f"当前 ROI 体素数：**{int(mask.sum())}**")
        if mask.sum() == 0:
            st.error("阈值过高，ROI 为空 —— 请调低阈值。")
            return
        _show_slice(volume, mask, axis, idx, "阈值分割结果（金色）")

    # ---------------- 提取特征 ----------------
    st.subheader("④ 提取放射组学特征")
    c1, c2 = st.columns([1, 3])
    bin_width = c1.select_slider("灰度分箱宽度 binWidth（HU）", [5, 10, 15, 20, 25, 50], value=25)
    c2.caption(
        "**binWidth 是最重要的一个参数**：它决定灰度被离散化成多少级。"
        "换一个值，纹理特征就会变 —— 这正是 2024 年那篇 PET 离散化论文要回答的问题。"
    )

    if st.button("🚀 开始提取特征", type="primary"):
        with st.spinner("PyRadiomics 正在计算…"):
            feats = _extract(volume, mask, tuple(spacing), float(bin_width))
        st.session_state["feats"] = feats

    feats = st.session_state.get("feats")
    if feats:
        grouped = group_features(feats)
        st.success(f"✅ 提取完成：共 **{len(feats)}** 个特征，覆盖 {len(grouped)} 个特征家族")

        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("**各家族特征数**")
            st.bar_chart(pd.Series({k: len(v) for k, v in grouped.items()}))
        with c2:
            st.markdown("**形状特征 vs 理论值**（用于检验正确性）")
            if "shape" in grouped and source == "内置合成体模":
                mv = grouped["shape"].get("MeshVolume", float("nan"))
                tv = ph.true_volume_mm3
                st.metric("网格体积", f"{mv:.1f} mm³",
                          delta=f"{100 * (mv - tv) / tv:+.2f}% vs 理论值 {tv:.1f}")
                st.caption("误差来自体素化（把球切成小方块）—— 0.5%~2% 是正常的。")

        st.markdown("**按家族查看特征**")
        for fam, items in grouped.items():
            with st.expander(f"{fam} · {FEATURE_FAMILIES.get(fam, '')} （{len(items)} 个）"):
                st.dataframe(
                    pd.DataFrame(sorted(items.items()), columns=["特征名", "数值"]),
                    width="stretch", hide_index=True)

        # 导出
        df = pd.DataFrame(to_records(feats))
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        st.download_button("⬇️ 导出全部特征（CSV）", buf.getvalue().encode("utf-8-sig"),
                           file_name="radiomics_features.csv", mime="text/csv")

        st.info(
            "**下一步**：把 binWidth 从 25 改成 10 或 50，重新提取，对比同一特征的变化 —— "
            "你会亲眼看到「特征稳健性」问题的来源。",
            icon="💡",
        )
