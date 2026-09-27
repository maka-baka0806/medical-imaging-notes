"""学习路线页：12 周计划 + 进度跟踪（进度保存在本地 JSON）。"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
PROGRESS_FILE = DATA_DIR / "progress.json"

WEEKS = [
    (1, "工具生存技能", "Python 基础语法 · Linux 常用命令 · Git 提交",
     "能在 GitHub 上新建仓库并提交"),
    (2, "数组与绘图", "NumPy 索引/广播 · matplotlib 画图 · 通读术语库 L1 条目",
     "会用数组做切片与广播运算"),
    (3, "医学影像 IO", "SimpleITK 读写 · 3D Slicer 安装与勾画 · DICOM/NIfTI 格式",
     "能读一套影像并手动勾画 ROI"),
    (4, "影像物理基础", "HU 与窗宽窗位 · 体素间距 · 重采样与插值",
     "能写一个重采样脚本"),
    (5, "放射组学入门", "PyRadiomics 提取特征 · 理解 7 大特征家族",
     "提出一张影像的 100+ 特征"),
    (6, "统计与相关分析", "Spearman 秩相关 · 可视化 · 复现肺放射组学滤波的简化版",
     "完成第一个「迷你复现」"),
    (7, "经典机器学习", "scikit-learn · 交叉验证 · ROC/AUC · 类别不平衡",
     "跑出 ROC 曲线并解释 AUC"),
    (8, "深度学习入门", "PyTorch 张量/自动求导 · 手写两层网络的前向与反向",
     "手写网络训到收敛"),
    (9, "图像分割", "卷积与 U-Net 原理 · 亲手实现 2D U-Net · Dice 指标",
     "在自己的数据上跑出 Dice"),
    (10, "工程化", "nnU-Net 官方教程 · 数据准备/训练/推理/评估全流程",
     "跑通完整的 nnU-Net 流程"),
    (11, "不确定性量化", "多次推理 → 方差图 · 熵 · 与错误区域的重叠分析",
     "画出「模型哪里没把握」热力图"),
    (12, "产出与连接", "写 5 页报告 · 推 GitHub · 给老师写邮件",
     "邮件已发出"),
]

MATH_TASKS = {
    1: "微积分复习：偏导数与梯度",
    2: "线性代数：矩阵运算、特征值",
    3: "线性代数：SVD 与 PCA",
    4: "概率统计：分布、期望、方差",
    5: "概率统计：相关与假设检验",
    6: "统计推断：置信区间、p 值的真实含义",
    7: "最优化：梯度下降与正则化",
    8: "微积分：链式法则与反向传播",
    9: "信号处理：卷积与滤波",
    10: "数值方法：插值与重采样",
    11: "概率：熵与不确定性",
    12: "按课题需要补",
}


def _load() -> dict:
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                             encoding="utf-8")


def render() -> None:
    st.title(" 学习路线")
    st.markdown(
        "12 周可执行计划。每周只有**一个交付物**——不要贪多，做完一个再走下一步。"
        "进度保存在本地 `platform/data/progress.json`。"
    )

    progress = _load()
    total = len(WEEKS)
    done = sum(1 for w, *_ in WEEKS if progress.get(f"week{w}"))

    c1, c2 = st.columns([3, 1])
    with c1:
        st.progress(done / total, text=f"已完成 {done} / {total} 周")
    with c2:
        if st.button(" 重置进度"):
            _save({})
            st.rerun()

    st.divider()

    for week, title, tasks, deliverable in WEEKS:
        key = f"week{week}"
        checked = bool(progress.get(key))
        icon = "" if checked else ""
        with st.expander(f"{icon} 第 {week} 周 · {title}", expanded=(week == done + 1)):
            st.markdown(f"**任务**：{tasks}")
            st.markdown(f"**数学同步**：{MATH_TASKS[week]}")
            st.markdown(f"**完成标志**：{deliverable}")
            new = st.checkbox("标记本周已完成", value=checked, key=f"cb_{key}")
            if new != checked:
                progress[key] = new
                _save(progress)
                st.rerun()

    st.divider()
    st.subheader("里程碑作品（可写进邮件给老师）")
    st.markdown(
        """
- [ ] 手写 Dice / IoU / HD95，并构造典型错误对比
- [ ] 用 NumPy 实现 3D 滑窗，生成放射组学特征图
- [ ] 训练 2D U-Net 做分割，报告 Dice 与 HD95
- [ ] 多次推理 → 计算方差 → 画不确定性热力图
        """
    )
    st.caption("每完成一个，就在 GitHub 仓库里提交一次，README 里打勾。")

    st.info(
        "**关于节奏**：每周建议投入 数学 4h + 编程 8h + 领域阅读 3h + 复盘 1h。"
        "学期中做不到就砍数学时长，但**编程不要断**。",
        icon="⏱",
    )
