"""MCP 服务：把 ToolRegistry 的 16 个业务工具暴露为 MCP（Streamable HTTP）。

方案 B：财务 app 从「主编排 + 调 WorkBuddy 推理」翻转为「**只当 MCP 工具执行方**」，
WorkBuddy 当主编排 + 对话框，通过自定义连接器（type: http）消费本服务（挂后端 /mcp）。

实现要点：
- 用 FastMCP（无状态 Streamable HTTP）暴露工具，handler 复用 services/ai/tools.py 的 ToolRegistry
  （含 A/B/C 安全分级、复用现有业务 service）。
- 每个 Tool 的动态参数签名由 Tool.parameters（JSON Schema）推导，inputSchema 与 app 内部定义一致。
- `streamable_http_path="/"`：让 FastMCP 内部把消息端点挂在根 "/"，
  这样在 main.py 经 `app.mount("/mcp", ...)` 挂载后，对外端点恰好是 /mcp
  （外层 mount 剥离 /mcp → 内层 Mount("/") 命中 → 叶子 ASGI），避免 /mcp/mcp 双重前缀。
- 每次工具调用：开一个独立 DB Session（check_same_thread=False 已设）→ 解析 owner 账号 → registry.execute → 关闭。
- 鉴权：读 MCP_AUTH_TOKEN 环境变量；若设置，要求 `Authorization: Bearer <token>`，否则 401；
  未设置则放行（本地单用户、仅 127.0.0.1 暴露时可用）。
- 无状态（stateless_http=True）：每次请求独立，挂载最简单（main.py 仅加一行 mount，
  FastMCP 子应用的 lifespan 由 Starlette 驱动）。
"""
from __future__ import annotations

import inspect
import json
import os
from typing import Any, Optional

from starlette.responses import JSONResponse

from mcp.server.fastmcp import FastMCP

from app.db.database import SessionLocal
from app.models import employee as m  # Account 模型在 employee 模块（m.Account）
from app.services.ai.tools import Tool, registry

# 本地单公司：MCP 调用方身份固定映射为 owner 账号（默认取 username="admin"，
# 可用 MCP_OWNER_USERNAME 覆盖；找不到则回退到库中第一个账号）。
_OWNER_USERNAME = os.getenv("MCP_OWNER_USERNAME", "admin")

# JSON Schema 基础类型 → Python 类型（用于 FastMCP 从函数签名推导 inputSchema）
_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _py_type(spec: dict) -> type:
    return _TYPE_MAP.get(spec.get("type", "string"), str)


def _resolve_owner(db) -> Any:
    """解析 MCP 调用方对应的业务账号（Account）。"""
    from sqlalchemy import select

    acc = db.scalar(select(m.Account).where(m.Account.username == _OWNER_USERNAME))
    if acc is None:
        acc = db.scalar(select(m.Account).order_by(m.Account.id).limit(1))
    return acc


def _make_handler(tool: Tool):
    """为某个 Tool 生成一个 async handler，签名由 JSON Schema 推导。"""
    props: dict = tool.parameters.get("properties", {}) or {}
    required: set = set(tool.parameters.get("required", []) or [])
    params = []
    annotations: dict = {}
    for pname, pspec in props.items():
        pyt = _py_type(pspec)
        if pname in required:
            params.append(
                inspect.Parameter(pname, inspect.Parameter.KEYWORD_ONLY, annotation=pyt)
            )
            annotations[pname] = pyt
        else:
            params.append(
                inspect.Parameter(
                    pname, inspect.Parameter.KEYWORD_ONLY, default=None, annotation=Optional[pyt]
                )
            )
            annotations[pname] = Optional[pyt]

    async def handler(**kwargs) -> str:
        # 过滤未提供的可选参数：FastMCP 对可选参数会显式传 None，
        # 而业务 handler 用 kw.get(key, default) 取值，显式 None 会覆盖默认值
        # （如 createPurchase 的 quantity 默认 1、createInvoice 的 details 默认 []），
        # 故此处丢弃 None，让真实默认值生效。
        clean = {k: v for k, v in kwargs.items() if v is not None}
        db = SessionLocal()
        try:
            user = _resolve_owner(db)
            result = await registry.execute(tool.name, clean, db, user)
        finally:
            db.close()
        return json.dumps(result, ensure_ascii=False, default=str)

    # FastMCP 通过 inspect.signature + 类型注解推导 inputSchema；
    # 用 __signature__ / __annotations__ 注入动态签名，使 schema 与 Tool.parameters 对齐。
    handler.__signature__ = inspect.Signature(params)  # type: ignore[attr-defined]
    handler.__annotations__ = annotations
    handler.__name__ = "mcp_" + tool.name
    handler.__doc__ = tool.description
    handler.__module__ = __name__
    return handler


# ── 构建 FastMCP 服务（无状态 Streamable HTTP）──
# streamable_http_path="/"：内部消息端点挂根，使外层 app.mount("/mcp") 后对外即 /mcp。
mcp = FastMCP(
    "智慧经营-财务业务工具",
    stateless_http=True,
    streamable_http_path="/",
)


for _t in registry._tools.values():
    # 装饰器形式注册（兼容各版本）：mcp.tool(name=..., description=...)(handler)
    mcp.tool(name=_t.name, description=_t.description)(_make_handler(_t))


class _AuthMiddleware:
    """可选 Bearer 鉴权（纯 ASGI 包装，便于用 app.mount 挂载）。
    仅当设置了 MCP_AUTH_TOKEN 时启用；未设置则直接透传（本地单用户放行）。"""

    def __init__(self, app, token: str) -> None:
        self.app = app
        self.token = token

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            auth = ""
            for k, v in scope.get("headers", []):
                if k == b"authorization":
                    auth = v.decode("latin-1")
                    break
            if auth != f"Bearer {self.token}":
                resp = JSONResponse({"error": "unauthorized"}, status_code=401)
                await resp(scope, receive, send)
                return
        await self.app(scope, receive, send)


def build_asgi_app():
    """返回可挂载到 FastAPI 的 ASGI app（含可选鉴权中间件）。"""
    token = os.getenv("MCP_AUTH_TOKEN", "").strip()
    app = mcp.streamable_http_app()  # 调用后 mcp._session_manager 才会被惰性创建
    # 缓存会话管理器，供 main.py 生命周期内启动（streamable_http_app 自身不带 lifespan）
    global _SESSION_MANAGER
    _SESSION_MANAGER = mcp._session_manager
    if not token:
        return app
    return _AuthMiddleware(app, token)


# streamable_http_app() 惰性创建，挂在 main.py 生命周期里启动
_SESSION_MANAGER = None


def get_session_manager():
    """供 main.py 生命周期启动 MCP 会话管理器（启动任务组）。"""
    return _SESSION_MANAGER
