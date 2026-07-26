# 万能对话框 · 方案 B — WorkBuddy 连接器接入指引

> 配套：架构 `ai-copilot-arch.md`（已切到方案 B）· 产品 `ai-copilot-prd.md` · 设计 `ai-copilot-design.md`
> 决策：财务 app **只当 MCP 工具执行方**，WorkBuddy 当**主编排 + 对话框**。
> 对话发生在 WorkBuddy，工具（采购/报销/发票 16 个）由本后端经 MCP 暴露、由 WorkBuddy 自定义连接器消费。

---

## 1. 已交付能力

后端在 **`/mcp/`** 暴露 16 个业务工具（采购 5 / 报销 6 / 发票 5），采用 **无状态 Streamable HTTP** 传输。
WorkBuddy 作为 MCP 客户端，通过「自定义连接器（type: http）」连到该端点，即可在对话里调用这些工具完成业务。

- 工具 handler **直接复用现有业务 service**（不重写逻辑），执行权限留在 app 内（安全）。
- 安全分级沿用：`A` 只读/报表直接执行；`B` 创建草稿（可撤销）；`C` 付款/审批/提交（不可逆，本方案下由 WorkBuddy 侧的确认 UX 兜底，工具本身标记 `requires_confirm`）。

## 2. 启动后端（本地）

venv 已升到 **Python 3.13.x** 并装好 `mcp>=1.28`，开箱即用：

```bash
cd backend
.venv/bin/uvicorn app.main:app --port 8521
```

冒烟验证端点（应返回 200，且是 SSE/JSON-RPC 响应）：

```bash
curl -s -X POST http://127.0.0.1:8521/mcp/ \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"1"}}}'
```

## 3. WorkBuddy 自定义连接器配置

在 WorkBuddy 设置 → **连接器（Connectors）** → 新增「自定义连接器（custom connector）」，
类型选 **`http`**（与现有 `~/.workbuddy/.mcp.json` 里的 `connecter-proxy` 同机制），填入：

```json
{
  "type": "http",
  "url": "http://127.0.0.1:8521/mcp/",
  "headers": {
    "Authorization": "Bearer <若后端设了 MCP_AUTH_TOKEN 则填，否则可留空或省略>"
  }
}
```

- **url 必须以 `/mcp/` 结尾（带尾斜杠）**。若只填 `/mcp`，本后端会 307 重定向到 `/mcp/`，WorkBuddy 跟随即可。
- 后端与 WorkBuddy 同机（127.0.0.1）时，连接最稳。跨机/容器需改 host 与防火墙。

## 4. 鉴权（可选）

默认 **不校验** `Authorization`（本地单用户、仅 127.0.0.1 暴露时可用）。

若要在局域网/公网暴露，启动时设环境变量：

```bash
MCP_AUTH_TOKEN=一段随机串 .venv/bin/uvicorn app.main:app --port 8521
```

并在连接器 `headers` 里带 `Authorization: Bearer <同一串>`。未带或错误会返回 `401`。

## 5. 工具清单（16 个，含安全分级）

| 域 | 工具 | 分级 | 说明 |
|---|---|---|---|
| 采购 | `listPurchases` | A | 查采购单（关键字/状态/申请人/供应商） |
| 采购 | `createPurchase` | B | 新建采购草稿 |
| 采购 | `submitPurchase` | C | 提交（自动审批+生成应付凭证） |
| 采购 | `approvePurchase` | C | 审批通过 |
| 采购 | `payPurchase` | C | 付款（结算应付+付款凭证） |
| 报销 | `listReimbursements` | A | 查报销单 |
| 报销 | `createReimbursement` | B | 新建报销草稿 |
| 报销 | `convertFromPurchase` | B | 采购转报销（幂等） |
| 报销 | `submitReimbursement` | C | 提交（自动审批+凭证） |
| 报销 | `approveReimbursement` | C | 审批通过 |
| 报销 | `payReimbursement` | C | 付款 |
| 发票 | `listInvoices` | A | 查发票 |
| 发票 | `createInvoice` | B | 新建发票（含明细） |
| 发票 | `linkInvoice` | B | 发票关联报销单 |
| 发票 | `invoiceSummaryByBill` | A | 按报销单汇总发票金额 |
| 发票 | `voucherDraft` | A | 按发票生成凭证分录草稿（仅预览） |

工具入参 schema 与 `app/services/ai/tools.py` 的 `Tool.parameters` 完全一致（MCP `inputSchema` 直接复用，无漂移）。

## 6. 已验证

用 MCP 官方 Python 客户端（`mcp.client.streamable_http`）实跑通：

1. `initialize` → 握手成功（server: 智慧经营-财务业务工具）。
2. `list_tools` → 返回 **16** 个工具，名称/入参 schema 正确。
3. `call_tool("listPurchases", {})` → 返回 `{"ok": true, "data": []}`（读路径 + DB 接线 OK）。
4. `call_tool("createPurchase", {applicant, item_name, expected_amount})` → 返回新建草稿 `{"ok": true, "data": {...}}`，`status: 草稿`（写路径 + 事务 OK）。

验证全程使用**临时 SQLite**，未触碰真实 `smart_finance.db`。

## 7. 下一步（老板侧）

1. 本地启动后端（见 §2），确认 `/mcp/` 冒烟通过。
2. 在 WorkBuddy 加自定义连接器（见 §3），url 填 `http://127.0.0.1:8521/mcp/`。
3. 在 WorkBuddy 对话框里试着说「列出我最近的采购单」「新建一张办公椅采购草稿」，应能看到工具被调用。
4. 如需跨机/公网，按 §4 设 `MCP_AUTH_TOKEN`。
5. C 级动作（付款/审批）建议让 WorkBuddy 侧在真正调用前做二次确认 UX（工具已标记 `requires_confirm`，可据此拦截）。
