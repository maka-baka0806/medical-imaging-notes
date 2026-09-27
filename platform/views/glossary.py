"""术语库页：搜索、筛选、阅读 177 条术语。"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core.glossary_parser import file_label, load_terms

DIFF_LABEL = {
    "L1": "L1 · 看一遍就懂",
    "L2": "L2 · 需要一点数学/医学背景",
    "L3": "L3 · 得动手做过才真懂",
}
EVID_LABEL = {
    "✅": "✅ 论文明确写明使用",
    "🔶": "🔶 作为对比方法/参考文献出现",
    "⚪": "⚪ 领域通用但论文未记载",
}


@st.cache_data(show_spinner=False)
def _terms():
    terms = load_terms()
    return [
        {
            "term": t.term, "difficulty": t.difficulty, "evidence": t.evidence,
            "definition": t.definition, "details": t.details,
            "section": t.section, "group": t.group, "source": t.source,
        }
        for t in terms
    ]


def render() -> None:
    st.title("📚 术语库")
    terms = _terms()

    if not terms:
        st.error("未找到术语数据，请确认 glossary/ 目录存在。")
        return

    # ---------------- 侧边筛选 ----------------
    with st.sidebar:
        st.markdown("#### 筛选")
        kw = st.text_input("搜索（中英文均可）", placeholder="如：Dice、剂量、不确定性")
        files = sorted({t["source"] for t in terms})
        pick_files = st.multiselect("主题文件", files,
                                    format_func=file_label, default=files)
        diffs = st.multiselect("难度", ["L1", "L2", "L3"], default=["L1", "L2", "L3"],
                               format_func=lambda d: DIFF_LABEL[d])
        only_evid = st.checkbox("只看有证据标记的工具类词条", value=False)
        st.caption("L1 先全部掌握，再攻 L2/L3。")

    # ---------------- 过滤 ----------------
    result = []
    for t in terms:
        if pick_files and t["source"] not in pick_files:
            continue
        if t["difficulty"] and t["difficulty"] not in diffs:
            continue
        if only_evid and t["evidence"] not in EVID_LABEL:
            continue
        if kw:
            haystack = " ".join([t["term"], t["definition"], *t["details"]]).lower()
            if kw.lower() not in haystack:
                continue
        result.append(t)

    st.caption(f"共 {len(terms)} 条术语，当前筛选出 **{len(result)}** 条")

    # ---------------- 统计图 ----------------
    tab1, tab2, tab3 = st.tabs(["📖 词条", "📊 分布统计", "🔀 易混淆对照"])

    with tab1:
        if not result:
            st.warning("没有匹配的词条，试试放宽筛选条件。")
        for t in result:
            badge = []
            if t["difficulty"]:
                badge.append(f"`{t['difficulty']}`")
            if t["evidence"]:
                badge.append(t["evidence"])
            head = f"{t['term']}　{' '.join(badge)}"
            with st.expander(head, expanded=False):
                st.markdown(f"**{t['definition']}**" if t["definition"] else "")
                for d in t["details"]:
                    st.markdown(f"- {d}")
                st.caption(f"所属：{t['section']}　｜　来源：{file_label(t['source'])}")
                if t["evidence"]:
                    st.caption(EVID_LABEL.get(t["evidence"], ""))

    with tab2:
        df = pd.DataFrame(result)
        if not df.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**各主题词条数**")
                by_file = df["source"].map(file_label).value_counts()
                st.bar_chart(by_file)
            with c2:
                st.markdown("**难度分布**")
                diff_counts = df["difficulty"].replace("", "未标记").value_counts()
                st.bar_chart(diff_counts)

            st.markdown("**下载当前筛选结果（CSV）**")
            st.download_button(
                "⬇️ 下载 CSV",
                df[["term", "difficulty", "evidence", "definition"]]
                  .to_csv(index=False).encode("utf-8-sig"),
                file_name="glossary_selection.csv",
                mime="text/csv",
            )

    with tab3:
        st.markdown("最容易混淆的 8 组词（来自术语库附录）")
        st.markdown(
            """
| 容易混 | 区别 |
|---|---|
| **GLCOM vs GLCM** | 同一个东西（灰度共生矩阵），论文里写 GLCOM，国际标准写 GLCM |
| **两个"蒙特卡洛"** | MCCV = 统计重采样；Monte Carlo 输运 = 粒子剂量模拟 |
| **Dice vs HD95** | 前者看"重叠多少"，后者看"边界差多远"；Dice 高不等于边界准 |
| **灵敏度 vs 特异度** | 找得全 vs 排得准；提高一个通常牺牲另一个 |
| **分割 vs 配准** | 分割 = 贴标签；配准 = 把两幅图对齐 |
| **合成 CT vs 真实 CT** | sCT 是 MRI 用 AI 生成的"假 CT"，只用于剂量计算，不能当诊断 CT |
| **放射组学 vs 剂量组学** | 前者挖影像，后者挖剂量分布 |
| **放射组学 vs 影像基因组学** | 后者把影像特征与基因组数据联合建模 |
            """
        )
