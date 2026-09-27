# 医学影像 AI 学习平台

把术语库、影像实验室、体模实验台、学习路线、工具链整合成一个本地网站。

## 快速开始

```bash
conda activate medimg
cd ~/医学影像学工作/medical-imaging-notes/platform
streamlit run app.py          # 或：bash run.sh
```

浏览器打开 **http://localhost:8501**

## 六个页面

| 页面 | 作用 |
|---|---|
| 🏠 **概览** | 关键指标、环境状态、学习闭环说明 |
| 📚 **术语库** | 177 条术语，支持中英文搜索、按主题/难度/证据级别筛选，可导出 CSV |
| 🔬 **影像实验室** | 载入体模或上传 NIfTI → 选阈值分割 → 提取 107 个特征 → 导出 CSV |
| 🧪 **体模实验台** | 拖滑杆实时看特征变化；**参数敏感性扫描**输出排行榜与曲线 |
| 🎯 **学习路线** | 12 周计划清单，进度存本地 JSON |
| 🧰 **工具与资源** | 环境自检、启动命令、网络备忘、文献与数据集链接 |

## 目录结构

```
platform/
├── app.py                  # 入口（st.navigation 定义导航）
├── run.sh                  # 一键启动脚本
├── views/                  # 六个页面
│   ├── home.py
│   ├── glossary.py
│   ├── imaging_lab.py
│   ├── phantom_lab.py
│   ├── roadmap.py
│   └── toolbox.py
├── core/                   # 计算与数据核心
│   ├── glossary_parser.py  # 解析 glossary/*.md
│   ├── phantom.py          # 体模生成 + 特征提取
│   └── env_check.py        # 环境自检
└── data/                   # 进度等本地数据（自动生成）
```

## 设计说明

- **所有计算都在本地完成**，影像数据不会上传到任何服务器 —— 这对将来处理真实临床数据很重要。
- 体模生成与特征提取复用 `examples/01_radiomics_demo.py` 的同一套逻辑，保证"示例脚本"和"平台"结果一致。
- 术语库直接解析 `glossary/*.md`，**改 Markdown 就等于改网站内容**，无需动代码。

## 依赖

已在 `medimg` 环境中（见 `../setup/环境配置说明.md`）：
streamlit、plotly、pyradiomics、SimpleITK、numpy、pandas、matplotlib、scikit-learn、torch 等。
