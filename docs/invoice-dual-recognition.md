# 发票双识别闸门 · PRD + 架构设计

> 方案 A（已选）：规则引擎① × 规则引擎②（前端，零新依赖）
> 主理人：齐活林｜阶段：PRD(许清楚) + 架构分解(高见远) 合并产出（环境无子智能体工具，由主理人直接跑完 SOP）

## 1. 产品目标
发票识别是系统核心能力。现仅有 **1 套**确定性识别算法（`invoiceFields.ts` 的 `extractInvoiceFields`），同算法跑两次毫无意义。本期新增**第二套逻辑独立的识别器** `extractInvoiceFieldsV2`，两套对同一文本独立识别后**比对**，一致才可信入库；不一致→置 `needs_review` 隔离，不自动信任，交由人工复核/手工录入。彻底无法识别的发票，走既有手工录入。

## 2. 用户故事
- 作为报销会计，上传发票后系统应**自动双重校验**金额/号码/销方，我只在"对不上"时被叫去复核，而不是被脏数据悄悄入库。
- 作为验收人，我希望在发票箱看到"待复核"状态、能一键打开修正并解除隔离。

## 3. 需求池
| 级别 | 需求 |
|------|------|
| P0 | 新增识别器②，逻辑与①独立（标签→就近数值扫描，不依赖 `*xxx*` 锚点与合计行正则） |
| P0 | `dualRecognize(text)` 跑两套并比对：发票号码/日期/销方名称/价税合计/金额合计，容差 0.02 元 |
| P0 | 比对不一致→`status='needs_review'`（前端带 `recognition` 结论，后端按结论落状态） |
| P0 | 发票箱列表支持 `needs_review` 过滤 + "复核"按钮闭环（编辑→`update`→解除隔离） |
| P1 | 前端四路解析（PDF文字/OCR/OFD/PNG）统一走 `dualRecognize` |
| P2 | 二期：识别器②换成 LLM（本地 omlx 或云 OCR），形成"规则×语义"更强双保险 |

## 4. 架构
### 4.1 调用流（时序）
```
文件 → invoiceParser.parseXxx(text)
                └→ dualRecognize(text)
                      ├→ extractInvoiceFields(text)      [识别器① 既有]
                      ├→ extractInvoiceFieldsV2(text)    [识别器② 新增，独立逻辑]
                      └→ 比对 → { result, consistent, diffs }
                result.recognition = { consistent, diffs, method:'dual' }
                → JSON.stringify → 后端 /invoice-inbox/upload
后端 upload / update_inbox：
   读 extracted_json.recognition.consistent
   False → status='needs_review'；否则 → 'recognized'
```
### 4.2 文件清单
| 文件 | 动作 | 说明 |
|------|------|------|
| `frontend/src/utils/invoiceDual.ts` | **新增** | 识别器② + `dualRecognize` 闸门 |
| `frontend/src/utils/invoiceFields.ts` | 改 | `ParsedInvoice` 增 `recognition?` 字段 |
| `frontend/src/utils/invoiceParser.ts` | 改 | 四路解析改调 `dualRecognize` |
| `backend/app/api/invoice_inbox.py` | 改 | upload/update 按 `recognition` 落 `needs_review` |
| `frontend/src/components/StatusTag.vue` | 改 | MAP 增 `needs_review` |
| `frontend/src/views/invoice/InvoiceInbox.vue` | 改 | 过滤项 + 复核按钮 |
| `frontend/src/components/InvoiceRecognizeDialog.vue` | 改 | 支持编辑已有记录（`editId`+`initialParsed`） |
| `frontend/tests/invoice_dual.mjs` | **新增** | 识别器②精度 + 闸门一致性 |
| `backend/tests/test_inbox_dual.py` | **新增** | 后端闸门单测 |

### 4.3 比对规则（容差 0.02 元，沿用现有 `verifyInvoice` 口径）
- 一致 = 发票号码相等 ∧ 日期相等 ∧ 销方名称归一相等 ∧ `|total差|≤0.02` ∧ `|amount差|≤0.02`（两者均有值时）
- 任一不符 → `consistent=false`，`diffs` 记录差异项
- 识别器②完全解析失败（连发票号码都未取到）→ 不阻断（视为"②不可用"），`consistent=true` 但 `method` 标注降级；避免②自身 bug 误伤正常发票

## 5. 质量关卡
- 前端：`node frontend/tests/invoice_dual.mjs`（识别器②在 5 个 fixtures 上与①一致；注入不一致用例→`consistent=false`）
- 前端：`vue-tsc` + `vite build` 通过
- 后端：`pytest` 含 `test_inbox_dual.py`（一致→recognized；不一致→needs_review；update 解除）

## 6. 待明确
- 识别器②暂不做"明细行逐条双比对"（仅做金额/价税合计层面交叉校验）；明细级双保险留待二期 LLM 方案。
- 全量"清库+重入库"在双识别上线后由老板拍板执行（本方案不含清库脚本，仅提供闸门）。
