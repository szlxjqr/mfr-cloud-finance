#!/bin/bash
# 智慧经营后端启动脚本（Plan A 单机模式）
# 用法：cd backend && ./start.sh
# 行为：先查杀占用 8521 端口的旧后端进程，再干净启动新进程。

PORT=8521
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR" || exit 1

echo "🔪 查杀占用端口 $PORT 的旧后端进程…"

# 1) 按端口精准查杀（覆盖 uvicorn reload 拉起的 worker 子进程）
if command -v lsof >/dev/null 2>&1; then
  OLD_PIDS=$(lsof -ti tcp:"$PORT" 2>/dev/null)
  if [ -n "$OLD_PIDS" ]; then
    echo "   发现旧进程 PID：$OLD_PIDS，正在终止…"
    kill $OLD_PIDS 2>/dev/null
    sleep 1
    OLD_PIDS=$(lsof -ti tcp:"$PORT" 2>/dev/null)
    if [ -n "$OLD_PIDS" ]; then
      echo "   1 秒后仍未退出，强制终止…"
      kill -9 $OLD_PIDS 2>/dev/null
    fi
  else
    echo "   端口 $PORT 当前未被占用，无需查杀。"
  fi
else
  echo "   ⚠️ 未找到 lsof，改按进程名查杀。"
fi

# 2) 兜底：按进程名精准查杀（匹配 app.main，覆盖 reload 主进程与 worker 子进程）
#    不宽泛 pkill uvicorn，避免误伤本机其他 uvicorn 服务。
if pkill -f "app[.]main" 2>/dev/null; then
  echo "   已按进程名 app.main 查杀残留进程。"
fi

# 等端口彻底释放
sleep 1

echo "🚀 启动新的后端（端口 $PORT）…"
exec ./.venv/bin/python -m app.main
