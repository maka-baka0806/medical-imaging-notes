"""概览页：Duke 风格首屏 + 文献映射。"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.env_check import check_tools, summary
from core.glossary_parser import load_terms
from core.theme import card, hero

REPO = Path(__file__).resolve().parents[2]

MODULES = [
    ("01", "体素级放射组学滤波", "3D 滑窗逐体素算特征，把「一个数」变成「一张图」，"
     "并与参考通气图做体素级相关分析。", "Med Phys 2022 · arXiv:2503.23898（肺通气）"),
    ("02", "分割与不确定性", "七种分割算法同台对比 + 多视角扰动不确定性；"
     "检验「高不确定区是否真的更易出错」。", "Med Phys 2024/2026 · Front Oncol 2025（SPU-Net）"),
    ("03", "特征建模与预后", "多共线性评估 → PCA/差异性选择 → LR/SVM/RF → 交叉验证 → "
     "三源融合 → Kaplan-Meier 生存分层。", "Front Oncol 2023（MFC）· 2024（双放射组学）"),
    ("04", "放疗剂量学工具", "DVH 与剂量指标（D2cc/V10Gy）、Gamma 指数（3%/2mm）、"
     "以及 SCNN 的球形投影变换。", "Med Phys 2025（SIMT）· Front Oncol 2022（HDR DVH）"),
    ("05", "形变配准与物理合理性", "SimpleITK 形变配准 + DVF + Jacobian 行列式，"
     "判断形变是否物理合理（组织不能自我折叠）。", "Phys Imaging Radiat Oncol 2026（PhysMorph）"),
    ("06", "影像实验室", "上传自己的 NIfTI 影像，走完整的「分割 → 提取 107 个特征 → 导出 CSV」流程。",
     "通用流程（放射组学标准工作流）"),
    ("07", "体模实验台", "拖动滑杆改变病灶参数，实时观察特征如何变化；"
     "参数敏感性扫描输出排行榜。", "对应「特征稳健性」系列研究"),
    ("08", "术语库 · 学习路线 · 工具链", "177 条术语可搜索；12 周计划可勾选；"
     "环境自检与启动命令。", "——"),
]


def _git_commits() -> int | None:
    try:
        import subprocess
        out = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=REPO,
                             capture_output=True, text=True, timeout=5)
        return int(out.stdout.strip()) if out.returncode == 0 else None
    except Exception:
        return None


def render() -> None:
    st.markdown(
        hero("Duke Kunshan University · Medical Physics",
             "医学影像 AI 学习平台",
             "依据杨振宇老师已发表工作构建：从看懂一个名词，到亲手复现他课题组的主流方法。"),
        unsafe_allow_html=True,
    )

    terms = load_terms()
    tools = check_tools()
    ok, total = summary(tools)
    commits = _git_commits()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("复现模块", "5", help="对应他五条主要技术线")
    c2.metric("术语库", f"{len(terms)} 条", help="可全文搜索")
    c3.metric("科研工具就绪", f"{ok}/{total}")
    c4.metric("仓库提交", commits if commits else "—")

    st.markdown('<hr class="dku-rule">', unsafe_allow_html=True)
    st.subheader("平台模块与文献映射")
    st.caption("每个模块都对应杨老师的具体论文，页面内附「对应文献」与核心结论解读。")

    for row_start in range(0, len(MODULES), 3):
        cols = st.columns(3)
        for col, (idx, title, body, src) in zip(cols, MODULES[row_start:row_start + 3]):
            with col:
                st.markdown(card(idx, title, body, src), unsafe_allow_html=True)
        st.write("")

    st.markdown('<hr class="dku-rule">', unsafe_allow_html=True)

    left, right = st.columns([1.15, 1])
    with left:
        st.subheader("这个平台覆盖了他工作的哪些部分")
        st.markdown(
            """
| 技术线 | 代表工作 | 平台模块 |
|---|---|---|
| 体素级放射组学 | Med Phys 2022 肺通气 | 🧬 放射组学滤波 |
| 不确定性量化 | Med Phys 2024/2026、国自然青年项目 | 🎯 分割与不确定性 |
| 多源特征融合 | Front Oncol 2023 MFC、2024 双放射组学 | 📈 特征建模与预后 |
| 放疗剂量学 | Med Phys 2025 SIMT、Front Oncol 2022 DVH | ☢️ 剂量学工具 |
| 形变配准 | Phys Imaging Radiat Oncol 2026 PhysMorph | 🫀 形变配准 |
| 可解释 AI | 科学通报 2025 综述 | 📈 置换重要性 · 🎯 不确定性图 |
| 时序建模（4DCT） | arXiv:2503.23898 | 🧬 特征序列分析（规划中） |

> **尚未覆盖**：Neural ODE / HBNODE 决策轨迹可视化、球面卷积网络的完整训练、
> 影像基因组学融合 —— 需要预训练模型或真实基因组数据，平台预留了扩展位。
            """
        )
    with right:
        st.subheader("建议使用顺序")
        st.markdown(
            """
1. **📚 术语库** —— 先建立词汇量，只看 `L1` 条目
2. **🧪 体模实验台** —— 建立「特征对什么敏感」的直觉
3. **🧬 放射组学滤波** —— 理解他最具代表性的方法
4. **🎯 分割与不确定性** —— 理解他当前的核心方向
5. **📈 特征建模与预后** —— 走通一篇论文的完整方法学
6. **☢️ 剂量学 / 🫀 配准** —— 按兴趣深入
7. **🔬 影像实验室** —— 换成你自己的数据
            """
        )
        st.info(
            "**所有计算都在本地完成**，影像数据不上传任何服务器 —— "
            "这对将来处理真实临床数据是硬要求。",
            icon="🔒",
        )

    st.markdown('<hr class="dku-rule">', unsafe_allow_html=True)
    st.caption(
        "仓库：[medical-imaging-notes](https://github.com/maka-baka0806/medical-imaging-notes)　·　"
        "环境：conda `medimg`（Python 3.11 · PyRadiomics · PyTorch · SimpleITK）　·　"
        "全部页面通过 AppTest 冒烟测试"
    )
