"""环境自检：检测科研工具链的安装状态与版本。"""
from __future__ import annotations

import importlib
from dataclasses import dataclass


@dataclass
class Tool:
    key: str          # import 名
    label: str        # 显示名
    category: str
    purpose: str
    version: str = ""
    ok: bool = False


TOOLS: list[tuple[str, str, str, str]] = [
    ("numpy", "NumPy", "数值计算", "数组与矩阵运算，一切的基础"),
    ("scipy", "SciPy", "数值计算", "科学计算：插值、优化、信号处理"),
    ("pandas", "pandas", "数值计算", "表格数据处理与统计分析"),
    ("matplotlib", "matplotlib", "可视化", "科研绘图标准库"),
    ("plotly", "Plotly", "可视化", "交互式图表（本平台的图表引擎）"),
    ("sklearn", "scikit-learn", "机器学习", "经典机器学习：LR/SVM/RF、交叉验证"),
    ("skimage", "scikit-image", "图像处理", "图像滤波、形态学、分割算法"),
    ("SimpleITK", "SimpleITK", "医学影像", "读写成像数据（DICOM/NIfTI）、重采样、配准"),
    ("pydicom", "pydicom", "医学影像", "读写 DICOM 文件（含 RTSTRUCT 等）"),
    ("nibabel", "nibabel", "医学影像", "读写 NIfTI 文件（BraTS 数据格式）"),
    ("itk", "ITK", "医学影像", "配准与分割算法库"),
    ("radiomics", "PyRadiomics", "放射组学", "提取影像组学特征（本平台核心）"),
    ("torch", "PyTorch", "深度学习", "构建与训练神经网络"),
    ("napari", "napari", "查看器", "Python 原生 3D 影像查看器"),
    ("streamlit", "Streamlit", "平台", "本平台所使用的 Web 框架"),
]


def check_tools() -> list[Tool]:
    out: list[Tool] = []
    for key, label, category, purpose in TOOLS:
        t = Tool(key=key, label=label, category=category, purpose=purpose)
        try:
            mod = importlib.import_module(key)
            t.ok = True
            t.version = str(getattr(mod, "__version__", "—"))
        except Exception:
            t.ok = False
        out.append(t)
    return out


def summary(tools: list[Tool]) -> tuple[int, int]:
    ok = sum(1 for t in tools if t.ok)
    return ok, len(tools)
