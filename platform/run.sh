#!/bin/bash
# 启动医学影像 AI 学习平台
# 用法：bash run.sh     然后浏览器打开 http://localhost:8501
set -e
cd "$(dirname "$0")"

# 确保使用 medimg 环境
if ! command -v python >/dev/null || ! python -c "import streamlit" 2>/dev/null; then
  if [ -x "$HOME/miniconda3/envs/medimg/bin/python" ]; then
    export PATH="$HOME/miniconda3/envs/medimg/bin:$PATH"
  else
    echo "未找到 medimg 环境，请先运行：conda activate medimg"
    exit 1
  fi
fi

export MPLCONFIGDIR="$PWD/data/mplconfig"   # 避免 matplotlib 字体缓存写到沙箱外
mkdir -p "$MPLCONFIGDIR"

echo "启动中…… 浏览器请访问 http://localhost:8501"
exec python -m streamlit run app.py \
  --server.port 8501 \
  --server.headless true \
  --browser.gatherUsageStats false
