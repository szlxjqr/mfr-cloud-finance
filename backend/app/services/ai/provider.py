"""AI Provider 抽象层。

v1 唯一可用 Provider = WorkBuddy（委派式 A）：
- WorkBuddy 作为推理 / 工具调用引擎（OpenAI 兼容 /chat/completions，SSE 流式）。
- 业务权限与工具执行留在财务 app 内（安全，WorkBuddy 不直连业务 DB）。

LocalProvider / CloudProvider 为占位 stub（v1 未启用，前端模型选择器仅暴露 WorkBuddy）。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import AsyncIterator, Optional

try:
    import httpx
except ImportError:  # 零新增依赖：仅在真正调用 WorkBuddy 时才需要 httpx
    httpx = None


@dataclass
class ProviderEvent:
    """Provider 流式事件，由 Agent 循环（T6）消费。"""

    kind: str  # "text" | "tool_call" | "done"
    text: str = ""
    tool: Optional[dict] = None  # {"name": str, "arguments": dict}


class BaseProvider:
    name: str = "base"
    label: str = "Base"

    async def stream(
        self, messages: list[dict], tools: Optional[list[dict]] = None
    ) -> AsyncIterator[ProviderEvent]:
        raise NotImplementedError


class WorkBuddyProvider(BaseProvider):
    name = "workbuddy"
    label = "WorkBuddy 委派"

    def __init__(self) -> None:
        self.base_url = os.getenv("WORKBUDDY_API_URL", "").rstrip("/")
        self.api_key = os.getenv("WORKBUDDY_API_KEY", "")
        self.model = os.getenv("WORKBUDDY_MODEL", "default")

    async def stream(
        self, messages: list[dict], tools: Optional[list[dict]] = None
    ) -> AsyncIterator[ProviderEvent]:
        if not self.base_url:
            raise RuntimeError(
                "WORKBUDDY_API_URL 未配置：v1 仅支持 WorkBuddy 委派，"
                "请在环境变量中设置委派端点后再启用"
            )
        if httpx is None:
            raise RuntimeError("未安装 httpx，请先执行 `pip install httpx` 再启用 WorkBuddy 委派")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": 0.2,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        # 累积 tool_calls（OpenAI 流式按片段增量下发，按 index 归并）
        acc: dict[int, dict] = {}

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise RuntimeError(
                        f"WorkBuddy 调用失败 {resp.status_code}: "
                        f"{body.decode('utf-8', 'ignore')[:500]}"
                    )
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    if delta.get("content"):
                        yield ProviderEvent(kind="text", text=delta["content"])
                    tc_list = delta.get("tool_calls")
                    if tc_list:
                        for tc in tc_list:
                            idx = int(tc.get("index", 0))
                            slot = acc.setdefault(idx, {"name": "", "arguments": ""})
                            fn = tc.get("function") or {}
                            if fn.get("name"):
                                slot["name"] += fn["name"]
                            if fn.get("arguments"):
                                slot["arguments"] += fn["arguments"]

        # 流结束后，输出累积的工具调用
        for idx in sorted(acc.keys()):
            slot = acc[idx]
            try:
                args = json.loads(slot["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            yield ProviderEvent(kind="tool_call", tool={"name": slot["name"], "arguments": args})
        yield ProviderEvent(kind="done")


class LocalProvider(BaseProvider):
    name = "local"
    label = "本地模型（暂未启用）"

    async def stream(self, messages, tools=None):
        raise NotImplementedError("v1 未启用本地模型，请选择 WorkBuddy 委派")


class CloudProvider(BaseProvider):
    name = "cloud"
    label = "云端模型（暂未启用）"

    async def stream(self, messages, tools=None):
        raise NotImplementedError("v1 未启用云端模型，请选择 WorkBuddy 委派")


_PROVIDERS = {
    "workbuddy": WorkBuddyProvider,
    "local": LocalProvider,
    "cloud": CloudProvider,
}


def get_provider(name: str = "workbuddy") -> BaseProvider:
    cls = _PROVIDERS.get(name, WorkBuddyProvider)
    return cls()


def list_providers() -> list[dict]:
    return [
        {"name": p.name, "label": p.label, "enabled": p.name == "workbuddy"}
        for p in (WorkBuddyProvider, LocalProvider, CloudProvider)
    ]
