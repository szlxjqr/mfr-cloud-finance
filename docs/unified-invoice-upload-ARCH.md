# 统一发票上传组件 — 系统设计文档 (ARCH)

> 文档编号：ARCH-20260725-001
> 架构师：高见远
> 创建日期：2026-07-25

---

## 1. 实现方案

### 1.1 核心策略

创建 **统一上传组件**（`UploadToInboxDialog.vue`），取代既有报销单「增加发票」弹窗与「发票箱上传」两个面板。上传结果统一入 `invoice_inbox` 表（发票池）。挂发票弹窗 (`AttachInvoiceDialog.vue`) 读取池 + 正式表两源合并展示。

### 1.2 框架选型

- 前端：Vue 3 + TypeScript + Element Plus（已有，不变）
- 后端：FastAPI + SQLAlchemy（已有，不变）
- **新增依赖**：无（OCR 复用 `parseInvoiceFile` + tesseract.js）

### 1.3 设计原则

- **最小变更**：只改前端层，后端 `invoice_inbox` 表已有 7 个 CRUD 端点，基本满足
- **向后兼容**：后端 `invoices` 表的 `reimbursement_bill_id` / `purchase_requisition_item_id` 不变
- **统一入口**：所有上传发票都走同一组件

---

## 2. 文件列表

### 2.1 新建文件

| 文件 | 相对路径 | 说明 |
|------|---------|------|
| 统一上传弹窗 | `frontend/src/components/UploadToInboxDialog.vue` | 多文件拖拽上传 → OCR → 编辑 → 入池 |

### 2.2 修改文件

| 文件 | 相对路径 | 改动 |
|------|---------|------|
| 报销单编辑页 | `frontend/src/views/reimburse/BillList.vue` | 「增加发票」按钮改为调 `UploadToInboxDialog`；删原有 `invoiceDialogVisible` / `invoiceForm` / `submitInvoice` / `onRecognizeFileChange` 等逻辑 |
| 我的报销页 | `frontend/src/views/reimburse/MyReimburse.vue` | 「上传发票/重新识别」按钮改为调 `UploadToInboxDialog`；删 `InvoiceRecognizeDialog` 用法 |
| 发票箱页 | `frontend/src/views/invoice/InvoiceInbox.vue` | 「批量上传并识别」按钮改为调 `UploadToInboxDialog`；删现有上传面板 |
| 挂发票弹窗 | `frontend/src/components/AttachInvoiceDialog.vue` | 调用新 `loadPoolInvoices` 合并池中已识别发票；确认时判断来源（池/正式）分别处理 |
| 前端接口 | `frontend/src/api/inboxApi.ts` | 新增 `batchUpload` 批量上传端点调用（可选，也可复用已有 `upload` 循环） |
| 后端接口 | `backend/app/api/inbox.py` | 新增 `POST /invoice-inbox/batch-upload` 支持多文件同时上传（可选） |

### 2.3 删除文件/代码

| 删除内容 | 行数预估 |
|---------|---------|
| BillList.vue 的 `invoiceDialogVisible` + 相关模板 (~80行) + `invoiceForm` state / `submitInvoice` / `onRecognizeFileChange` 等方法 (~200行) | ~280 行 |
| MyReimburse.vue 的 `InvoiceRecognizeDialog` 引用 + `recognizeVisible` + `onInvoiceConfirm` | ~30 行 |
| MyReimburse.vue 的「上传发票/重新识别」按钮 | 1 行 |

**总计净减**：约 200 行

---

## 3. 数据结构

### 3.1 invoice_inbox 表（已有，后文称为"发票池"）

```python
class InvoiceInbox(Base):
    __tablename__ = "invoice_inbox"
    id: int
    filename: str
    storage_path: str
    source: str           # upload / box
    duplicated: bool
    extracted_json: str | None  # OCR 结果 JSON（含解析后的发票字段）
    status: str           # pending → recognized → linked
    linked_doc_type: str | None  # reimburse / purchase
    linked_doc_id: int | None
    verify_result: str
    verify_note: str | None
    created_at: datetime
    recognized_at: datetime | None
    linked_at: datetime | None
```

### 3.2 关键变化

- 上传组件只写 `invoice_inbox`（status=recognized）
- 挂发票弹窗**只读**两源：`invoice_inbox.recognized` + `invoices.unlinked`
- 确认挂接时：
  - 若来自池：复制字段到正式 `Invoice`，设 `reimbursement_bill_id` / `purchase_requisition_item_id`，池记录 `status=linked`
  - 若来自正式表：直接设 `reimbursement_bill_id` / `purchase_requisition_item_id`

---

## 4. 调用流程

### 4.1 上传入池流程

```
用户: 点「上传发票」按钮
    ↓
UploadToInboxDialog 打开
    ↓
选择文件（多选/文件夹拖拽）
    ↓
enqueue 逐个调用 parseInvoiceFile(file) 进行 OCR
    ↓
展示识别结果列表（每行一张，可展开编辑）
    ↓
用户确认 → 逐个调用 inboxApi.upload(file, extracted_json)
    ↓
全部入 invoice_inbox，status=recognized
    ↓
弹窗关闭 → 回调父组件刷新
```

### 4.2 挂发票流程（更新后）

```
挂发票弹窗打开
    ↓
并行拉取：
  A. 发票池: inboxApi.list({ status: 'recognized', linked_doc_id: null })
  B. 正式表: invoiceApi.list({ unlinked: true })
    ↓
合并去重（按发票号 no）展示
    ↓
用户选择行 + 选择细项 → 确认
    ↓
每条发票判断来源：
  来自池 → 先 inboxApi.link(id, billId, itemId) → 后端复制到 Invoice + 更新池状态
  来自正式表 → invoiceApi.batchLink(invoiceIds, billId, itemId)
    ↓
刷新列表
```

---

## 5. 任务列表（按实现顺序）

### Phase 1: 后端扩展

| 顺序 | 任务 | 文件 | 预估 |
|------|------|------|------|
| 1 | inbox_api.py 新增批量上传端点（可选） | `backend/app/api/inbox.py` | 30 行 |
| 2 | inbox_api.py 新增 `POST /invoice-inbox/{iid}/link-to-bill`：复制池记录 → Invoice + 绑定 | `backend/app/api/inbox.py` | 50 行 |

### Phase 2: 统一上传组件

| 顺序 | 任务 | 文件 | 预估 |
|------|------|------|------|
| 3 | 创建 `UploadToInboxDialog.vue`：拖拽区 + 多文件列表 + 批量 OCR + 识别结果表格 + 编辑 | `frontend/src/components/UploadToInboxDialog.vue` | 350 行 |
| 4 | `inboxApi.ts` 加 `batchUpload`（或复用 upload 循环） | `frontend/src/api/inboxApi.ts` | 10 行 |

### Phase 3: 消费端接入

| 顺序 | 任务 | 文件 | 预估 |
|------|------|------|------|
| 5 | BillList.vue：删「增加发票」弹窗 + 按钮改调 UploadToInboxDialog | `frontend/src/views/reimburse/BillList.vue` | −280 行 |
| 6 | MyReimburse.vue：「上传发票/重新识别」改调 UploadToInboxDialog | `frontend/src/views/reimburse/MyReimburse.vue` | −30 行 |
| 7 | InvoiceInbox.vue：「批量上传并识别」改调 UploadToInboxDialog | `frontend/src/views/invoice/InvoiceInbox.vue` | −40 行 |

### Phase 4: 挂发票弹窗扩展

| 顺序 | 任务 | 文件 | 预估 |
|------|------|------|------|
| 8 | AttachInvoiceDialog.vue：加载发票池已识别记录 + 合并展示 | `frontend/src/components/AttachInvoiceDialog.vue` | +80 行 |
| 9 | AttachInvoiceDialog.vue：确认挂接时判断来源，调用对应接口 | `frontend/src/components/AttachInvoiceDialog.vue` | +40 行 |

### Phase 5: 测试

| 顺序 | 任务 | 文件 | 预估 |
|------|------|------|------|
| 10 | 前端 vue-tsc + build 回归 | - | - |
| 11 | 后端 pytest 回归 | - | - |

---

## 6. 依赖包列表

| 包 | 现有/新增 | 用途 |
|----|----------|------|
| `tesseract.js` | 已有 | OCR 识别（图片类） |
| `pdfjs-dist` | 已有 | PDF 文本提取 |
| `@element-plus/icons-vue` | 已有 | 图标 |
| Element Plus `el-upload` / `el-image` / `el-dialog` | 已有 | UI |

**零新增依赖**。

---

## 7. 共享知识（跨文件约定）

- 挂发票弹窗合并数据时以 `no`（发票号码）去重，池中优先（因池中字段最新）
- `UploadToInboxDialog` 的 props：`modelValue(boolean)`、作为固定独立弹窗，不依赖外部表单上下文
- OCR 解析失败的发票在结果列表中标红（status="解析失败"），可手动创建后再存入池（status="pending"）
- 同一文件重复上传 → 后端 `inboxApi.upload` 已支持 `duplicated` 检测，前端不做深度去重

---

## 8. 待明确事项

| # | 事项 | 建议 | 等待老板确认 |
|---|------|------|-----------|
| A | `inbox_api.py` 的 link-to-bill 端点，复制到 Invoice 时是否需要保留发票细项行？ | 建议：从 `extracted_json.items` 反序列化 → `InvoiceDetail` | □ |
| B | 批量上传接口是新建专用端点还是前端循环调用 `inboxApi.upload`？ | 建议前端循环调用（简单可靠，不新增后端接口） | □**
