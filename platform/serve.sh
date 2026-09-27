#!/bin/bash
# ============================================================
#  医学影像 AI 学习平台 —— 一键启动 / 守护脚本
# ============================================================
#  用法：
#    bash serve.sh start           启动（本机访问）
#    bash serve.sh start --public  启动并开放公网隧道（自动生成口令）
#    bash serve.sh status          查看状态与访问地址
#    bash serve.sh stop            停止全部
#    bash serve.sh url             只打印当前访问地址
#
#  设计要点：
#    - 服务默认只绑定 127.0.0.1（不暴露到局域网，等价于最小化防火墙）
#    - 端口被占用时自动选择空闲端口
#    - 启动后做健康检查，失败则打印日志尾部
#    - 公网模式自动生成访问口令并写入 .access_code
# ============================================================
set -uo pipefail

PLATFORM_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$PLATFORM_DIR/.." && pwd)"
RUN_DIR="$PLATFORM_DIR/data/run"
PY="$HOME/miniconda3/envs/medimg/bin/python"
CFD="$ROOT_DIR/../tools/cloudflared"
PORT="${PLATFORM_PORT:-8501}"
HOST="127.0.0.1"
mkdir -p "$RUN_DIR"

log()  { printf '  %s\n' "$*"; }
ok()   { printf '  \033[32m%s\033[0m\n' "$*"; }
warn() { printf '  \033[33m%s\033[0m\n' "$*"; }
err()  { printf '  \033[31m%s\033[0m\n' "$*"; }

port_free() {
  ! lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

pick_port() {
  local p="$PORT"
  while ! port_free "$p"; do p=$((p + 1)); done
  echo "$p"
}

start_app() {
  local port="$1"
  export MPLCONFIGDIR="$PLATFORM_DIR/data/mplconfig"
  export PYTHONDONTWRITEBYTECODE=1
  export OMP_NUM_THREADS=1
  mkdir -p "$MPLCONFIGDIR"

  cd "$PLATFORM_DIR"
  nohup "$PY" -m streamlit run app.py \
      --server.address "$HOST" \
      --server.port "$port" \
      --server.headless true \
      --server.enableXsrfProtection true \
      --server.enableCORS false \
      --browser.gatherUsageStats false \
      > "$RUN_DIR/app.log" 2>&1 &
  echo $! > "$RUN_DIR/app.pid"
}

health_check() {
  local port="$1"
  for i in $(seq 1 30); do
    if curl -sf -o /dev/null --max-time 3 "http://$HOST:$port/healthz"; then
      return 0
    fi
    sleep 1
  done
  return 1
}

start_public() {
  local port="${1:-$PORT}"
  if [ ! -x "$CFD" ]; then
    err "未找到 cloudflared（$CFD），无法开启公网隧道"
    return 1
  fi
  # 生成访问口令（若未指定）
  local code
  code="${PLATFORM_PASSWORD:-$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 10)}"
  echo "$code" > "$PLATFORM_DIR/data/.access_code"
  chmod 600 "$PLATFORM_DIR/data/.access_code"
  export PLATFORM_PASSWORD="$code"

  nohup "$CFD" tunnel --url "http://$HOST:$port" --protocol http2 --no-autoupdate \
      > "$RUN_DIR/tunnel.log" 2>&1 &
  echo $! > "$RUN_DIR/tunnel.pid"

  local url=""
  for i in $(seq 1 40); do
    url=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$RUN_DIR/tunnel.log" 2>/dev/null | head -1)
    [ -n "$url" ] && break
    sleep 1
  done
  if [ -n "$url" ]; then
    echo "$url" > "$RUN_DIR/public_url.txt"
    ok "公网隧道已建立"
    return 0
  fi
  err "隧道建立失败，详见 $RUN_DIR/tunnel.log"
  return 1
}

cmd_start() {
  echo "启动医学影像 AI 学习平台"
  if [ -f "$RUN_DIR/app.pid" ] && kill -0 "$(cat "$RUN_DIR/app.pid")" 2>/dev/null; then
    warn "服务已在运行"
  else
    local port; port=$(pick_port)
    [ "$port" != "$PORT" ] && warn "端口 $PORT 被占用，改用 $port"
    echo "$port" > "$RUN_DIR/port.txt"
    start_app "$port"
    if health_check "$port"; then
      ok "服务已就绪（健康检查通过）"
    else
      err "健康检查失败，日志尾部："
      tail -15 "$RUN_DIR/app.log"
      return 1
    fi
  fi

  local port; port=$(cat "$RUN_DIR/port.txt" 2>/dev/null || echo "$PORT")
  echo
  log "本机访问：  http://localhost:$port"

  if [ "${1:-}" = "--public" ] || [ "${1:-}" = "public" ]; then
    start_public "$port" && {
      echo
      log "公网访问：  $(cat "$RUN_DIR/public_url.txt")"
      log "访问口令：  $(cat "$PLATFORM_DIR/data/.access_code")"
    }
  else
    ip=$(ipconfig getifaddr en0 2>/dev/null || echo "")
    [ -n "$ip" ] && log "局域网访问：http://$ip:$port（默认只绑定本机，如需开放见 README）"
  fi
  echo
  ok "完成。停止服务：bash serve.sh stop"
}

cmd_status() {
  echo "平台状态"
  if [ -f "$RUN_DIR/app.pid" ] && kill -0 "$(cat "$RUN_DIR/app.pid")" 2>/dev/null; then
    local port; port=$(cat "$RUN_DIR/port.txt" 2>/dev/null || echo "$PORT")
    if curl -sf -o /dev/null --max-time 3 "http://$HOST:$port/healthz"; then
      ok "应用运行中（健康）  http://localhost:$port   PID $(cat "$RUN_DIR/app.pid")"
    else
      warn "进程存在但健康检查失败，建议重启"
    fi
  else
    warn "应用未运行"
  fi

  if [ -f "$RUN_DIR/tunnel.pid" ] && kill -0 "$(cat "$RUN_DIR/tunnel.pid")" 2>/dev/null; then
    ok "公网隧道运行中  $(cat "$RUN_DIR/public_url.txt" 2>/dev/null || echo '(URL 见 tunnel.log)')"
    [ -f "$PLATFORM_DIR/data/.access_code" ] && \
      log "访问口令：  $(cat "$PLATFORM_DIR/data/.access_code")"
  else
    log "公网隧道未运行"
  fi
}

cmd_stop() {
  echo "停止平台"
  for name in tunnel app; do
    local pf="$RUN_DIR/$name.pid"
    if [ -f "$pf" ]; then
      local pid; pid=$(cat "$pf")
      if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null
        sleep 1
        kill -9 "$pid" 2>/dev/null
        ok "已停止 $name (PID $pid)"
      fi
      rm -f "$pf"
    fi
  done
  ok "完成"
}

cmd_url() {
  local port; port=$(cat "$RUN_DIR/port.txt" 2>/dev/null || echo "$PORT")
  echo "http://localhost:$port"
  [ -f "$RUN_DIR/public_url.txt" ] && echo "$(cat "$RUN_DIR/public_url.txt")"
}

case "${1:-start}" in
  start)  cmd_start "${2:-}" ;;
  status) cmd_status ;;
  stop)   cmd_stop ;;
  url)    cmd_url ;;
  *) echo "用法：bash serve.sh {start [--public] | status | stop | url}" ;;
esac
