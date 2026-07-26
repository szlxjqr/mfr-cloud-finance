"""AI Copilot 服务层（v1：WorkBuddy 委派 + 采购/报销/发票 三域工具）。

注意：本包不在此处向 app.services / app 注册，待 T7（SSE 路由）+ T8（main include）时由路由层按需导入，
避免提前引入对 WorkBuddy 端点 / httpx 的硬依赖。
"""
from app.services.ai.prompts import SAFETY_TIERS, SYSTEM_PROMPT, build_system_prompt
from app.services.ai.provider import (
    BaseProvider,
    CloudProvider,
    LocalProvider,
    ProviderEvent,
    WorkBuddyProvider,
    get_provider,
    list_providers,
)
from app.services.ai.session import (
    add_message,
    build_openai_messages,
    create_session,
    delete_session,
    get_messages,
    get_session,
    list_sessions,
)
from app.services.ai.tools import Tool, ToolRegistry, registry

__all__ = [
    "BaseProvider",
    "CloudProvider",
    "LocalProvider",
    "ProviderEvent",
    "WorkBuddyProvider",
    "get_provider",
    "list_providers",
    "Tool",
    "ToolRegistry",
    "registry",
    "add_message",
    "build_openai_messages",
    "create_session",
    "delete_session",
    "get_messages",
    "get_session",
    "list_sessions",
    "SYSTEM_PROMPT",
    "SAFETY_TIERS",
    "build_system_prompt",
]
