"""工具与资源页：环境状态、启动命令、参考链接。"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import streamlit as st

from core.env_check import check_tools, summary

REPO = Path(__file__).resolve().parents[2]


def _slicer_installed() -> bool:
    return Path("/Applications/Slicer.app").exists() or \
           Path.home().joinpath("Applications/Slicer.app").exists()


def render() -> None:
    st.title(" 工具与资源")

    # ---------------- 环境状态 ----------------
    st.subheader("① 环境状态")
    tools = check_tools()
    ok, total = summary(tools)

    c1, c2, c3 = st.columns(3)
    c1.metric("工具就绪", f"{ok}/{total}")
    c2.metric("conda 环境", "medimg")
    c3.metric("Python", "3.11.11")

    df = pd.DataFrame([{
"状态": "" if t.ok else "",
        "工具": t.label,
        "版本": t.version or "—",
        "类别": t.category,
        "用途": t.purpose,
    } for t in tools])
    st.dataframe(df, hide_index=True, width="stretch")

    if not _slicer_installed():
        st.warning(
            "**3D Slicer 尚未安装**（唯一需要手动安装的工具）\n\n"
            "1. 打开 https://download.slicer.org/\n"
            "2. 选 **macOS** → **Stable Release** → **Apple Silicon**\n"
            "3. 下载 `.dmg` → 把 Slicer 拖进 Applications\n"
            "4. 首次打开若被拦截：`系统设置 → 隐私与安全性 → 仍要打开`",
            
        )
    else:
        st.success("3D Slicer 已安装 ")

    st.divider()

    # ---------------- 启动命令 ----------------
    st.subheader("② 启动命令（复制到终端执行）")

    st.markdown("**启动本平台**")
    st.code("conda activate medimg\n"
            "cd ~/医学影像学工作/medical-imaging-notes/platform\n"
            "streamlit run app.py", language="bash")

    st.markdown("**启动 JupyterLab（写代码、做分析）**")
    st.code("conda activate medimg\njupyter lab", language="bash")

    st.markdown("**启动 napari（Python 原生 3D 影像查看器）**")
    st.code("conda activate medimg\nnapari", language="bash")

    st.markdown("**运行示例脚本**")
    st.code("conda activate medimg\n"
            "cd ~/医学影像学工作/medical-imaging-notes\n"
            "python examples/01_radiomics_demo.py", language="bash")

    st.markdown("**提交笔记到 GitHub**")
    st.code("cd ~/医学影像学工作/medical-imaging-notes\n"
            "git add .\n"
            'git commit -m "今天学了什么"\n'
            "git push", language="bash")

    st.divider()

    # ---------------- 网络备忘 ----------------
    st.subheader("③ 网络备忘（踩过的坑）")
    st.markdown(
        """
| 场景 | 规则 |
|---|---|
| `pip` / `conda` 装包 | **直连国内镜像**（已永久配置为清华源） |
| 访问 GitHub（curl / git https） | **必须挂校园代理** |
| `git push`（SSH） | 直连即可，无需代理 |
| 报 `ProxyError ... 403` | 说明程序自动读了系统代理 → 加 `export no_proxy="*"` |
| 报连接超时（GitHub） | 挂代理：`export https_proxy=http://proxy-dku.oit.duke.edu:3128` |
        """
    )
    st.code('conda activate medimg\n'
            'export no_proxy="*"          # 装包时最保险\n'
            'pip install 包名', language="bash")

    st.divider()

    # ---------------- 参考资源 ----------------
    st.subheader("④ 参考资源")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**必读文献**")
        st.markdown(
            "- [中文综述：揭开医学图像分析算法的黑箱（科学通报 2025）]"
            "(https://doi.org/10.1360/tb-2024-1299)　← **从这里开始**\n"
            "- [肺放射组学滤波（Med Phys 2022）](https://doi.org/10.1002/mp.15837)\n"
            "- [SPU-Net 不确定性量化（Med Phys 2024）](https://doi.org/10.1002/mp.16695)\n"
            "- [不确定性引导分割（Med Phys 2026）](https://doi.org/10.1002/mp.70360)\n"
            "- [球面卷积预测脑剂量（Med Phys 2025）](https://doi.org/10.1002/mp.17748)"
        )
        st.markdown("**公开数据集**")
        st.markdown(
            "- [TCIA（美国 NCI 影像库）](https://www.cancerimagingarchive.net/)\n"
            "- [BraTS 脑肿瘤分割挑战赛](https://www.med.upenn.edu/cbica/brats/)\n"
            "- [VAMPIRE 肺通气挑战赛](https://vampire-challenge.github.io/)"
        )
    with c2:
        st.markdown("**学习资源**")
        st.markdown(
            "- [PyRadiomics 文档](https://pyradiomics.readthedocs.io/)\n"
            "- [SimpleITK Notebook 教程](https://simpleitk.org/)\n"
            "- [nnU-Net 官方仓库](https://github.com/MIC-DKFZ/nnUNet)\n"
            "- [3D Slicer 文档](https://slicer.readthedocs.io/)\n"
            "- [PhysMorph 配准代码（开源）](https://github.com/DongyangGu0/PhysMorph)"
        )
        st.markdown("**自己的仓库**")
        st.markdown(
            "- [medical-imaging-notes]"
            "(https://github.com/maka-baka0806/medical-imaging-notes)\n"
            "- 术语库：`glossary/`（177 条）\n"
            "- 环境配置：`setup/环境配置说明.md`\n"
            "- 示例脚本：`examples/01_radiomics_demo.py`"
        )

    st.divider()
    st.caption(
        "本平台运行在你的电脑本地（Streamlit），所有计算都在本地完成，"
        "影像数据不会上传到任何服务器 —— 这对将来处理真实临床数据很重要。"
    )
