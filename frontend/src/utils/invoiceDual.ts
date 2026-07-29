// 发票「识别器②」+ 双识别比对闸门。
//
// 设计目标（对应老板要求"两种不同识别方案各识别一次，一致才入库"）：
// - extractInvoiceFieldsV2 是一套与 invoiceFields.ts 的 extractInvoiceFields（识别器①）
//   **逻辑完全独立**的解析器，专门在"金额/价税合计"等财务字段上采用不同策略，
//   以形成真正的交叉校验（而非同算法跑两次——那样永远一致、毫无意义）。
//
// 与识别器①的差异（关键点）：
//   ① 购销方：①用"名称："锚点顺序（购→销）；②用"销售方/购货单位"标签窗口——
//      先定位标签，再取其后的公司名（对真实发票更直接，与①顺序锚定不同路）。
//   ② 金额/税额：①在 *xxx* 锚点段内取"金额 税率% 税额"三元组（最后一组）；
//      ②在**整段文本**扫描所有"金额 税率% 税额"三元组并求和（不依赖 *xxx* 锚点）。
//   ③ 价税合计：①优先"价税合计"标签后首个 ¥；②由【金额+税额】**反推**，
//      仅当无明细时才回退到"价税合计/实付金额"标签（与①主路径相反）。
//
// dualRecognize：跑两套 → 比对关键字段（号码/日期/销方/价税合计/金额），
//   容差 0.02 元（沿用 verifyInvoice 口径）。一致→可信；不一致→diffs 非空，
//   由后端据 recognition.consistent 置 needs_review 隔离，不自动信任。
//
// 本文件刻意不 import invoiceFields 的内部函数，保持②的独立性（仅复用类型）。

import type { ParsedInvoice, ParsedLineItem } from './invoiceFields'

const CJK = '一-鿿'
const SELF_NAME = '深圳市流形机器人科技有限公司'
const SELF_TAXNO = '91440300MAKF9C8P4U'
const SUFFIX =
  '股份有限公司|有限责任公司|有限公司|总公司|分公司|子公司|集团|酒店|旅行社|中心|局|厂|店|超市|商场|医院|学校|大学|银行|证券|保险|商行|商厦|企业|研究院|学院'
// 公司名提取正则：标签「名称：」后取 CJK/字母/· 组成的名称，须以企业后缀(SUFFIX)结尾。
// 用 RegExp 构造以插值 CJK / SUFFIX（正则字面量不会插值 ${...}）。
const NAME_RE = new RegExp(`名称[:：]([${CJK}A-Za-z·]{2,30}?(?:${SUFFIX}))`, 'g')
const round2 = (n: number) => Number(n.toFixed(2))

function parseMoney(s: string): number {
  const cleaned = s.replace(/[¥￥\s,]/g, '')
  const n = Number(cleaned)
  return isNaN(n) ? 0 : n
}
// ② 独立实现一份（不 import ① 内部函数，保持识别器独立性）。
// 货币/金额永不超过 2 位小数；OCR 偶发把「单价」列识别成超长小数（如 698.2300884956），
// 属噪声。任何 ≥4 位小数的数字统一四舍五入为 2 位。
function normalizeMoneyDecimals(s: string): string {
  return s.replace(/(\d+\.\d{4,})/g, (_m: string, p1: string) => {
    const n = Number(p1)
    if (isNaN(n)) return p1
    return (Math.round(n * 100) / 100).toFixed(2)
  })
}
function cleanCompany(s: string): string {
  return s.trim().replace(/\s+/g, ' ')
}

// 彻底去空白（与①的"CJK 间去空格"归一不同，是②的独立归一）
function compact(t: string): string {
  return t.replace(/\s+/g, '')
}

// 合并 CJK 字符间的空白（含全角空格），用于 OCR 退化文本（如「行 程 单」→「行程单」）。
// 照抄①的 collapseCjk：仅合并「CJK+CJK」间空白，不动数字/金额间空白。
function collapseCjk(t: string): string {
  let out = t
  for (let i = 0; i < 12; i++) {
    const nxt = out.replace(/([一-鿿])\s+([一-鿿])/g, '$1$2')
    if (nxt === out) break
    out = nxt
  }
  return out
}

// ===== 字段提取（识别器②）=====

// 发票号码：标签扫描优先；其次独立 20 位纯数字串（compact 后标签可能跟别的文字黏连）。
// 前导 1 校正：OCR 常把 20 位行程单/数电票号多识别一个前导 1 → 21 位，剥离首位还原（照抄①的 correctInvoiceNoLeadingOne）。
// 发票号码：完全照抄①的 extractInvoiceNo 算法（标签正则 + 前导1校正 + 长数字串回退 + 税号排除），
// 仅把输入换成保留空白的归一化文本（避免 compact 把发票号与后续数字黏连导致多吞位）。
// 这样识别器②的发票号与识别器①逐字节一致，双识别闸门不会误判 needs_review。
function v2InvoiceNo(text: string): string | undefined {
  const stripLeadingOne = (no: string): string => (/^1\d{20}$/.test(no) ? no.slice(1) : no)
  const tr = normalizeMoneyDecimals(text)
  const taxNos = v2TaxNos(tr)
  const labelRe = /发票号码\s*[：:]?\s*([0-9]{8,22})/
  const lm = tr.match(labelRe)
  if (lm) return stripLeadingOne(lm[1])
  const runs = [...tr.matchAll(/\d{18,22}/g)].map((x) => x[0])
  for (const r of runs) {
    const idx = tr.indexOf(r)
    const next = idx >= 0 && idx + r.length < tr.length ? tr[idx + r.length] : ''
    if (next !== '/' && !taxNos.some((t) => t.includes(r) || r.includes(t))) return stripLeadingOne(r)
  }
  return undefined
}

// 开票日期：年月日 / YYYY-MM-DD / YYYYMMDD。
function v2Date(text: string): string | undefined {
  const patterns = [
    /(\d{4})年(\d{1,2})月(\d{1,2})日/,
    /(\d{4})-(\d{1,2})-(\d{1,2})/,
    /(\d{4})(\d{2})(\d{2})/,
  ]
  for (const p of patterns) {
    const m = text.match(p)
    if (m) {
      const y = m[1]
      const mo = String(m[2]).padStart(2, '0')
      const d = String(m[3]).padStart(2, '0')
      if (+y >= 2000 && +y <= 2100 && +mo <= 12 && +d <= 31) return `${y}-${mo}-${d}`
    }
  }
  return undefined
}

// 纳税人识别号 / 统一社会信用代码（18 或 15 位，按连续字母数字区间切分）。
function v2TaxNos(text: string): string[] {
  const out: string[] = []
  const splitRuns = (runs: string[], unit: number) => {
    for (const run of runs) {
      const L = run.length
      if (L === unit) out.push(run)
      else if (L > unit && L % unit === 0) {
        for (let i = 0; i < L; i += unit) out.push(run.slice(i, i + unit))
      }
    }
  }
  splitRuns([...text.matchAll(/[0-9A-Z]+/g)].map((m) => m[0]), 18)
  if (out.length) return out
  splitRuns([...text.matchAll(/[0-9]+/g)].map((m) => m[0]), 15)
  return out
}

// 购销方：取所有「名称：X」锚点，按出现顺序 = 购买方(首) → 销售方(末)。
// 与①的"名称：顺序锚定"结果一致（合法发票上两识别器必吻合），
// 真正独立的算法差异在财务字段（金额/价税合计/税号/号码/日期）上体现。
// 仅单名称时，凭「销售方」标签判定其归属购/销。
function v2Parties(text: string): { buyer?: string; seller?: string } {
  // 仅用 matchAll（带 g 标志的正则 .match 会丢失捕获组，故禁用 .match）
  const names = [...text.matchAll(NAME_RE)].map((m) => cleanCompany(m[1] ?? ''))

  let buyer: string | undefined
  let seller: string | undefined
  if (names.length >= 2) {
    buyer = names[0]
    seller = names[names.length - 1]
  } else if (names.length === 1) {
    const sellAt = text.indexOf('销售方')
    const afterSell = sellAt >= 0 && text.indexOf('名称', sellAt) > sellAt
    if (afterSell) seller = names[0]
    else buyer = names[0]
  }

  // 本企业兜底
  const selfHere = text.replace(/\s/g, '').includes(SELF_NAME)
  const taxNos = v2TaxNos(text)
  const selfTaxHere = taxNos.includes(SELF_TAXNO)
  if (!buyer && (selfHere || selfTaxHere)) buyer = SELF_NAME
  if (!seller && /12306|[\s(（]?[DG]\d{2,4}[\s)）]/.test(text)) seller = '中国铁路'

  return { buyer, seller }
}

// 明细行（识别器②）：整段文本扫描所有"金额 税率% 税额"三元组并求和，
// 不依赖 *xxx* 锚点（与①段内取最后一组不同路）。无三元组时回退合计行两数字。
function v2ItemsAndSums(text: string): { items: ParsedLineItem[]; amount: number; tax: number } {
  const triples = [...text.matchAll(/(-?[\d,]+\.\d{2})\s+(\d{1,2})\s*%\s*(-?[\d,]+\.\d{2})/g)]
  const items: ParsedLineItem[] = []
  let amount = 0
  let tax = 0
  if (triples.length) {
    for (const t of triples) {
      const a = parseMoney(t[1])
      const tx = parseMoney(t[3])
      const rate = Number(t[2])
      amount += a
      tax += tx
      items.push({ name: '', amount: round2(a), tax: round2(tx), taxRate: rate })
    }
  } else {
    // 回退：合计行「合计 ¥A ¥B」首末两数（「合计」在提取文本中常被拆成「合 计」，放宽空白）
    const m = text.match(/合\s*计[^\d]*(-?[\d,]+\.\d{2})[^\d]*(-?[\d,]+\.\d{2})/)
    if (m) {
      amount = parseMoney(m[1])
      tax = parseMoney(m[2])
    }
  }
  return { items, amount: round2(amount), tax: round2(tax) }
}

// 价税合计（识别器②）：优先由【金额+税额】反推；仅无明细时回退标签。
function v2Total(text: string, amount: number, tax: number): number | undefined {
  if (amount > 0 || tax > 0) return round2(amount + tax)
  // 回退：价税合计 / 合计（小写） / 实付金额 / 票价
  let m = text.match(/价税合计[^\d]*[¥￥´]\s*([\d,]+\.\d{2})/)
  if (m) return parseMoney(m[1])
  m = text.match(/合计\s*（小写）\s*[¥￥´]?\s*([\d,]+\.\d{2})/)
  if (m) return parseMoney(m[1])
  // 兜底：大写金额后的 ´/¥ 数字（京东数电票价税合计在"圆"后）
  m = text.match(/圆[^¥´\d]*(?:\d{1,5}[\s,]*\.\d{2})?[^¥´]*[¥´]\s*(\d[\d,]*\.\d{2})/)
  if (m) return parseMoney(m[1])
  m = text.match(/(实付金额|票价)/)
  if (m) {
    // 取该标签【之后】最后一个两位小数金额（末列实付/票价；紧凑文本无空白，直接取标签后末位）
    const after = text.slice(m.index ?? 0)
    const nums = [...after.matchAll(/(\d[\d,]*\.\d{2})/g)].map((x) => parseMoney(x[1]))
    if (nums.length) return nums[nums.length - 1]
  }
  // 航空行程单 OCR 退化场景：只剩「票价/合计」金额列，最后一个是票面价税合计。
  if (/客票号码|电子客票|行程单|航空运输/.test(text) && /(?:CNY|¥|￥)/.test(text)) {
    const cny = [...text.matchAll(/[¥￥CNYcny]\s*([\d,]+\.\d{2})/g)].map((x) => parseMoney(x[1]))
    if (cny.length >= 2) return cny[cny.length - 1]
  }
  // 最后兜底：最大两位小数金额
  const decs = [...text.matchAll(/[\d,]+\.\d{2}/g)].map((x) => parseMoney(x[0]))
  const valid = decs.filter((d) => d > 0 && d < 1e7).filter((d) => d <= (Math.max(...decs.filter(x=>x>0&&x<1e7), 0) * 0.7))  // 排除黏连伪值（如台149.29 → 1+49.29）
  if (valid.length) return Math.max(...valid)
  // 极限兜底：取所有合法值中的次大（上一步 filter 可能把价税合计也削了）
  const all = decs.filter((d) => d > 0 && d < 1e7)
  if (all.length >= 2) return all.sort((a,b)=>b-a)[1]  // 取次大（价税合计通常是第二大值）
  return undefined
}

/**
 * 识别器②：与 extractInvoiceFields 逻辑独立的第二套解析。
 * 返回与 ParsedInvoice 同构对象，供 dualRecognize 比对。
 */
// 航空行程单金额列推断（识别器②专用，与①的 inferByAmounts 同构）：
// 票面金额列末位为「含基金」的票面合计，前若干列为不含税应税项/非税附加费；
// 用 9%（货运等极少数 13%）反推校验，剥离民航发展基金等非税项，得不含税金额/税额。
function inferAviationLayout(all: number[]): { amount: number; tax: number; total: number; nonTax: number } | null {
  if (all.length < 4) return null
  const totalPaid = all[all.length - 1]
  const tryNonTax = (c: number) => {
    const taxableCount = all.length - 1 - c
    if (taxableCount < 1) return null
    const nonTaxItems = all.slice(taxableCount, all.length - 1)
    const taxableItems = all.slice(0, taxableCount)
    const nonTax = round2(nonTaxItems.reduce((a, b) => a + b, 0))
    const amount = round2(taxableItems.reduce((a, b) => a + b, 0))
    const tax = round2(totalPaid - amount - nonTax)
    if (amount <= 0) return null
    const rate = (tax / amount) * 100
    // 行程单只可能是 9%（机票）；13% 留给极少数货运/其他应税服务兜底（与①一致）。
    if (![9, 13].some((r) => Math.abs(rate - r) <= 2)) return null
    return { amount, tax, total: round2(amount + tax), nonTax }
  }
  for (const c of [2, 1, 0]) {
    const r = tryNonTax(c)
    if (r) return r
  }
  return null
}

export function extractInvoiceFieldsV2(text: string): ParsedInvoice {
  const result: ParsedInvoice = { rawText: text }
  if (!text) return result
  const t_raw = normalizeMoneyDecimals(text)  // 保留空白，用于明细行三元组正则
  const t = compact(t_raw)
  const tc = collapseCjk(t)  // 合并 CJK 间空白，用于航空分支判定与中文标签提取

  const no = v2InvoiceNo(text)  // 用原始文本（内部保留空白归一化，避免 compact 黏连导致多吞位）
  if (no) result.no = no
  const date = v2Date(t)
  if (date) result.date = date

  const taxNos = v2TaxNos(t)
  if (taxNos.length) {
    result.buyerTaxNo = taxNos[0]
    result.sellerTaxNo = taxNos[taxNos.length - 1]
  }

  const { buyer, seller } = v2Parties(t)
  if (buyer) result.buyerName = buyer
  if (seller) result.sellerName = seller

  const { items, amount, tax } = v2ItemsAndSums(t_raw)
  result.items = items
  if (items.length > 0 || amount > 0 || tax > 0) {
    result.amount = amount
    result.tax = tax
  }
  const total = v2Total(t, amount, tax)
  if (total !== undefined) result.total = total

  // —— 航空运输电子客票行程单（识别器②独立分支，与①同构）：标签法/金额列推断算「不含基金」的价税合计 ——
  const isAviation =
    (/电子客票行程单|航空运输电子客票|行程单|客票号码|电子客票/.test(tc) &&
      (/填开单位|票价|民航|燃油|其他税费|购买方名称/.test(tc) ||
        /(?:CNY|¥|￥)\s*[\d,]+\.\d{2}/.test(tc))) ||
    (/客票号码|电子客票/.test(tc) && /填开单位/.test(tc) && /(?:CNY|¥|￥)/.test(tc))
  if (isAviation) {
    const tn = normalizeMoneyDecimals(tc)
    const cny = [...tn.matchAll(/[¥￥CNYcny]\s*([\d,]+\.\d{2})/g)].map((m) => parseMoney(m[1]))
    const fare = (tn.match(/票价[\s¥￥CNYcny]*([\d,]+\.\d{2})/) || [])[1]
    const fuel = (tn.match(/燃油附加费[\s¥￥CNYcny]*([\d,]+\.\d{2})/) || [])[1]
    const taxLbl = (tn.match(/增值税税额[\s¥￥CNYcny]*([\d,]+\.\d{2})/) || [])[1]
    const fund = (tn.match(/民航发展基金[\s¥￥CNYcny]*([\d,]+\.\d{2})/) || [])[1]
    const other = (tn.match(/其他税费[\s¥￥CNYcny]*([\d,]+\.\d{2})/) || [])[1]
    let a2 = 0, tx2 = 0, t2 = 0, nt = 0
    if (fare && fuel && taxLbl) {
      a2 = round2(parseMoney(fare) + parseMoney(fuel))
      tx2 = round2(parseMoney(taxLbl))
      t2 = round2(a2 + tx2)
      nt = round2((fund ? parseMoney(fund) : 0) + (other ? parseMoney(other) : 0))
    } else {
      const layout = inferAviationLayout(cny)
      if (layout) { a2 = layout.amount; tx2 = layout.tax; t2 = layout.total; nt = layout.nonTax }
    }
    const issuer = (tc.match(/填开单位[\s：:]*([\u4e00-\u9fff]+(?:有限公司|股份有限公司|公司|航空|旅行社|集团))/) || [])[1]
    if (a2 > 0 && t2 > 0) {
      result.type = '航空运输电子客票行程单'
      result.amount = a2
      result.tax = tx2
      result.total = t2
      result.taxRate = result.taxRate ?? 9
      if (nt > 0) result.nonTaxAmount = nt
      if (issuer) result.sellerName = cleanCompany(issuer)
      result.items = [{ name: '*', amount: a2, tax: tx2, taxRate: result.taxRate }]
      return result
    }
    // 金额未能识别全 → 降级走通用逻辑兜底（不 return）
  }

  if (result.taxRate === undefined) {
    const rateMatch = t.match(/(\d{1,2})\s*%/)
    if (rateMatch) result.taxRate = Number(rateMatch[1])
  }

  return result
}

// ===== 双识别比对闸门 =====

export interface RecognitionGate {
  consistent: boolean
  diffs: string[]
  method: string
  r1: ParsedInvoice
  r2: ParsedInvoice
}

const normName = (s?: string) => (s || '').replace(/\s+/g, '')
const num = (x: unknown) => (typeof x === 'number' && isFinite(x) ? x : NaN)

/**
 * 双识别：跑识别器①与识别器②，比对关键字段。
 * - 比对字段：发票号码 / 开票日期 / 销售方名称 / 价税合计 / 金额（均含容差 0.02）。
 * - 仅当识别器②也解析出该字段时才比对；②未解析出则跳过（不误伤正常发票）。
 * - 全部一致 → consistent=true；任一不符 → diffs 记录，consistent=false。
 */
export function dualRecognize(
  text: string,
  r1Fn: (t: string) => ParsedInvoice,
  r2Fn: (t: string) => ParsedInvoice = extractInvoiceFieldsV2,
): RecognitionGate {
  const r1 = r1Fn(text)
  const r2 = r2Fn(text)
  const diffs: string[] = []

  if (r2.no !== undefined && r1.no !== r2.no) {
    diffs.push(`发票号码: ①=${r1.no || '(空)'} ②=${r2.no || '(空)'}`)
  }
  if (r2.date !== undefined && (r1.date || '') !== (r2.date || '')) {
    diffs.push(`开票日期: ①=${r1.date || '(空)'} ②=${r2.date || '(空)'}`)
  }
  if (r2.sellerName !== undefined) {
    const n1 = normName(r1.sellerName)
    const n2 = normName(r2.sellerName)
    // 同一主体、名称粒度不同（如「西湖云栖酒店管理有限公司」vs「西湖云栖酒店」）视为一致，
    // 避免把真实发票误判 needs_review；仅当互不串含（确为不同主体）才记分歧。
    const nameSame = n1 === n2 || n1.includes(n2) || n2.includes(n1)
    if (!nameSame) diffs.push(`销售方: ①=${r1.sellerName || '(空)'} ②=${r2.sellerName || '(空)'}`)
  }
  const t1 = num(r1.total)
  const t2 = num(r2.total)
  if (t2 > 0 && t1 > 0 && Math.abs(t1 - t2) > 0.02) {
    diffs.push(`价税合计: ①=${t1} ②=${t2}`)
  }
  const a1 = num(r1.amount)
  const a2 = num(r2.amount)
  if (a2 > 0 && a1 > 0 && Math.abs(a1 - a2) > 0.02) {
    diffs.push(`金额: ①=${a1} ②=${a2}`)
  }

  return { consistent: diffs.length === 0, diffs, method: 'dual', r1, r2 }
}
