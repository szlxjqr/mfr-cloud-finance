"""tests 目录级夹具：最小 TestClient + admin 鉴权，用于 HTTP 接口级测试。

背景：根 conftest.py 已把 DATABASE_URL 重定向到临时 SQLite（绝不触碰真实库
smart_finance.db），并种入 admin/admin123。这里在此基础上补一个「已登录的
TestClient」，让工资单等接口可以走真实 HTTP 路径（含鉴权依赖）测试，
补上此前 88 个用例「全部直接构造 ORM 对象、零接口测试」的缺口。

注意：
- 不使用 `with TestClient(app)`，避免触发 lifespan（其中会启动 MCP 任务组），
  普通请求无需 lifespan。
- 仅新增测试侧夹具，不改动 app/ 业务代码。
"""
import pytest


@pytest.fixture(scope="session")
def _app():
    from app.main import app  # 延迟导入：确保根 conftest 已完成 DATABASE_URL 重定向

    return app


@pytest.fixture
def client(_app):
    """已携带 admin Bearer Token 的 TestClient（走真实 /api/auth/login）。"""
    from fastapi.testclient import TestClient

    c = TestClient(_app)
    resp = c.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200, f"admin 登录失败：{resp.status_code} {resp.text}"
    c.headers["Authorization"] = f"Bearer {resp.json()['token']}"
    return c
