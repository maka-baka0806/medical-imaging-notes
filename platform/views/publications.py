"""文献收藏：杨振宇老师文献专藏。"""
from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from core.publications import (AWARDS, EARLY_PHYSICS, PUBLICATIONS, TOPICS,
                               stats)
from core.theme import DUKE_ACCENT, DUKE_BLUE

POS_LABEL = {"": " 第一作者", "": " 通讯/末位（导师位）",
"": " 合作者", "—": "— 项目/学位论文"}


def _records_to_df(records: list[dict]) -> pd.DataFrame:
    return pd.DataFrame([{
        "年份": r["year"],
        "位次": POS_LABEL.get(r["position"], r["position"]),
        "类型": r.get("kind", ""),
        "标题": r["title"],
        "期刊": r["journal"],
        "卷期页": r.get("cite", ""),
        "主题": "、".join(r.get("topic", [])),
        "核心发现": r.get("finding", ""),
        "平台复现": r.get("replicate", "—"),
        "DOI": r.get("doi", ""),
    } for r in records])


def render() -> None:
    st.title(" 文献收藏 · 杨振宇老师专藏")
    st.markdown(
        "已核实归属的**全部公开成果**（已排除同名研究者）。"
        "每条都标注了**作者位次**、**核心发现**与**平台对应复现模块**。"
    )

    st.markdown(
        '<div class="paper"><div class="meta"><span class="tag">配套项目</span></div>'
        '<h4>可执行复现：yang-lab-replications</h4>'
        '<p class="goal">本页是文献档案；每一篇的<b>逐步复现代码与实测报告</b>在独立项目中，'
        '每篇 5–7 个可独立执行的步骤，运行后自动生成报告。</p>'
        '<div class="diff">仓库：'
        '<a href="https://github.com/maka-baka0806/yang-lab-replications" target="_blank">'
        'github.com/maka-baka0806/yang-lab-replications</a>'
        '　·　本地：<code>~/医学影像学工作/yang-lab-replications</code></div></div>',
        unsafe_allow_html=True,
    )

    s = stats()
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("收录总数", s["总数"])
    c2.metric("期刊论文", s["期刊论文"])
    c3.metric("会议摘要", s["会议摘要"])
    c4.metric("第一作者", s["第一作者"])
    c5.metric("通讯/末位", s["通讯/末位"])
    c6.metric("合作者", s["合作者"])

    tab1, tab2, tab3, tab4 = st.tabs(
        [" 全部文献", " 统计与趋势", " 按技术线", " 早期物理研究"])

    # ---------------- 全部文献 ----------------
    with tab1:
        with st.sidebar:
            st.markdown("#### 筛选")
            years = sorted({p["year"] for p in PUBLICATIONS})
            pick_years = st.multiselect("年份", years, default=years)
            pick_pos = st.multiselect("位次", list(POS_LABEL),
                                      default=list(POS_LABEL),
                                      format_func=lambda k: POS_LABEL[k])
            kinds = sorted({p["kind"] for p in PUBLICATIONS})
            pick_kinds = st.multiselect("类型", kinds, default=kinds)
            pick_topics = st.multiselect("主题", TOPICS, default=[])
            only_repl = st.checkbox("只看平台已复现的", value=False)
            kw = st.text_input("关键词", placeholder="如：uncertainty、肺、剂量")

        rows = []
        for p in PUBLICATIONS:
            if p["year"] not in pick_years or p["position"] not in pick_pos:
                continue
            if p.get("kind") not in pick_kinds:
                continue
            if pick_topics and not set(pick_topics) & set(p["topic"]):
                continue
            if only_repl and not p["replicate"].startswith(""):
                continue
            if kw and kw.lower() not in (p["title"] + p["finding"] + p["journal"]).lower():
                continue
            rows.append(p)

        st.caption(f"当前筛选出 **{len(rows)}** 条")
        df = _records_to_df(rows)

        for p in rows:
            doi_link = (f'　·　<a href="https://doi.org/{p["doi"]}" target="_blank">打开 DOI</a>'
                        if p.get("doi") else "")
            with st.expander(f"{p['year']}　[{p.get('kind','')}]　"
                             f"{POS_LABEL.get(p['position'],'')}　{p['title'][:64]}"):
                st.markdown(
                    f"**{p['title']}**\n\n"
                    f"*{p['journal']}*　{p.get('cite','')}　·　第一作者：{p.get('first_author','—')}"
                    f"{doi_link}"
                )
                st.markdown(f"**类型**：{p.get('kind','—')}　｜　"
                            f"**主题**：{'、'.join(p['topic'])}")
                st.markdown(f"**核心发现**：{p['finding']}")
                st.info(f"**平台复现**：{p['replicate']}", icon="")

        if rows:
            buf = io.StringIO()
            df.to_csv(buf, index=False)
            st.download_button(" 导出当前筛选结果（CSV）",
                               buf.getvalue().encode("utf-8-sig"),
                               file_name="yang_zhenyu_publications.csv", mime="text/csv")

    # ---------------- 统计 ----------------
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**按年份（医学影像方向）**")
            st.bar_chart(pd.Series(s["按年份"]).sort_index())
        with c2:
            st.markdown("**按作者位次**")
            pos_counts = {"★ 第一作者": s["第一作者"], "☆ 通讯/末位": s["通讯/末位"],
                          "○ 合作者": s["合作者"]}
            st.bar_chart(pd.Series(pos_counts))

        st.markdown("**按文献类型**")
        st.bar_chart(pd.Series(s["按类型"]))

        st.markdown("**按主题分布**")
        st.bar_chart(pd.Series(s["按主题"]).sort_values(ascending=False))

        st.info(
            "**从位次变化能读出什么**：2024 年以前他基本是第一作者（自己动手做）；"
            "2024 年起越来越多**末位/通讯**（带学生做）—— 张日辉、王兰纳、张泽宇、戴晓仪等。"
            "这说明他现在需要能干活的学生。",
            
        )

    # ---------------- 按技术线 ----------------
    with tab3:
        LINES = {
            "① 放射组学方法学与稳健性": ["Digital phantoms", "discretization parameters",
                                          "视"],
            "② 肺通气成像（他最具代表性的方向）": ["pulmonary radiomic filtering",
                                                    "Pulmonary Ventilation"],
            "③ 不确定性量化（他当前的核心方向）": ["uncertainty", "Uncertainty",
                                                    "不确定性"],
            "④ 分割与深度学习架构": ["segmentation", "U-Net", "vision transformers",
                                      "Swin"],
            "⑤ 预后与生存分析": ["local failure", "overall survival", "Survival",
                                  "Outcome Prediction"],
            "⑥ 放疗剂量学与近距离治疗": ["DVH", "dose map", "brain dose", "Dosiomic",
                                          "synthetic CT"],
            "⑦ 形变配准": ["Registration", "registration"],
            "⑧ 可解释 AI 与影像基因组学": ["explainable", "Explainable", "Radiogenomic",
                                            "黑箱"],
        }
        for line, keys in LINES.items():
            hits = [p for p in PUBLICATIONS
                    if any(k.lower() in (p["title"] + p["finding"] + p["journal"]).lower()
                           for k in keys)]
            n_repl = sum(1 for p in hits if p["replicate"].startswith(""))
            with st.expander(f"{line}　（{len(hits)} 篇，其中 {n_repl} 篇平台可复现）",
                             expanded=len(hits) > 0 and line.startswith("②")):
                for p in sorted(hits, key=lambda x: -x["year"]):
                    mark = "" if p["replicate"].startswith("") else "　"
                    st.markdown(f"{mark} **{p['year']}** {p['title'][:80]}　"
                                f"<span style='color:#5A6472;font-size:0.85rem'>"
                                f"{p['journal']}</span>", unsafe_allow_html=True)

    # ---------------- 早期物理 ----------------
    with tab4:
        st.markdown(
            "本科期间与**东南大学侯吉旋**老师合作的统计物理与生物物理工作。"
            "这条线里有**生物物理（红细胞形状）**和「用极简模型解释复杂现象」的方法论，"
            "与他后来做的医学影像研究一脉相承。"
        )
        st.dataframe(pd.DataFrame([{
            "年份": p["year"], "标题": p["title"], "期刊": p["journal"],
            "卷期": p["cite"], "DOI": p["doi"],
        } for p in EARLY_PHYSICS]), hide_index=True, width="stretch")

        st.markdown("**特别值得一看的两篇**")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                "**Shape transformation of red blood cells induced by the osmotic pressure**"
                "（Eur J Phys 2020）\n\n用弹性膜能量模型解释红细胞在渗透压下的"
                "双凹圆盘 ↔ 球形转变 —— **这是他的第一篇生物物理工作。**"
            )
        with c2:
            st.markdown(
                "**Non-Markovian Mpemba effect in mean-field systems**"
                "（Phys Rev E 2020）\n\n"
                "「热水先结冰」在带记忆的平均场模型中出现 —— "
                "**反直觉现象 → 可控模型 → 定量解释**，这是他科研思维的底色。"
            )

    st.markdown("---")
    st.caption(
        "收录范围：同行评议期刊论文、预印本、会议摘要、学位论文与科研项目。"
        "已通过单位与课题组交叉核对排除同名研究者（如杜克 BME 的另一位 Zhenyu Yang）。"
        "OpenAlex 等数据库的 `author.orcid` 过滤会把 150+ 条记录混在一起，不可直接采信。"
    )
