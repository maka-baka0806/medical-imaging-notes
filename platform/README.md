# 医学影像 AI 学习平台

依据杨振宇老师（昆山杜克大学医学物理）已发表工作构建的本地科研平台。

## 快速开始

```bash
bash serve.sh start            # 启动（仅本机可访问）
bash serve.sh start --public   # 启动并开放公网隧道（自动生成访问口令）
bash serve.sh status           # 查看状态与访问地址
bash serve.sh stop             # 停止
```

启动后控制台会打印访问地址；公网模式还会打印访问口令（也保存在 `data/.access_code`）。

## 页面结构（13 个）

| 分组 | 页面 | 说明 |
|---|---|---|
| 开始 | 概览 | 关键指标、模块与文献映射 |
| 杨振宇老师专栏 | **文献复现专栏** | 9 篇论文 / **57 个可逐步执行的复现步骤** |
| | **文献收藏** | 29 篇成果专藏（位次/主题/核心发现/DOI），可筛选导出 |
| 复现他论文的方法 | 体素级放射组学滤波 | 特征图 + 体素级相关 + 核大小扫描 |
| | 分割与不确定性 | 7 种算法对比 + 多视角扰动 + 共识聚合 |
| | 特征建模与预后 | 共线性/PCA/分类器/交叉验证/融合/生存分析 |
| | 放疗剂量学工具 | DVH、Gamma 指数、球形投影 |
| | 形变配准与物理合理性 | SimpleITK 配准 + Jacobian 折叠检测 |
| 基础训练 | 术语库 / 影像实验室 / 体模实验台 / 学习路线 | 177 条术语、特征提取、参数实验、12 周计划 |
| 参考 | 工具与资源 | 环境自检、启动命令、网络备忘、文献链接 |

## 架构

```
platform/
├── app.py               # 入口：导航 + 口令门 + 错误边界
├── serve.sh             # 守护脚本：启动/停止/状态/公网隧道
├── views/               # 13 个页面
├── core/                # 16 个核心模块
│   ├── theme.py         # 设计系统（干净大气，无装饰图标）
│   ├── auth.py          # 可选访问口令（环境变量 PLATFORM_PASSWORD）
│   ├── capabilities.py  # 依赖检测与优雅降级
│   └── ...              # filtering / segmentation / modeling / survival /
│                        # dosimetry / registration / timeseries / neuralode /
│                        # replication / publications / glossary_parser ...
└── tests/test_app.py    # AppTest 冒烟测试（14 项）
```

## 稳定性与安全

| 措施 | 说明 |
|---|---|
| 默认只绑定 127.0.0.1 | 不暴露到局域网，等价于最小化防火墙 |
| 可选访问口令 | 设置 `PLATFORM_PASSWORD` 后启用（公网模式自动生成） |
| XSRF 防护开启 | `server.enableXsrfProtection = true` |
| CORS 关闭 | 仅同源访问 |
| 错误边界 | 任一页面异常只显示友好提示，不影响其他页面 |
| 能力降级 | 缺少 PyRadiomics / PyTorch 等依赖时，相关页面给出提示而非崩溃 |
| 健康检查 | `serve.sh` 启动后自动检查 `/healthz`，失败会打印日志 |
| 端口自适应 | 默认端口被占用时自动切换到空闲端口 |

### 关于公网访问

`serve.sh start --public` 使用 Cloudflare 快速隧道（无需账号）。
**快速隧道的地址每次重启都会变化**，仅适合临时分享。

**需要永久网址**，请部署到 Streamlit Community Cloud（免费）：

1. 打开 https://share.streamlit.io ，用 GitHub 账号登录
2. 选择仓库 `maka-baka0806/medical-imaging-notes`
3. Main file path 填 `platform/app.py`，点 Deploy

仓库根目录已备好 `requirements.txt` 与 `.streamlit/config.toml`。
云端不安装 PyRadiomics（需编译），平台会自动降级并在相关页面提示。

## 依赖

本地完整环境见 `../setup/环境配置说明.md`（conda 环境 `medimg`）。
