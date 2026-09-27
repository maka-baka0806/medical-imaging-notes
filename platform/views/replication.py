"""文献复现专栏：逐步骤复现杨老师论文的方法学。"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.plotting import setup_cjk_font
from core.replication import PAPERS, get_paper
from core.theme import ACCENT as DUKE_ACCENT, PRIMARY as DUKE_BLUE
from core.theme import paper_block, step_marker
from core.capabilities import require

setup_cjk_font()


# ----------------------------------------------------------------------
# 每篇论文的「复现结果可视化」
# ----------------------------------------------------------------------
def _viz(pid: str, st_: dict) -> None:
    if pid == "R1" and "filter" in st_:
        ph, res = st_["phantom"], st_["filter"]
        fig, axes = plt.subplots(1, 4, figsize=(17, 4.4))
        panels = [
            (ph.ct[32], "输入 CT", "gray"),
            (res.maps["std"][32], "局部标准差（特征图）", "inferno"),
            (ph.reference[32], "参考通气图（金标准）", "viridis"),
            (ph.defect[32], "真实缺损区", "gray"),
        ]
        for ax, (img, title, cm) in zip(axes, panels):
            ax.imshow(img, cmap=cm); ax.set_title(title, fontsize=11); ax.axis("off")
        fig.tight_layout(); st.pyplot(fig, width="stretch"); plt.close(fig)
    elif pid == "R2" and "uq" in st_:
        ph, uq = st_["phantom"], st_["uq"]
        fig, axes = plt.subplots(1, 4, figsize=(17, 4.4))
        for ax, (img, title, cm) in zip(axes, [
            (ph.image[28], "输入影像", "gray"),
            (st_["single"][28], "单次分割", "gray"),
            (uq.consensus[28], "12 视角共识", "gray"),
            (uq.entropy[28], "不确定性（熵）", "magma"),
        ]):
            im = ax.imshow(img, cmap=cm)
            ax.set_title(title, fontsize=11); ax.axis("off")
            if "熵" in title:
                fig.colorbar(im, ax=ax, fraction=0.046)
        fig.tight_layout(); st.pyplot(fig, width="stretch"); plt.close(fig)
    elif pid == "R3" and "sphere" in st_:
        case, sp = st_["case"], st_["sphere"]
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
        axes[0].imshow(case.dose[32], cmap="jet")
        axes[0].set_title(f"剂量分布（{case.n_targets} 个靶点）", fontsize=11); axes[0].axis("off")
        im = axes[1].imshow(sp.density, cmap="Blues", aspect="auto")
        axes[1].set_title("球形投影（2D 球面图）", fontsize=11)
        axes[1].set_xlabel("方位角 θ"); axes[1].set_ylabel("极角 φ")
        fig.colorbar(im, ax=axes[1], fraction=0.046)
        fig.tight_layout(); st.pyplot(fig, width="stretch"); plt.close(fig)
    elif pid == "R4" and "fusion" in st_:
        df = st_["fusion"]
        fig = go.Figure(go.Bar(
            x=df["特征来源"], y=df["AUC"],
            marker_color=[DUKE_ACCENT if "+" in s else DUKE_BLUE for s in df["特征来源"]]))
        fig.update_layout(height=380, yaxis_title="AUC", margin=dict(l=10, r=10, t=20, b=10))
        fig.update_xaxes(tickangle=-25)
        st.plotly_chart(fig, width="stretch")
    elif pid == "R5" and "strat" in st_:
        fig = go.Figure()
        for label, color in [("低风险", DUKE_BLUE), ("高风险", DUKE_ACCENT)]:
            km = st_["strat"][label]["KM"]
            fig.add_trace(go.Scatter(x=km["时间"], y=km["生存概率"] * 100, mode="lines",
                                     name=label, line=dict(color=color, shape="hv")))
        fig.update_layout(xaxis_title="随访时间（月）", yaxis_title="生存率 (%)",
                          height=420, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, width="stretch")
    elif pid == "R6" and "case0" in st_:
        dth, dose = st_["case0"]
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
        axes[0].scatter(dth, dose, s=3, alpha=0.25, color=DUKE_BLUE)
        axes[0].set_xlabel("距靶区距离 DTH (mm)"); axes[0].set_ylabel("剂量 (Gy)")
        axes[0].set_title("距离-剂量关系", fontsize=11)
        if "kde" in st_:
            xs, ys, _ = st_["kde"]
            axes[1].plot(xs, ys, color=DUKE_BLUE, lw=2)
            axes[1].axvline(st_["knn"]["test"], color=DUKE_ACCENT, ls="--",
                            label=f"真实 D2cc={st_['knn']['test']:.2f}")
            axes[1].axvline(float(np.median(st_["knn"]["sel"])), color="green", ls=":",
                            label=f"预测={np.median(st_['knn']['sel']):.2f}")
            axes[1].set_xlabel("D2cc (Gy)"); axes[1].set_ylabel("概率密度")
            axes[1].set_title("KDE 预测分布", fontsize=11); axes[1].legend(fontsize=8)
        fig.tight_layout(); st.pyplot(fig, width="stretch"); plt.close(fig)
    elif pid == "R8" and "node" in st_:
        res = st_["node"]
        X, y = st_["data"]
        fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
        # 输入数据
        axes[0].scatter(X[y == 0, 0], X[y == 0, 1], s=8, alpha=0.6, color=DUKE_BLUE, label="类 0")
        axes[0].scatter(X[y == 1, 0], X[y == 1, 1], s=8, alpha=0.6, color=DUKE_ACCENT, label="类 1")
        axes[0].set_title("输入数据（线性不可分）", fontsize=11); axes[0].legend(fontsize=8)
        # 轨迹：抽 40 个样本，画出 8 个时间点的位置连线
        idx = np.r_[np.where(y == 0)[0][:20], np.where(y == 1)[0][:20]]
        for i in idx:
            traj = res.trajectories[:, i, :]
            color = DUKE_BLUE if y[i] == 0 else DUKE_ACCENT
            axes[1].plot(traj[:, 0], traj[:, 1], color=color, alpha=0.45, lw=0.9)
        axes[1].scatter(res.trajectories[0, idx, 0], res.trajectories[0, idx, 1],
                        s=12, color="gray", alpha=0.5, label="t=0")
        axes[1].scatter(res.trajectories[-1, idx, 0], res.trajectories[-1, idx, 1],
                        s=12, color="black", alpha=0.6, label="t=1")
        axes[1].set_title("潜空间轨迹（每个样本一条线）", fontsize=11); axes[1].legend(fontsize=8)
        # 分离度曲线
        axes[2].plot(res.times, res.separation, "o-", color=DUKE_BLUE, lw=2)
        axes[2].set_xlabel("演化时间 t"); axes[2].set_ylabel("两类质心距离")
        axes[2].set_title("类间分离度随演化单调上升", fontsize=11)
        fig.tight_layout(); st.pyplot(fig, width="stretch"); plt.close(fig)
    elif pid == "R9" and "series" in st_:
        lung, ser = st_["lung"], st_["series"]
        di, hi, dh, hh = st_["curves"]
        fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))
        ph = np.arange(len(lung.phase_names))
        axes[0].plot(ph, di, "o-", color=DUKE_ACCENT, lw=2, label="缺损区")
        axes[0].plot(ph, hi, "s-", color=DUKE_BLUE, lw=2, label="健康区")
        axes[0].set_xticks(ph); axes[0].set_xticklabels(lung.phase_names)
        axes[0].set_xlabel("呼吸相位"); axes[0].set_ylabel("局部强度 (HU)")
        axes[0].set_title("核心图：强度随呼吸的变化", fontsize=11); axes[0].legend(fontsize=9)
        axes[1].plot(ph, dh, "o-", color=DUKE_ACCENT, lw=2, label="缺损区")
        axes[1].plot(ph, hh, "s-", color=DUKE_BLUE, lw=2, label="健康区")
        axes[1].set_xticks(ph); axes[1].set_xticklabels(lung.phase_names)
        axes[1].set_xlabel("呼吸相位"); axes[1].set_ylabel("局部均匀性")
        axes[1].set_title("均匀性变化", fontsize=11); axes[1].legend(fontsize=9)
        axes[2].imshow(lung.volume[7, 24], cmap="gray")
        axes[2].imshow(np.ma.masked_where(~lung.defect[24], lung.defect[24]),
                       cmap="autumn", alpha=0.45)
        axes[2].set_title("相位 70%（呼气末）与缺损区", fontsize=11); axes[2].axis("off")
        fig.tight_layout(); st.pyplot(fig, width="stretch"); plt.close(fig)
    elif pid == "R7" and "reg" in st_:
        case, res = st_["case"], st_["reg"]
        from core.registration import jacobian_determinant
        det = jacobian_determinant(res["dvf"])
        fig, axes = plt.subplots(1, 4, figsize=(17, 4.4))
        for ax, (img, title, kw) in zip(axes, [
            (case.fixed[24], "参考图像", dict(cmap="gray")),
            (case.moving[24], "待配准图像", dict(cmap="gray")),
            (res["warped"][24], "配准后", dict(cmap="gray")),
            (det[24], "Jacobian 行列式", dict(cmap="RdBu_r", vmin=0.5, vmax=1.5)),
        ]):
            im = ax.imshow(img, **kw); ax.set_title(title, fontsize=11); ax.axis("off")
            if "Jacobian" in title:
                fig.colorbar(im, ax=ax, fraction=0.046)
        fig.tight_layout(); st.pyplot(fig, width="stretch"); plt.close(fig)


def _render_payload(kind: str, payload) -> None:
    if kind == "metrics" and isinstance(payload, dict):
        keys = list(payload)
        for i in range(0, len(keys), 4):
            cols = st.columns(min(4, len(keys) - i))
            for col, k in zip(cols, keys[i:i + 4]):
                v = payload[k]
                col.metric(str(k), v if isinstance(v, str) else
                           (f"{v:.4g}" if isinstance(v, float) else v))
    elif kind == "table" and isinstance(payload, pd.DataFrame):
        st.dataframe(payload, hide_index=True, width="stretch")
    elif kind == "text":
        st.markdown(str(payload))
    else:
        st.write(payload)


def render() -> None:
    if not require("scipy", "文献复现专栏"):
        return
    st.title("文献复现专栏")
    st.markdown(
        "把杨老师论文的方法学**拆成可逐步执行的步骤**，每一步都能单独运行、单独看结果。"
        "所有步骤都用合成数据（真实临床数据需申请），因此复现的是**方法学与结论方向**。"
    )

    with st.sidebar:
        st.markdown("#### 选择文献")
        labels = [f"{p.id} · {p.name[:16]}…" for p in PAPERS]
        idx = st.radio("文献列表", range(len(PAPERS)),
                       format_func=lambda i: f"{PAPERS[i].id} · {PAPERS[i].name.split('：')[0]}",
                       label_visibility="collapsed")
        st.caption("R1–R7 共 7 篇，覆盖他五条主要技术线。")

    paper = PAPERS[idx]
    state_key = f"repl_{paper.id}"
    state = st.session_state.setdefault(state_key, {"__step__": 0})

    # ---- 文献信息卡 ----
    st.markdown(
        paper_block([paper.id, paper.position], paper.name,
                    paper.goal, paper.difference),
        unsafe_allow_html=True,
    )

    n = len(paper.steps)
    done = state["__step__"]
    st.progress(done / n, text=f"复现进度：{done} / {n} 步")

    c1, c2, c3, c4 = st.columns([1, 1, 1, 3])
    if c1.button(" 运行下一步", type="primary", disabled=done >= n):
        step = paper.steps[done]
        with st.spinner(f"正在执行：{step.title}"):
            try:
                payload = step.fn(state)
                state.setdefault("__results__", {})[done] = (step.kind, payload)
                state["__step__"] = done + 1
                st.rerun()
            except Exception as e:
                st.error(f"第 {done+1} 步执行失败：{type(e).__name__}: {e}")
    if c2.button("⏭ 运行全部", disabled=done >= n):
        for i in range(done, n):
            step = paper.steps[i]
            try:
                payload = step.fn(state)
                state.setdefault("__results__", {})[i] = (step.kind, payload)
                state["__step__"] = i + 1
            except Exception as e:
                st.error(f"第 {i+1} 步失败：{type(e).__name__}: {e}")
                break
        st.rerun()
    if c3.button(" 重置"):
        st.session_state[state_key] = {"__step__": 0}
        st.rerun()

    st.divider()

    # ---- 步骤结果 ----
    results = state.get("__results__", {})
    for i, step in enumerate(paper.steps):
        finished = i in results
        state = "done" if finished else ("now" if i == done else "todo")
        with st.expander(step.title, expanded=finished and i == done - 1):
            st.markdown(step.detail)
            if finished:
                kind, payload = results[i]
                _render_payload(kind, payload)
                if step.note:
                    st.caption(f" {step.note}")
            else:
                st.caption("尚未运行 —— 点上方「运行下一步」。")

    # ---- 复现结果可视化 ----
    if done > 0:
        st.markdown("---")
        st.subheader("复现结果可视化")
        try:
            _viz(paper.id, state)
        except Exception as e:
            st.caption(f"（可视化暂不可用：{type(e).__name__}）")

    if done == n:
        st.success(f" R{paper.id[1]} 全部 {n} 步复现完成", icon="")
        if paper.conclusion:
            st.markdown(paper.conclusion)
