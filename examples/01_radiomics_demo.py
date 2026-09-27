#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
示例 01：放射组学特征提取最小完整流程
================================================

这是"12 周计划"第 6 周的里程碑任务的最小版本：
    造一个答案已知的合成体模 → 提取放射组学特征 → 理解每组特征的物理含义

为什么用合成体模？
    真实医学数据要申请、要脱敏、格式复杂。而合成体模（数字体模）是
    放射组学领域公认的标定方法——把"答案"掌握在自己手里，才能判断
    特征算得对不对。

运行方式：
    conda activate medimg
    python examples/01_radiomics_demo.py

预期输出：
    107 个特征，涵盖 shape / firstorder / glcm / gldm / glrlm / glszm / ngtdm 七大类
"""

import numpy as np
import SimpleITK as sitk
from radiomics import featureextractor, setVerbosity

setVerbosity(40)  # 只显示警告以上级别


def make_sphere_phantom(size=32, radius=6, tissue_hu=100, noise_sd=10, seed=0):
    """造一个合成体模：空气背景中标一个球（模拟一个"病灶"）。

    参数
    ----
    size      : 立方体边长（体素数）
    radius    : 球的半径（体素数）
    tissue_hu : 球内组织的 HU 值（模拟软组织约 100 HU）
    noise_sd  : 组织内部噪声标准差（模拟图像噪声）
    seed      : 随机种子——**永远固定随机种子**，否则结果不可复现

    返回
    ----
    (image, mask) : 两个 SimpleITK 图像对象
    """
    rng = np.random.RandomState(seed)
    zz, yy, xx = np.mgrid[0:size, 0:size, 0:size]
    mask = ((xx - size // 2) ** 2 + (yy - size // 2) ** 2 + (zz - size // 2) ** 2) <= radius ** 2

    image = np.full((size, size, size), -1000.0, dtype=np.float32)  # 空气 ≈ -1000 HU
    image[mask] = tissue_hu + rng.randn(int(mask.sum())) * noise_sd

    return sitk.GetImageFromArray(image), sitk.GetImageFromArray(mask.astype(np.uint8))


def extract_features(image, mask):
    """用 PyRadiomics 默认配置提取特征。"""
    extractor = featureextractor.RadiomicsFeatureExtractor()
    return extractor.execute(image, mask)


def main():
    print("=" * 62)
    print("示例 01：合成体模的放射组学特征提取")
    print("=" * 62)

    image, mask = make_sphere_phantom()
    print(f"\n体模参数：32³ 体素，球形病灶半径 6 体素，组织 100 HU，噪声 σ=10")

    result = extract_features(image, mask)
    features = {k: float(v) for k, v in result.items() if k.startswith("original_")}

    print(f"\n提取到 {len(features)} 个特征\n")

    # ---- 按类别分组展示：这正是《术语手册》里的特征家族 ----
    groups = {
        "shape": "形状特征（体积/表面积/球形度…）",
        "firstorder": "一阶特征（只看灰度分布）",
        "glcm": "GLCM 灰度共生矩阵（纹理）",
        "gldm": "GLDM 灰度依赖矩阵（纹理）",
        "glrlm": "GLRLM 灰度游程矩阵（纹理）",
        "glszm": "GLSZM 灰度区域大小矩阵（纹理）",
        "ngtdm": "NGTDM 邻域灰度差（纹理）",
    }
    for key, desc in groups.items():
        items = {k.replace(f"original_{key}_", ""): v
                 for k, v in features.items() if k.startswith(f"original_{key}_")}
        if not items:
            continue
        print(f"── {key}（{len(items)} 个）：{desc}")
        for name in list(items)[:3]:
            print(f"     {name:32s} = {items[name]:.4f}")
        print()

    # ---- 用几何公式检验 shape 特征是否正确 ----
    radius_voxels = 6
    expected_volume = 4 / 3 * np.pi * radius_voxels ** 3          # 体素数
    got_volume = features["original_shape_MeshVolume"]
    print("── 正确性检验（shape 特征）")
    print(f"     理论球体积（体素计数） : {expected_volume:.1f}")
    print(f"     PyRadiomics 网格体积   : {got_volume:.1f}")
    print(f"     相对误差              : {abs(got_volume - expected_volume) / expected_volume * 100:.2f}%")
    print("\n     ⚠️ 注意：完美球体的 Elongation 与 Flatness 应等于 1.0：")
    print(f"        Elongation = {features['original_shape_Elongation']:.4f}")
    print(f"        Flatness   = {features['original_shape_Flatness']:.4f}")

    print("\n" + "=" * 62)
    print("下一步练习（见仓库 README 学习路线）：")
    print("  1. 把 radius 改成 4 / 6 / 8，看哪些形状特征随之变化")
    print("  2. 把 noise_sd 改成 0 / 10 / 30，看哪些纹理特征随之变化")
    print("  3. 把 noise_sd=0 而 tissue_hu 改成 50 / 100 / 200，看一阶特征如何变化")
    print("  4. 思考：为什么纹理特征对噪声敏感，而体积不敏感？")
    print("=" * 62)


if __name__ == "__main__":
    main()
