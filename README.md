# medical-imaging-notes

医学影像 AI 学习笔记 —— 目标方向：**医学物理 / 放射组学 / 可解释 AI**

[![terms](https://img.shields.io/badge/术语库-177条-blue)]() [![status](https://img.shields.io/badge/状态-学习中-orange)]()

---

## 我是谁

生物学背景，大一。正在从零开始学 Python、数学与医学影像。
这个仓库记录我的学习过程：术语、代码练习、读书笔记、复现实验。

**为什么做这个方向**：医学影像 AI 的问题来自生理与病理，方法才是物理和计算机 —— 生物学直觉在这里是资产，不是短板。

---

## 术语库（约 180 条）

按主题分成 4 个文件，每条都标了**难度**（`L1` 看一遍就懂 / `L2` 需要一点数学医学背景 / `L3` 得动手做过才真懂），
并对**工具类**词条标注了证据等级（`✅` 论文明确使用 / `🔶` 作为对比方法出现 / `⚪` 领域通用但未见于论文）。

| 文件 | 覆盖范围 | 条数 |
|---|---|---|
| [01 · 临床 · 影像 · 放疗](glossary/01-临床-影像-放疗.md) | 肿瘤学基础、CT/MRI/PET/SPECT、放疗与剂量学（DVH、EQD2、SBRT/SRS…） | 51 |
| [02 · 放射组学 · 图像处理](glossary/02-放射组学-图像处理.md) | 影像组学特征家族、放射组学滤波、分割与配准（FEM、Jacobian…） | 34 |
| [03 · 机器学习 · 统计 · 可解释性](glossary/03-机器学习-统计-可解释性.md) | CNN/U-Net/Transformer、交叉验证与评价指标、XAI 与不确定性量化 | 58 |
| [04 · 工程 · 标准 · 代号 · 数据集](glossary/04-工程-标准-代号-数据集.md) | 软件工具链、AAPM 标准体系、方法代号、公开数据集 | 34 |
| | **合计** | **177** |

> 📌 每个文件末尾或正文中都标出了**容易混淆的词**（例如 GLCOM vs GLCM、两个"蒙特卡洛"、Dice vs HD95）。

### 入门必背 20 个（第一周）

| 术语 | 一句话解释 | 备注 |
|---|---|---|
| **HU** | CT 的密度刻度：水 = 0，空气 ≈ −1000，骨 ≈ +1000 | CT 定量分析的基础 |
| **4DCT** | 按呼吸周期分相位的 CT | 肺通气成像的核心数据 |
| **T1ce** | 注射对比剂后的 T1，血脑屏障破坏区强化 | 增强肿瘤最关键序列 |
| **FLAIR** | 抑制脑脊液信号的 T2 | 看瘤周水肿更清楚 |
| **GTV / CTV / PTV** | 大体肿瘤 / 临床靶 / 计划靶体积 | **GTV 必须医生勾画** |
| **DVH** | 剂量-体积直方图，放疗计划的"体检报告" | D2cc、V12Gy 由此而来 |
| **SBRT / SRS** | 立体定向体部 / 颅脑放疗 | 脑转移瘤常用 SRS |
| **HDR 近距离治疗** | 高剂量率后装治疗 | 剂量跌落极陡 |
| **Radiomics** | 从图像高通量提取定量特征 | 像"给图像做群落调查" |
| **GLCM / GLCOM** | 灰度共生矩阵 | 论文写 GLCOM，标准写 GLCM |
| **GLRLM** | 灰度游程矩阵 | 肺通气研究最强特征来源 |
| **GLSZM** | 灰度区域大小矩阵 | |
| **一阶特征** | 只看灰度分布，不看空间关系 | |
| **滑窗 / radiomic filtering** | 小窗逐体素滑动，每处算一组特征 | 特征于是成为"特征图" |
| **IBSI** | 影像组学标准化倡议 | 相当于 qPCR 的 MIQE |
| **U-Net** | 编码器 + 解码器 + 跳跃连接 | 医学分割经典网络 |
| **nnU-Net** | 自动配置结构的医学分割框架 | 先跑通官方教程 |
| **Dice 系数** | `2×A∩B ÷ (A+B)` | **就是 Sørensen 相似性指数** |
| **HD95** | 边界距离的 95 分位 | Dice 高不代表边界准 |
| **AUC / ROC** | 判别能力曲线下面积 | 0.5 抛硬币，1.0 完美 |

---

## 🖥️ 本地学习平台（本仓库最大的一块）

把术语库、影像实验室、体模实验台、学习路线、工具链整合成一个**本地网站**：

```bash
conda activate medimg
cd ~/医学影像学工作/medical-imaging-notes/platform
streamlit run app.py        # 或 bash run.sh
```

浏览器打开 **http://localhost:8501**

| 页面 | 作用 |
|---|---|
| 🏠 **概览** | 关键指标、环境自检、学习闭环 |
| 📚 **术语库** | 177 条术语**可搜索可筛选**，支持导出 CSV |
| 🔬 **影像实验室** | 载入体模/上传 NIfTI → 阈值分割 → 提取 107 个特征 → 导出 |
| 🧪 **体模实验台** | 拖滑杆实时看特征变化；**参数敏感性扫描**出排行榜与曲线 |
| 🎯 **学习路线** | 12 周清单，进度存本地 |
| 🧰 **工具与资源** | 环境状态、启动命令、网络备忘、文献链接 |

> **所有计算都在本地完成，影像数据不上传任何服务器** —— 这对将来处理真实临床数据很重要。
>
> 代码见 [`platform/`](platform/)，说明见 [platform/README.md](platform/README.md)。

---

## 学习路线

- **阶段 1（第 1–4 周）**：Python + NumPy + matplotlib + 医学影像 IO（SimpleITK / 3D Slicer）
- **阶段 2（第 5–8 周）**：放射组学（PyRadiomics）+ 统计与相关分析
- **阶段 3（第 9–12 周）**：PyTorch + U-Net 分割 + 不确定性可视化

**里程碑作品**（计划中）：

- [ ] 手写 Dice / IoU / HD95，并构造典型错误对比
- [ ] 用 NumPy 实现 3D 滑窗，生成放射组学特征图
- [ ] 训练 2D U-Net 做分割，报告 Dice
- [ ] 多次推理 → 计算方差 → 画不确定性热力图

---

## 环境与工具

**已配置完成**（详见 [setup/环境配置说明.md](setup/环境配置说明.md)）：

| 用途 | 工具 | 版本 | 状态 |
|---|---|---|---|
| 包管理 | Miniconda（环境名 `medimg`） | conda 26.7.1 | ✅ |
| 语言 | Python | 3.11.11 | ✅ |
| 数值计算 | NumPy / SciPy / pandas | 2.4.6 / 1.17.1 / 3.0.6 | ✅ |
| 可视化 | matplotlib / seaborn | 3.11.2 / 0.13.2 | ✅ |
| 机器学习 | scikit-learn | 1.9.1 | ✅ |
| 图像处理 | scikit-image / OpenCV | 0.26.0 / — | ✅ |
| **医学影像 IO** | **SimpleITK / pydicom / nibabel / ITK** | 2.5.6 / 3.0.2 / 5.4.2 / — | ✅ |
| **放射组学** | **PyRadiomics** | 3.0.1 | ✅ |
| 深度学习 | PyTorch / torchvision（conda-forge 版） | 2.10.0 / 0.26.0 | ✅ MPS 加速可用 |
| 交互环境 | JupyterLab | 4.6.4 | ✅ |
| 3D 影像查看器 | napari | 0.9.1 | ✅ |
| 阅片/勾画 | 3D Slicer | — | ⬜ 待手动安装 |
| 版本管理 | Git + GitHub（SSH 免密） | 2.50.1 | ✅ |

一键复现环境：

```bash
conda activate medimg                 # 激活
python examples/01_radiomics_demo.py  # 跑第一个示例
conda env create -f setup/environment.yml   # 在别的机器上重建
```

> 💡 **本机网络备忘（踩过的坑）**
> - **命令行工具默认不走系统代理**：`git` / `curl` 直连 GitHub 会超时 → 需要 `export https_proxy=http://proxy-dku.oit.duke.edu:3128`
> - **但 conda / pip 会自动读取系统代理**：走校园代理访问清华镜像会被 **403 拒绝** → 需要 `export no_proxy="*"`
> - **一句话记住**：**镜像直连，GitHub 挂代理**。pip 与 conda 已永久指向清华镜像。

---

## 可运行示例

| 脚本 | 内容 | 状态 |
|---|---|---|
| [examples/01_radiomics_demo.py](examples/01_radiomics_demo.py) | 合成体模 → 提取 107 个放射组学特征 → 用几何公式验证形状特征 | ✅ 已跑通 |

`01_radiomics_demo.py` 的输出示例：

```
提取到 107 个特征
── shape（14 个）      Elongation = 1.0000   Flatness = 1.0000
── firstorder（18 个） 10Percentile = 86.61  90Percentile = 111.85
── glcm（24 个）       Autocorrelation = 6.06
── gldm（14 个）       DependenceEntropy = 4.73
── glrlm（16 个）      GrayLevelNonUniformity = 267.30
── glszm（16 个）      GrayLevelNonUniformity = 6.69
── ngtdm（5 个）       Busyness = 21.79  Coarseness = 0.0044

正确性检验：理论球体积 904.8 vs PyRadiomics 911.5（相对误差 0.74%）
完美球体的 Elongation 与 Flatness 应等于 1.0 —— 实测正是 1.0000 ✅
```

---

## 学习日志

| 日期 | 做了什么 | 遇到的问题 / 收获 |
|---|---|---|
| 2026-09-27 | 创建仓库、配置 SSH 免密推送、整理 177 条术语 | GitHub 直连超时 → **查明是命令行不走系统代理**，加代理后解决 |
| 2026-09-27 | 装 Miniconda + 建 `medimg` 环境 + 装 14 类科研包 | conda 自动读系统代理 → 访问清华镜像 **403** → 用 `no_proxy` 绕过；**PyRadiomics 无 arm64 预编译包，从源码编译成功** |
| 2026-09-27 | 跑通第一个示例：合成体模特征提取 107 个 | 网格体积比理论值大 0.74%——体素化导致的正常误差 |
| 2026-09-27 | 修复 OpenMP 冲突（`import torch` 崩溃） | pip 版 torch 自带 `libomp.dylib`，与 conda 的 libomp 撞车 → **改用 conda-forge 版 PyTorch** 统一运行时 |
| 2026-09-27 | 搭建本地学习平台（6 个页面的 Streamlit 网站） | 踩到 matplotlib 中文缺字（换 Arial Unicode MS 解决）与 Streamlit `use_container_width` 弃用 |

---

## 参考

- 杨振宇（昆山杜克大学医学物理）研究方向：放射组学、医学影像 AI、可解释性与不确定性量化
- 中文入门综述：《揭开医学图像分析算法的黑箱：医学图像分析中可解释人工智能的最新进展》，科学通报 2025，DOI [10.1360/tb-2024-1299](https://doi.org/10.1360/tb-2024-1299)

---

## 目录结构

```
medical-imaging-notes/
├── README.md                 # 本文件：项目说明 + 术语索引 + 环境 + 学习日志
├── glossary/                 # 术语库（177 条，按主题分 4 个文件）
│   ├── 01-临床-影像-放疗.md
│   ├── 02-放射组学-图像处理.md
│   ├── 03-机器学习-统计-可解释性.md
│   └── 04-工程-标准-代号-数据集.md
├── platform/                 # 🖥️ 本地学习平台（Streamlit 网站）
│   ├── app.py                #    入口
│   ├── views/                #    六个页面
│   └── core/                 #    术语解析 / 体模计算 / 环境自检
├── examples/                 # 可运行示例
│   └── 01_radiomics_demo.py
├── setup/                    # 环境配置
│   ├── 环境配置说明.md
│   ├── environment.yml
│   ├── requirements.txt
│   └── requirements-full.txt
└── .gitignore
```

*持续更新中。*
