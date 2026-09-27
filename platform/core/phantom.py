"""体模生成与放射组学特征提取：平台各实验室页面共用的计算核心。"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import SimpleITK as sitk

# 特征家族中文说明（与术语库一致）
FEATURE_FAMILIES = {
    "shape": "形状特征（体积 / 表面积 / 球形度…）",
    "firstorder": "一阶特征（只看灰度分布）",
    "glcm": "GLCM 灰度共生矩阵（纹理）",
    "gldm": "GLDM 灰度依赖矩阵（纹理）",
    "glrlm": "GLRLM 灰度游程矩阵（纹理）",
    "glszm": "GLSZM 灰度区域大小矩阵（纹理）",
    "ngtdm": "NGTDM 邻域灰度差（纹理）",
}


@dataclass
class Phantom:
    """一个合成体模及其解析解，便于验证特征是否正确。"""
    image: np.ndarray
    mask: np.ndarray
    radius: int
    spacing: tuple[float, float, float]

    @property
    def true_volume_mm3(self) -> float:
        return 4 / 3 * np.pi * (self.radius * self.spacing[0]) ** 3

    @property
    def true_volume_voxels(self) -> float:
        return 4 / 3 * np.pi * self.radius ** 3


def make_sphere_phantom(
    size: int = 48,
    radius: int = 8,
    tissue_hu: float = 100.0,
    noise_sd: float = 10.0,
    background_hu: float = -1000.0,
    spacing: float = 1.0,
    seed: int = 0,
    shape: str = "sphere",
) -> Phantom:
    """生成合成体模。

    shape: sphere（球）/ ellipsoid（椭球）/ cube（立方）
    """
    rng = np.random.RandomState(seed)
    c = size // 2
    zz, yy, xx = np.mgrid[0:size, 0:size, 0:size]

    if shape == "sphere":
        inside = ((xx - c) ** 2 + (yy - c) ** 2 + (zz - c) ** 2) <= radius ** 2
    elif shape == "ellipsoid":
        inside = (((xx - c) / radius) ** 2 + ((yy - c) / radius) ** 2
                  + ((zz - c) / max(radius // 2, 1)) ** 2) <= 1
    elif shape == "cube":
        inside = (np.abs(xx - c) <= radius) & (np.abs(yy - c) <= radius) & (np.abs(zz - c) <= radius)
    else:
        raise ValueError(f"未知形状: {shape}")

    image = np.full((size, size, size), background_hu, dtype=np.float32)
    image[inside] = tissue_hu + rng.randn(int(inside.sum())) * noise_sd

    return Phantom(image=image, mask=inside, radius=radius,
                   spacing=(spacing, spacing, spacing))


def to_sitk(phantom: Phantom) -> tuple[sitk.Image, sitk.Image]:
    img = sitk.GetImageFromArray(phantom.image)
    img.SetSpacing(phantom.spacing)
    msk = sitk.GetImageFromArray(phantom.mask.astype(np.uint8))
    msk.SetSpacing(phantom.spacing)
    return img, msk


def slice_view(volume: np.ndarray, mask: np.ndarray | None = None,
               axis: int = 0, index: int | None = None,
               threshold: float | None = None):
    """取一张切片用于显示，返回 (切片, 掩膜切片)。"""
    if index is None:
        index = volume.shape[axis] // 2
    sl = [slice(None)] * 3
    sl[axis] = index
    img2d = volume[tuple(sl)]
    m2d = None
    if mask is not None:
        m2d = mask[tuple(sl)]
    elif threshold is not None:
        m2d = volume[tuple(sl)] >= threshold
    return img2d, m2d


def extract_features(image: sitk.Image, mask: sitk.Image,
                     bin_width: float = 25.0) -> dict[str, float]:
    """提取放射组学特征，返回 {特征名: 数值}。"""
    from radiomics import featureextractor, setVerbosity
    setVerbosity(40)

    settings = {"binWidth": bin_width}
    extractor = featureextractor.RadiomicsFeatureExtractor(**settings)
    result = extractor.execute(image, mask)
    return {k: float(v) for k, v in result.items() if k.startswith("original_")}


def group_features(features: dict[str, float]) -> dict[str, dict[str, float]]:
    """按特征家族分组。"""
    out: dict[str, dict[str, float]] = {}
    for key, value in features.items():
        parts = key.split("_")
        if len(parts) < 3:
            continue
        family = parts[1]
        name = "_".join(parts[2:])
        out.setdefault(family, {})[name] = value
    return out


def to_records(features: dict[str, float]) -> list[dict]:
    """转成可写入 CSV / DataFrame 的记录。"""
    records = []
    for key, value in features.items():
        parts = key.split("_")
        records.append({
            "家族": parts[1] if len(parts) > 2 else "",
            "特征名": "_".join(parts[2:]) if len(parts) > 2 else key,
            "数值": value,
        })
    return records
