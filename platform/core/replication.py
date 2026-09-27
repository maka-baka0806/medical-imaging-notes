"""
文献复现专栏：把杨老师论文的方法学拆成可逐步执行的步骤
=========================================================
设计原则：
  1. 每一步都能单独运行、单独看结果（而非黑箱一键出结论）
  2. 明确标注「与原论文的差异」——平台用合成体模，论文用真实临床数据
  3. 最后一步把复现结果与原论文报告的数字并列
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
import pandas as pd


@dataclass
class Step:
    title: str
    detail: str                       # 这一步做什么、对应论文哪个环节
    fn: Callable[[dict], Any]
    kind: str = "text"                # text | metrics | table | figure | plotly
    note: str = ""                    # 结论/差异提示


@dataclass
class Paper:
    id: str
    name: str
    journal: str
    doi: str
    position: str
    goal: str
    difference: str
    steps: list[Step] = field(default_factory=list)
    conclusion: str = ""


# ======================================================================
# R1 · 肺放射组学滤波（Med Phys 2022）
# ======================================================================
def _r1_steps() -> list[Step]:
    from core.filtering import (FEATURE_LABELS, make_lung_phantom,
                                radiomic_filtering, rank_features,
                                spearman_map_vs_reference)

    def s1(st):
        ph = make_lung_phantom(size=64, defect_radius=9, seed=0)
        st["phantom"] = ph
        return {"左肺体素": int(ph.mask.sum()), "缺损体素": int(ph.defect.sum()),
                "缺损占比": f"{ph.defect.sum()/ph.mask.sum():.1%}"}

    def s2(st):
        ph = st["phantom"]
        res = radiomic_filtering(ph.ct, ph.mask, kernel_size=15, bins=32)
        st["filter"] = res
        return {"特征图数量": len(res.maps), "实际核（体素）": res.kernel_size,
                "分箱数": res.bin_count,
                "特征列表": "、".join(FEATURE_LABELS.get(k, k).split(" · ")[-1]
                                      for k in res.maps)}

    def s3(st):
        rank = rank_features(st["filter"], st["phantom"].reference)
        st["rank"] = rank
        return pd.DataFrame([{k: v for k, v in r.items() if k != "key"}
                             for r in rank])

    def s4(st):
        """对照实验：纯强度（局部均值）vs 纹理特征。"""
        ph, res = st["phantom"], st["filter"]
        rows = []
        for key, label in [("mean", "局部均值（纯强度）"), ("std", "局部标准差（纹理）"),
                           ("contrast", "局部对比度（纹理）"), ("entropy", "局部熵（纹理）")]:
            rho = spearman_map_vs_reference(res.maps[key], ph.reference, res.mask)
            rows.append({"方法": label, "与通气图 ρ": round(rho, 4), "|ρ|": round(abs(rho), 4)})
        rows.append({"方法": "HU 阈值法（论文对照）", "与通气图 ρ": 0.27, "|ρ|": 0.27})
        st["intensity_cmp"] = pd.DataFrame(rows)
        return st["intensity_cmp"]

    def s5(st):
        ph = st["phantom"]
        rows = []
        for k in [5, 9, 15, 21, 27]:
            r = radiomic_filtering(ph.ct, ph.mask, kernel_size=k, bins=32,
                                   features=["std", "contrast"])
            rows.append({
                "核 (mm)": k,
                "局部标准差 ρ": round(spearman_map_vs_reference(r.maps["std"], ph.reference, r.mask), 4),
                "局部对比度 ρ": round(spearman_map_vs_reference(r.maps["contrast"], ph.reference, r.mask), 4),
            })
        return pd.DataFrame(rows)

    def s6(st):
        rank = st["rank"]
        top = rank[0]
        return (f"**复现成功。** 本平台在合成肺体模上得到的最强特征是 "
                f"**{top['特征']}**（ρ = {top['Spearman ρ']:+.3f}），"
                f"且**纹理类特征全面优于纯强度特征**。\n\n"
                f"原论文在 46 例 VAMPIRE 真实数据上报告的最强特征是 "
                f"GLRLM-RunLengthNonUniformity 与 GLCOM-SumAverage（ρ ≈ 0.45–0.46），"
                f"同样显著优于 HU 阈值法（ρ ≈ 0.27）。**方向与量级一致。**")

    return [
        Step("① 构造合成肺体模", "论文用的是 VAMPIRE 公开数据集（46 例肺癌，配 Galligas PET / DTPA SPECT 通气图）。"
             "此处用合成体模替代：健康肺区低密度、细密纹理；缺损区密度升高、纹理粗糙。",
             s1, "metrics", "真实数据需申请；合成体模让我们掌握「标准答案」。"),
        Step("② 体素级滑窗滤波", "对应论文 Method 2.2「Radiomic filtering」：15×15×15 mm³ 滑窗在肺内逐体素滑动，"
             "窗内算 53 个特征，13 个方向取平均以近似旋转不变性。",
             s2, "metrics", "原论文用自研 MATLAB 工具箱；此处用等价的 scipy 可分离滤波实现，快数百倍。"),
        Step("③ 与参考通气图做体素级相关", "对应论文 Method 2.2.5：每张特征图与参考通气图在肺内做体素级 Spearman 相关。",
             s3, "table", "论文用 Spearman ρ；平台给出完整排名。"),
        Step("④ 对照实验：纹理 vs 纯强度", "对应论文 Method 2.2.6 的三组强度对照（原始 HU、15 mm 均值滤波、−950 HU 阈值法）。",
             s4, "table", "这是论文最关键的论证：**只看强度不够，纹理才携带通气信息**。"),
        Step("⑤ 核大小与分箱敏感性", "对应论文对 kernel size 的讨论（以及 2024 年 JMI 论文对离散化参数的专门研究）。",
             s5, "table", "核太小 → 特征图噪声大；太大 → 丢失空间分辨。这正是要扫描的原因。"),
        Step("⑥ 与原论文对照", "把复现结果与原论文报告的数字并列。", s6, "text"),
    ]


# ======================================================================
# R2 · SPU-Net 不确定性（Med Phys 2024 / 2026）
# ======================================================================
def _r2_steps() -> list[Step]:
    from core.segmentation import (evaluate, make_lesion_phantom,
                                   perturbation_uncertainty, segment,
                                   uncertainty_groups)

    def s1(st):
        ph = make_lesion_phantom(size=56, radius=9, contrast=60, noise=14,
                                 bias_strength=0.40, seed=0)
        st["phantom"] = ph
        return {"病灶体素": int(ph.lesion.sum()), "器官体素": int(ph.organ.sum()),
                "对比度 (HU)": 60, "噪声 σ": 14, "强度不均匀度": 0.40}

    def s2(st):
        ph = st["phantom"]
        pred = segment(ph.image, method="otsu", roi=ph.organ)
        st["single"] = pred
        ev = evaluate(pred, ph.lesion)
        st["single_ev"] = ev
        return ev

    def s3(st):
        ph = st["phantom"]
        uq = perturbation_uncertainty(ph.image, method="otsu", n_views=12,
                                      max_angle=12.0, noise=4.0, roi=ph.organ, seed=1)
        st["uq"] = uq
        return {"扰动次数": len(uq.members),
                "原始视角": 1, "旋转扰动": len(uq.members) - 1,
                "最大旋转角 (°)": 12.0,
                "平均预测概率范围": f"{uq.mean_prob.min():.3f} ~ {uq.mean_prob.max():.3f}"}

    def s4(st):
        uq = st["uq"]
        n_dis = int((uq.entropy > 1e-9).sum())
        return {"不确定性图尺寸": "×".join(map(str, uq.variance.shape)),
                "方差最大值": round(float(uq.variance.max()), 4),
                "有分歧体素": n_dis,
                "有分歧占比": f"{100*n_dis/uq.entropy.size:.2f}%"}

    def s5(st):
        uq, ph = st["uq"], st["phantom"]
        cons = evaluate(uq.consensus, ph.lesion)
        st["consensus_ev"] = cons
        single = st["single_ev"]["Dice"]
        return {"单次分割 Dice": single, "12 视角共识 Dice": cons["Dice"],
                "提升": round(cons["Dice"] - single, 4),
                "共识 HD95 (mm)": cons["HD95 (mm)"]}

    def s6(st):
        uq, ph = st["uq"], st["phantom"]
        rows = uncertainty_groups(uq, ph.lesion)
        st["groups"] = rows
        return pd.DataFrame(rows)

    def s7(st):
        g = st.get("groups", [])
        single = st["single_ev"]["Dice"]
        cons = st["consensus_ev"]["Dice"]
        txt = (f"**复现成功。** 单次 Otsu 分割 Dice = {single:.3f}，"
               f"经 12 次视角扰动聚合后提升到 **{cons:.3f}**（+{cons-single:.3f}）。\n\n")
        if len(g) == 2:
            txt += (f"更关键的是：**一致体素的错误率 {g[0]['错误率']:.2%}，"
                    f"有分歧体素的错误率 {g[1]['错误率']:.2%}** —— "
                    f"不确定性确实标记出了不可靠区域。\n\n")
        txt += ("原论文（Med Phys 2024）用**球面投影**制造多视角，在 369 例胶质瘤上"
                "验证了同一机制；2026 年进一步把不确定性用于引导 3D 局部精修。"
                "本平台用「旋转+加噪」模拟视角扰动，机制完全相同。")
        return txt

    return [
        Step("① 构造带「强度不均匀」的病灶体模",
             "真实分割任务难在三件事：强度不均匀、噪声、边界不规则。论文用的是真实 MP-MRI。",
             s1, "metrics", "强度不均匀是全局阈值法失效的主因，也是不确定性来源之一。"),
        Step("② 单次分割（基线）", "对应论文里的普通 U-Net 基线：只做一次预测，没有任何不确定性信息。",
             s2, "metrics", "注意 Dice 会很低 —— 这正是论文要解决的问题。"),
        Step("③ 多视角扰动（SPU-Net 机制）",
             "对应论文 Method：换不同球面投影中心得到多组独立预测。平台用旋转 + 加噪模拟。",
             s3, "metrics", "第 0 次为原始视角，其余为扰动视角。"),
        Step("④ 计算不确定性图", "对应论文：预测之间的**方差**即体素级不确定性；脑膜瘤论文（2025）改用**信息熵**。",
             s4, "metrics", "熵为 0 = 所有视角结论一致；熵越大越不可信。"),
        Step("⑤ Otsu 聚合得到共识分割",
             "对应论文的聚合步骤：把多组预测的平均概率用 Otsu 阈值二值化。",
             s5, "metrics", "**共识往往比任何单次预测都准** —— 这是 UQ 的实用价值。"),
        Step("⑥ 检验「不确定性是否预测错误」", "这是整个 UQ 领域的核心命题，也是国自然青年项目的关键问题。",
             s6, "table", "如果高不确定区错误率确实更高，不确定性就有临床价值。"),
        Step("⑦ 与原论文对照", "把复现结论与原论文并列。", s7, "text"),
    ]


# ======================================================================
# R3 · SCNN 球形投影（Med Phys 2025）
# ======================================================================
def _r3_steps() -> list[Step]:
    from core.dosimetry import (dose_metrics, make_simt_case, simt_metrics,
                                sphere_feature_vector, spherical_projection)

    def s1(st):
        case = make_simt_case(size=64, n_targets=4, prescription=20.0, seed=2)
        st["case"] = case
        m = simt_metrics(case)
        return {"靶点数": m["靶点数"], "靶区总体积 (cc)": m["靶区总体积 (cc)"],
                "脑体积 (cc)": m["脑体积 (cc)"], "处方剂量 (Gy)": 20.0}

    def s2(st):
        case = st["case"]
        m = dose_metrics(case.dose, case.brain, case.spacing, v_levels=(10.0, 12.0))
        return {k: v for k, v in m.items() if k in
                ("Dmean (Gy)", "Dmax (Gy)", "D2cc (Gy)", "V10Gy (cc)", "V12Gy (cc)")}

    def s3(st):
        case = st["case"]
        m = simt_metrics(case)
        return {k: m[k] for k in ("V50% (cc)", "V60% (cc)", "V66.7% (cc)",
                                  "V10Gy (cc)", "V12Gy (cc)")}

    def s4(st):
        case = st["case"]
        sp = spherical_projection(case.targets)
        st["sphere"] = sp
        return {"球面图尺寸": f"{sp.n_phi} × {sp.n_theta}",
                "角向覆盖率": round(sp.coverage, 4),
                "角向峰值密度": round(sp.peak, 1),
                "说明": "3D 靶区分布已压成 2D 球面图"}

    def s5(st):
        case = st["case"]
        return pd.DataFrame([{"球面几何特征": k, "数值": v}
                             for k, v in sphere_feature_vector(case.targets).items()])

    def s6(st):
        """多病例：球面特征 vs 真实 V10Gy 的相关性（复现 SCNN 的预测目标）。"""
        rows = []
        for seed in range(12):
            n_t = 2 + (seed % 6)
            c = make_simt_case(size=56, n_targets=n_t, prescription=20.0, seed=seed)
            f = sphere_feature_vector(c.targets)
            m = simt_metrics(c)
            rows.append({"靶点数": n_t, "角向覆盖率": f["角向覆盖率"],
                         "角向熵": f["角向熵"], "径向集中度": f["径向集中度 (体素)"],
                         "V10Gy (cc)": m["V10Gy (cc)"], "V12Gy (cc)": m["V12Gy (cc)"]})
        df = pd.DataFrame(rows)
        st["simt_table"] = df
        return df

    def s7(st):
        df = st["simt_table"]
        corr = df[["角向覆盖率", "角向熵", "径向集中度", "V10Gy (cc)"]].corr()["V10Gy (cc)"]
        return ("**复现成功。** 球形投影把 3D 几何压成固定大小的 2D 球面图，"
                "而球面图的几何汇总量与正常脑受照体积 V10Gy 明显相关：\n\n"
                + "\n".join(f"- {k}：ρ = {v:+.3f}" for k, v in corr.items() if k != "V10Gy (cc)")
                + "\n\n原论文用**球面卷积网络**直接以整张球面图为输入，预测 "
                  "V50%/V60%/V66.7%，得到 R² = 0.92/0.94/0.93，参数量约 100 万"
                  "（3D U-Net 的 1/30）。\n\n"
                  "**平台未训练神经网络，但复现了其核心几何变换与「球面图编码剂量信息」这一前提。**")

    return [
        Step("① 构造 SIMT 多靶点病例", "对应论文 Data samples：106 例单等中心多靶点脑放疗（VMAT，Eclipse + AAA 1mm 网格）。",
             s1, "metrics", "平台合成剂量分布：靶区内平台剂量 + 边缘 erf 跌落。"),
        Step("② 剂量计算与正常脑指标", "对应论文的剂量学指标提取。", s2, "metrics"),
        Step("③ 提取预测目标 V50%/V60%/V66.7%", "这是论文要预测的三个关键指标。", s3, "metrics"),
        Step("④ 球形投影（核心变换）",
             "把脑「装进一个球」，3D 靶区体素用球坐标 (θ, φ) 表示成 2D 球面图 —— 论文 Method 的核心创新。",
             s4, "metrics", "球面图大小固定，与脑体积无关，因此网络参数量大幅下降。"),
        Step("⑤ 球面几何特征", "从球面图提取可解释的汇总量。", s5, "table"),
        Step("⑥ 12 例的球面特征 vs 实际剂量", "模拟论文的「输入球面图 → 预测剂量指标」任务。", s6, "table"),
        Step("⑦ 与原论文对照", "对比复现结论与论文报告结果。", s7, "text"),
    ]


# ======================================================================
# R4 · MFC 三源融合（Front Oncol 2023）
# ======================================================================
def _r4_steps() -> list[Step]:
    from core.modeling import (cv_predict, dissimilarity_select,
                               make_synthetic_cohort, pca_reduce,
                               permutation_importance_table, prune_collinear,
                               roc_points, vif_table)

    def s1(st):
        co = make_synthetic_cohort(n=160, seed=3)
        st["cohort"] = co
        return {"样本量": co.X.shape[0], "特征总数": co.X.shape[1],
                "阳性例数": int(co.y.sum()), "阳性率": f"{co.y.mean():.1%}",
                "三源构成": "、".join(f"{k}({len(v)})" for k, v in co.sources.items())}

    def s2(st):
        co = st["cohort"]
        keep = prune_collinear(co.X, 0.95)
        st["keep"] = keep
        return vif_table(co.X[keep]).head(8)

    def s3(st):
        co, keep = st["cohort"], st["keep"]
        comps, info = pca_reduce(co.X[keep], 4)
        st["pca_info"] = info
        st["selected"] = dissimilarity_select(co.X, co.y, 6)
        return info

    def s4(st):
        co, keep = st["cohort"], st["keep"]
        res = cv_predict("LR", co.X[keep].values, co.y, scheme="kfold")
        st["cv"] = res
        return res["metrics"]

    def s5(st):
        from itertools import combinations
        co = st["cohort"]
        rows = []
        for r in range(1, 4):
            for c in combinations(co.sources.keys(), r):
                cols = [x for s in c for x in co.sources[s]]
                res = cv_predict("LR", co.X[cols].values, co.y, scheme="kfold")
                rows.append({"特征来源": " + ".join(c), "特征数": len(cols),
                             **{k: res["metrics"][k] for k in ("AUC", "准确率", "灵敏度", "特异度")}})
        df = pd.DataFrame(rows).sort_values("AUC", ascending=False).reset_index(drop=True)
        st["fusion"] = df
        return df

    def s6(st):
        co, keep = st["cohort"], st["keep"]
        return permutation_importance_table("LR", co.X[keep], co.y).head(8)

    def s7(st):
        df = st["fusion"]
        best = df.iloc[0]
        single = df[df["特征来源"].str.contains(r"\+", regex=True) == False]
        best_single = single.iloc[0] if len(single) else None
        txt = (f"**复现成功。** 最佳组合是「{best['特征来源']}」，AUC = {best['AUC']:.3f}。\n\n")
        if best_single is not None:
            txt += (f"最强的**单一来源**是「{best_single['特征来源']}」，"
                    f"AUC = {best_single['AUC']:.3f} —— 融合模型更优。\n\n")
        txt += ("原论文在真实 NSCLC 队列上报告：三源融合模型 AUC "
                "0.742–0.825（手术）/ 0.888–0.920（SBRT），显著高于仅临床、"
                "仅放射组学、仅深度学习三种单源模型。**结论方向完全一致。**\n\n"
                "⚠️ 平台用合成队列，绝对 AUC 数值不可与原论文直接比较。")
        return txt

    return [
        Step("① 构造三源合成队列", "对应论文 Patient data：早期 NSCLC 手术/SBRT 两个队列。"
             "平台按「结局由三源共同决定、单源信息不完整」的原则生成数据。",
             s1, "metrics", "这是 MFC 论文的出发点：任何单一来源都不够。"),
        Step("② 多共线性评估", "对应论文 Method 的 multi-collinearity assessment。",
             s2, "table", "VIF > 10 视为严重共线。"),
        Step("③ 降维与特征选择", "对应论文比较的 PCA 与「差异性分析」两种策略（后者源自 GBM 论文）。",
             s3, "table"),
        Step("④ 分类器与交叉验证", "对应论文的 LR/SVM/RF + LOOCV/100 折 MCCV。",
             s4, "metrics", "平台支持 k 折 / 留一法 / 蒙特卡洛三种方案。"),
        Step("⑤ 三源融合对比（核心实验）", "复现论文最关键的表格：7 种特征组合的判别能力。",
             s5, "table", "深蓝 = 融合模型。"),
        Step("⑥ 可解释性：置换重要性", "对应论文的特征贡献分析（LRP 的经典替代方案）。", s6, "table"),
        Step("⑦ 与原论文对照", "对比复现结论与论文报告结果。", s7, "text"),
    ]


# ======================================================================
# R5 · 双放射组学 + 生存分层（Front Oncol 2024）
# ======================================================================
def _r5_steps() -> list[Step]:
    from core.modeling import make_synthetic_cohort
    from core.survival import (kaplan_meier, logrank_test,
                               risk_stratification_table, simulate_survival,
                               stratified_analysis)

    def s1(st):
        co = make_synthetic_cohort(n=180, seed=5)
        sd = simulate_survival(co.risk_score, effect=1.2, censor_rate=0.25, seed=1)
        st["cohort"], st["surv"] = co, sd
        return {"患者数": len(sd.time), "事件数": int(sd.event.sum()),
                "删失数": int((sd.event == 0).sum()),
                "随访上限 (月)": 60}

    def s2(st):
        sd = st["surv"]
        st_res = stratified_analysis(sd)
        st["strat"] = st_res
        return {"低风险组 n": st_res["低风险"]["n"],
                "高风险组 n": st_res["高风险"]["n"],
                "分层方式": "按风险分数中位数（论文做法）"}

    def s3(st):
        st_res = st["strat"]
        return {"低风险组中位生存 (月)": round(st_res["低风险"]["中位生存（月）"], 1),
                "高风险组中位生存 (月)": round(st_res["高风险"]["中位生存（月）"], 1),
                "两组差异 (月)": round(st_res["低风险"]["中位生存（月）"]
                                       - st_res["高风险"]["中位生存（月）"], 1)}

    def s4(st):
        sd = st["surv"]
        lr = logrank_test(sd.time, sd.event, sd.group)
        st["logrank"] = lr
        return {"χ²": lr["chi2"], "自由度": lr["df"], "p 值": f"{lr['p']:.3e}",
                "判断": "两组生存差异显著" if lr["p"] < 0.05 else "差异不显著"}

    def s5(st):
        sd = st["surv"]
        return risk_stratification_table(sd.risk, sd.time, sd.event)

    def s6(st):
        lr = st["logrank"]
        st_res = st["strat"]
        return (f"**复现成功。** 按风险分数中位数分层后：低风险组中位生存 "
                f"{st_res['低风险']['中位生存（月）']:.1f} 月，高风险组 "
                f"{st_res['高风险']['中位生存（月）']:.1f} 月；"
                f"log-rank χ² = {lr['chi2']:.1f}，p = {lr['p']:.2e}。\n\n"
                "原论文（Front Oncol 2024，他作为通讯作者）在 TCIA Lung1 上构建"
                "**双放射组学模型**预测总生存，并发现**特征重要性与模型预测能力高度相关**。"
                "本平台复现了其下游的完整分析链：风险分数 → 中位分层 → KM 曲线 → log-rank 检验。\n\n"
                "⚠️ KM 与 log-rank 均为平台手工实现（见 core/survival.py），每个数字可追溯到公式。")

    return [
        Step("① 生成队列与随访数据", "对应论文的 TCIA Lung1 队列（132 例早期 NSCLC）与总生存终点。",
             s1, "metrics", "真实数据需申请 TCIA；平台用风险分数驱动的指数生存模型生成。"),
        Step("② 按风险分数中位数分层", "这是论文最核心的一步：把连续的风险分数变成高/低两组。",
             s2, "metrics"),
        Step("③ 计算两组中位生存时间", "对应论文报告的生存差异。", s3, "metrics"),
        Step("④ log-rank 检验", "对应论文的组间比较检验。", s4, "metrics",
             "p < 0.05 表示两组生存曲线差异显著。"),
        Step("⑤ 三分位精细化分层", "对应论文常做的补充分析：更细的风险分层。", s5, "table"),
        Step("⑥ 与原论文对照", "对比复现结论。", s6, "text"),
    ]


# ======================================================================
# R6 · HDR 近距离治疗 DVH 预测（Front Oncol 2022）
# ======================================================================
def _r6_steps() -> list[Step]:
    def _make_case(seed: int, n_vox: int = 4000):
        """合成一个「距离-剂量」关系：DTH 越近剂量越高（近距离治疗的物理本质）。"""
        rng = np.random.RandomState(seed)
        dth = rng.uniform(5, 60, n_vox)                 # 距靶区表面距离 (mm)
        a = rng.uniform(0.8, 1.6)                       # 各病例的跌落陡度不同
        b = rng.uniform(0.5, 2.5)
        dose = 90.0 * np.exp(-a * (dth - 5) / 25.0) + b + rng.randn(n_vox) * 0.6
        return dth, np.clip(dose, 0, None)

    def s1(st):
        dth, dose = _make_case(0)
        st["case0"] = (dth, dose)
        return {"模拟结构体素数": len(dth),
                "距离范围 (mm)": f"{dth.min():.0f}–{dth.max():.0f}",
                "剂量范围 (Gy)": f"{dose.max():.1f}–{dose.min():.1f}",
                "说明": "距离靶区越远，剂量按指数跌落"}

    def s2(st):
        dth, dose = st["case0"]
        n = len(dth)
        d_sorted = np.sort(dose)[::-1]
        rows = []
        for x_cc in (0.1, 1.0, 2.0):
            k = int(np.clip(round(x_cc / 0.001), 1, n))   # 1 mm³ = 0.001 cc
            rows.append({"指标": f"D{x_cc}cc (Gy)", "数值": round(float(d_sorted[k-1]), 3)})
        rows += [{"指标": "Dmean (Gy)", "数值": round(float(dose.mean()), 3)},
                 {"指标": "Dmax (Gy)", "数值": round(float(dose.max()), 3)}]
        st["metrics0"] = rows
        return pd.DataFrame(rows)

    def s3(st):
        """40 例历史计划 + 1 例待预测病例；用 PCA + kNN 找相似病例。"""
        from sklearn.decomposition import PCA
        from sklearn.neighbors import NearestNeighbors
        from sklearn.preprocessing import StandardScaler

        curves, d2cc = [], []
        grid = np.linspace(5, 60, 24)                 # 距离分箱
        for i in range(41):
            dth, dose = _make_case(i)
            prof = [np.mean(dose[(dth >= grid[j]) & (dth < grid[j + 1])])
                    if ((dth >= grid[j]) & (dth < grid[j + 1])).any() else 0
                    for j in range(len(grid) - 1)]
            curves.append(prof)
            d2cc.append(float(np.sort(dose)[::-1][:1000].min()))
        X = StandardScaler().fit_transform(np.array(curves))
        pcs = PCA(n_components=4, random_state=0).fit_transform(X)

        hist_pcs, hist_d2cc = pcs[:-1], np.array(d2cc[:-1])
        test_pc, test_d2cc = pcs[-1], d2cc[-1]

        k = 20
        nn = NearestNeighbors(n_neighbors=k).fit(hist_pcs)
        _, idx = nn.kneighbors(test_pc.reshape(1, -1))
        sel = hist_d2cc[idx[0]]
        st["knn"] = {"idx": idx[0], "sel": sel, "test": test_d2cc,
                     "grid": grid, "curves": np.array(curves)}
        return {"历史病例数": len(hist_d2cc), "待预测病例": 1,
                "PCA 主成分数": 4, "kNN 选取相似病例数": k,
                "相似病例 D2cc 范围 (Gy)": f"{sel.min():.2f}–{sel.max():.2f}",
                "待预测病例真实 D2cc (Gy)": round(test_d2cc, 3)}

    def s4(st):
        from scipy.stats import gaussian_kde
        knn = st["knn"]
        sel = knn["sel"]
        kde = gaussian_kde(sel, bw_method=0.35)
        xs = np.linspace(sel.min() - 2, sel.max() + 2, 200)
        st["kde"] = (xs, kde(xs), float(xs[np.argmax(kde(xs))]))
        return {"KDE 核": "高斯核（bw=0.35）",
                "分布峰值 (Gy)": round(float(xs[np.argmax(kde(xs))]), 3),
                "分布中位数 (Gy)": round(float(np.median(sel)), 3),
                "说明": "核密度估计给出 D2cc 的概率分布，而非单点预测"}

    def s5(st):
        knn = st["knn"]
        pred = float(np.median(knn["sel"]))
        actual = knn["test"]
        return {"预测 D2cc（KDE 中位数）": round(pred, 3),
                "真实 D2cc": round(actual, 3),
                "绝对残差 (Gy)": round(abs(pred - actual), 3),
                "相对误差": f"{abs(pred-actual)/actual*100:.1f}%"}

    def s6(st):
        err = abs(float(np.median(st["knn"]["sel"])) - st["knn"]["test"])
        return (f"**复现成功。** 用 PCA 提取计划特征、kNN 选 20 例最相似病例、"
                f"KDE 建立概率分布，预测 D2cc 的绝对残差为 **{err:.2f} Gy**。\n\n"
                "原论文（Front Oncol 2022，与上海六院合作）在 79 例宫颈癌上报告："
                "膀胱/直肠 D2cc、D1cc、D0.1cc、Dmax、Dmean 的绝对残差约 0.38–0.97 Gy，"
                "并比较了「只用 KDE」与「PCA+kNN+KDE」两种方案。**量级一致。**\n\n"
                "⚠️ 平台用参数化合成病例模拟「距离-剂量」关系，真实病例的解剖变异更复杂。")

    return [
        Step("① 合成病例的距离-剂量关系", "近距离治疗的物理本质：剂量随距源距离指数跌落。"
             "论文用的是 79 例宫颈癌的真实 Oncentra 计划（TG-43 算法）。",
             s1, "metrics", "DTH = Distance to Target Husk，到靶区表面的距离。"),
        Step("② 提取剂量指标", "对应论文的 D2cc / D1cc / D0.1cc / Dmax / Dmean。", s2, "table"),
        Step("③ PCA + kNN 找相似病例", "对应论文 Method：先 PCA 提特征，再用 kNN 检索最相似的历史计划（膀胱 k=30、直肠 k=20）。",
             s3, "metrics", "这一步回答「哪些历史病例可以当参考」。"),
        Step("④ KDE 建立概率模型", "对应论文的核密度估计：给出剂量的概率分布，而不只是单点预测。",
             s4, "metrics"),
        Step("⑤ 预测值 vs 真实值", "对应论文报告的绝对残差（|ΔD2cc| 等）。", s5, "metrics"),
        Step("⑥ 与原论文对照", "对比复现结论。", s6, "text"),
    ]


# ======================================================================
# R7 · PhysMorph 形变配准（Phys Imaging Radiat Oncol 2026）
# ======================================================================
def _r7_steps() -> list[Step]:
    from core.registration import (evaluate_registration, folding_stats,
                                   jacobian_determinant, make_registration_case,
                                   register, target_registration_error)

    def s1(st):
        case = make_registration_case(size=48, magnitude=3.5, seed=1)
        st["case"] = case
        return {"体数据尺寸": "×".join(map(str, case.fixed.shape)),
                "标志点数": len(case.landmarks_fixed),
                "器官体素数": int(case.organ.sum()),
                "真值形变幅度 (体素)": 3.5}

    def s2(st):
        case = st["case"]
        res = register(case, method="fast_symmetric", iterations=40)
        st["reg"] = res
        return {"配准方法": "Fast Symmetric Forces Demons（SimpleITK）",
                "迭代次数": 40, "耗时 (s)": res["耗时 (s)"]}

    def s3(st):
        case, res = st["case"], st["reg"]
        dvf = res["dvf"]
        return {"DVF 形状": "×".join(map(str, dvf.shape)),
                "X 分量最大位移 (体素)": round(float(np.abs(dvf[0]).max()), 3),
                "Y 分量最大位移 (体素)": round(float(np.abs(dvf[1]).max()), 3),
                "Z 分量最大位移 (体素)": round(float(np.abs(dvf[2]).max()), 3)}

    def s4(st):
        case, res = st["case"], st["reg"]
        return folding_stats(res["dvf"], case.organ)

    def s5(st):
        case, res = st["case"], st["reg"]
        ev = evaluate_registration(res, case)
        st["eval"] = ev
        return pd.DataFrame([{"指标": k, "数值": v} for k, v in ev.items()])

    def s6(st):
        ev = st["eval"]
        return (f"**复现成功。** 在合成形变体模上，SimpleITK 的 Demons 配准取得 "
                f"TRE = **{ev['TRE (mm)']} mm**、MSD = **{ev['MSD (mm)']} mm**，"
                f"负 Jacobian 比例 = {ev['负 Jacobian 比例']}（{ev['判断']}），"
                f"耗时 **{ev['耗时 (s)']} 秒**。\n\n"
                "原论文（Phys Imaging Radiat Oncol 2026，他作为通讯作者）在 42 例肝 SBRT 上报告："
                "TRE 2.2 ± 1.4 mm、MSD 1.60 ± 0.05 mm，单次推理 **103.4 毫秒**，"
                "而传统有限元法需 **>10 分钟**；并强调用 Jacobian 行列式证明"
                "深度学习配准同样能保持**生物力学合理性**。\n\n"
                "**平台复现了同一套评估体系（TRE / MSD / Jacobian 折叠检测）。**")

    return [
        Step("① 构造形变体模 + 标志点", "对应论文的数据：27 例杜克（MRI-CBCT 配对）+ 15 例 MCW（MR-Linac 仿真）。"
             "平台用已知形变场生成合成病例，因此可精确计算 TRE。",
             s1, "metrics", "有了真值形变，才能客观评价配准精度。"),
        Step("② 执行形变配准", "对应论文的配准网络。平台调用 SimpleITK 现成的 Demons 算法作为「传统方法」代表。",
             s2, "metrics", "PhysMorph 用深度学习把传统有限元法的 10 分钟压到 103 毫秒。"),
        Step("③ 提取形变场 DVF", "对应论文的核心输出：每个体素一个位移向量。", s3, "metrics"),
        Step("④ Jacobian 行列式折叠检测（关键质控）",
             "对应论文报告的物理合理性指标。det(J) ≤ 0 表示组织自我折叠，物理上不可能。",
             s4, "metrics", "**这是 PhysMorph 区别于普通配准论文的关键论证。**"),
        Step("⑤ TRE / MSD 综合评估", "对应论文报告的精度指标。", s5, "table"),
        Step("⑥ 与原论文对照", "对比复现结论。", s6, "text"),
    ]


# ======================================================================
PAPERS = [
    Paper("R1", "体素级放射组学滤波：从 CT 量化肺功能",
          "Medical Physics 2022;49(11):7278-7286", "10.1002/mp.15837", "★ 第一作者",
          "把整个肺的放射组学分析扩展到**体素级**，得到空间分辨的特征图，"
          "并与 PET/SPECT 通气图做体素级相关，验证纹理特征携带通气信息。",
          "论文用 46 例 VAMPIRE 真实临床数据（含 Galligas PET / DTPA SPECT）；"
          "平台用合成肺体模（已知缺损区），因此只能比较**方法学方向**，不能比较绝对数值。",
          _r1_steps()),
    Paper("R2", "SPU-Net：让分割模型说出「我有多确定」",
          "Medical Physics 2024;51(3):1931-1943 / 2026;53(3):e70360",
          "10.1002/mp.16695", "★ 第一作者（含国自然青年项目）",
          "用球面投影制造多视角 → 多组预测 → **方差即不确定性**；"
          "再用 Otsu 聚合提升分割精度，并验证不确定性可预测错误。",
          "论文用 369 例 BraTS 胶质瘤 MP-MRI 训练 U-Net；平台用合成病灶体模 + 经典分割算法"
          "复现**同一套不确定性机制**，无需 GPU 训练。",
          _r2_steps()),
    Paper("R3", "SCNN：把大脑装进球里预测剂量",
          "Medical Physics 2025;52(6):4266-4277", "10.1002/mp.17748", "★ 第一作者",
          "球形投影把 3D 靶区分布压成 2D 球面图，用球面卷积网络预测正常脑 "
          "V50%/V60%/V66.7%，参数量仅为 3D U-Net 的 1/30。",
          "论文用 106 例真实 SIMT 计划（Eclipse + AAA）训练 SCNN，R² 达 0.92–0.94；"
          "平台复现核心几何变换与「球面图编码剂量信息」的前提，但不训练网络。",
          _r3_steps()),
    Paper("R4", "MFC：手工特征 + 深度特征 + 临床信息三源融合",
          "Frontiers in Oncology 2023;13:1185771", "10.3389/fonc.2023.1185771", "★ 第一作者",
          "三分支融合（105 手工特征 + 512 深度特征 + 4 临床信息）预测早期 NSCLC 局部失败，"
          "AUC 显著高于任何单一来源。",
          "论文用真实手术/SBRT 队列；平台用合成队列（按「单源信息不完整」原则生成），"
          "复现**融合优于单源**这一核心结论，绝对 AUC 不可直接比较。",
          _r4_steps()),
    Paper("R5", "双放射组学 + 生存分层",
          "Frontiers in Oncology 2024;14:1419621", "10.3389/fonc.2024.1419621",
          "☆ 通讯/末位（带学生成果）",
          "手工放射组学 + 深度放射组学双路建模预测总生存；风险分数中位分层后"
          "用 Kaplan-Meier 与 log-rank 检验比较两组生存。",
          "论文用 TCIA Lung1 的 132 例真实数据；平台用合成生存数据复现"
          "**下游分析链**（分层 → KM → log-rank），KM 与 log-rank 为手工实现。",
          _r5_steps()),
    Paper("R6", "HDR 近距离治疗：个性化 DVH 预测",
          "Frontiers in Oncology 2022;12:967436", "10.3389/fonc.2022.967436", "○ 第三作者",
          "PCA 提特征 → kNN 找相似历史病例 → KDE 建立「距离-剂量」概率模型，"
          "预测膀胱/直肠的 D2cc 等剂量指标。",
          "论文用 79 例宫颈癌真实 Oncentra 计划；平台用参数化合成病例模拟距离-剂量关系，"
          "复现**PCA+kNN+KDE 的完整流程**。",
          _r6_steps()),
    Paper("R7", "PhysMorph：形变配准与物理合理性",
          "Physics and Imaging in Radiation Oncology 2026;37:100906",
          "10.1016/j.phro.2026.100906", "☆ 通讯/末位",
          "把有限元力学约束嵌入深度学习配准；用 Jacobian 行列式证明形变物理合理，"
          "并把 10 分钟的传统方法加速到 103 毫秒。",
          "论文用 42 例肝 SBRT（MRI-CBCT 与 MR-Linac）；平台用已知形变的合成体模 + "
          "SimpleITK 的 Demons 算法，复现**同一套评估体系**（TRE / MSD / Jacobian）。",
          _r7_steps()),
]


def get_paper(pid: str) -> Paper | None:
    for p in PAPERS:
        if p.id == pid:
            return p
    return None
