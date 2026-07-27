// 发票字段提取（纯逻辑，无浏览器依赖）：从「任意发票文本」中识别结构化字段。
//
// 设计原则——「格式无关 / 宽松匹配」，不写任何票面特例：
// 1. 先版面归并：把被 pdfjs 按字形拆开的标签（如「销 售 方 信 息」）在 CJK 字符之间
//    去空格还原成「销售方信息」，但保留数字/字母间距（金额小数点不被吞）。
// 2. 购销方：优先抓「名称：」锚点（数电票/电子发票常把 购买方/销售方 前缀拆到别的行，
//    所以不依赖前缀，只看「名称：」出现的先后顺序 = 购买方 → 销售方）。
// 3. 明细行：以「*xxx*」为锚点，每条取「金额 税率% 税额」三元组（最后一组）为
//    （金额, 税额），税率取该组百分比；跳过单价超长小数与跨锚点泄漏。
// 4. 价税合计优先「价税合计」标签后首个 ¥ 数；账单类（去哪儿）用「实付金额」末列 ¥；
//    火车票/行程单无标签时取最大两位小数金额兜底。
// 5. 税号兼容 18 位(统一社会信用代码，含字母) 与 15 位(旧税号，纯数字)；顺序即 购→销。
// 6. 本企业恒为「深圳市流形机器人科技有限公司」（税号 91440300MAKF9C8P4U）：
//    文本含本名或本税号且未识别到购买方时，购买方补为本企业。
// 7. 火车票等无标签版式：含「12306」或「 D/G+车次」即销售方=中国铁路。
//
// 本文件刻意不 import pdfjs / jszip / tesseract / File / document，以便 Node 直接单测。

export interface ParsedLineItem {
  name: string
  qty?: number
  price?: number
  amount: number
  taxRate?: number
  tax: number
  total?: number
}

export interface InvoiceValidation {
  /** 公式核对是否通过（核心三数自洽） */
  passed: boolean
  /** 推导出的标准 VAT 税率（%），如 13 */
  rate?: number
  /** 原始推导税率（未吸附标准率），用于定位 leading-1 等异常 */
  derivedRate?: number
  /** 是否自动校正了 leading-1 等 OCR 脏值 */
  corrected: boolean
  /** 校正后最终值 */
  correctedAmount?: number
  correctedTotal?: number
  /** 校正前原始值（用于审计） */
  original?: { amount?: number; total?: number }
  /** 不通过时的简要说明 */
  message?: string
  /** 所有警告/提示 */
  warnings: string[]
}

export interface ParsedInvoice {
  type?: string
  code?: string
  no?: string
  date?: string
  buyerName?: string
  buyerTaxNo?: string
  sellerName?: string
  sellerTaxNo?: string
  amount?: number
  tax?: number
  total?: number
  taxRate?: number
  item?: string
  items?: ParsedLineItem[]
  account?: string
  rawText?: string
  // 双识别闸门结论（由 invoiceDual.dualRecognize 注入）：
  // consistent=false 时后端置 needs_review 隔离，不自动信任。
  recognition?: { consistent: boolean; diffs: string[]; method: string }
  // 公式核对结论（由 invoiceParser 注入）：权威判定，抓识别错误。
  validation?: InvoiceValidation
}

export interface ValidationResult {
  ok: boolean
  missing: string[]
  parsed: ParsedInvoice
}

/** @deprecated 改用 InvoiceValidation */
export interface VerifyResult {
  consistent: boolean
  warnings: string[]
}

const CJK = '一-鿿' // U+4E00–U+9FFF
// CJK 字符 + 常见符号（括号·连接符/【】），用于实体与标签字符类
const ENTCLASS = `[${CJK}（）()·\\-/【】]`
// 本企业（报销场景本企业恒为购买方）
const SELF_NAME = '深圳市流形机器人科技有限公司'
const SELF_TAXNO = '91440300MAKF9C8P4U'
// 企业名后缀锚点（仅取「终尾型」后缀，避免吞掉名称内部含 科技/贸易/信息 等词的公司）。
// 长后缀放前面，正则按序首匹配。
const SUFFIX =
  '股份有限公司|有限责任公司|有限公司|总公司|分公司|子公司|集团|酒店|旅行社|中心|局|厂|店|超市|商场|医院|学校|大学|银行|证券|保险|商行|商厦|企业|研究院|学院'
const round2 = (n: number) => Number(n.toFixed(2))

// 标准 VAT 税率（%）。推导税率时吸附到最近的标准率；
// 0% 用于免税/不征税；负数或超大值视为异常。
const STANDARD_VAT_RATES = [0, 1, 3, 6, 9, 13]

// 由税额/金额推导实际税率，并吸附到最近的标准 VAT 税率。
// 返回 { rate: 标准率, derived: 原始推导值 }。
// amount 必须 >0；tax>=0。容差内吸附，否则返回原始推导值。
function deriveTaxRate(amount: number, tax: number): { rate: number; derived: number } | null {
  if (!amount || amount <= 0) return null
  const derived = (tax / amount) * 100
  // 找最近标准率
  let best = STANDARD_VAT_RATES[0]
  let bestDiff = Math.abs(derived - best)
  for (const r of STANDARD_VAT_RATES.slice(1)) {
    const d = Math.abs(derived - r)
    if (d < bestDiff) {
      bestDiff = d
      best = r
    }
  }
  // 吸附容差：1 个百分点（如 12.5%→13%，13.5%→13%）
  const SNAP = 1.0
  if (bestDiff <= SNAP) return { rate: best, derived }
  return { rate: Math.round(derived * 100) / 100, derived }
}

// 尝试校正 OCR leading-1 脏值（金额/价税合计最高位多识别一个 1）。
// 思路：若当前 amount/total 导致推导税率偏离标准率，尝试把 amount/total 各减 10 的幂次（1000/10000…）
// 后重算；若某组合能恢复标准率且 amount+tax≈total，则采信。
function tryCorrectLeadingOne(
  amount: number,
  tax: number,
  total: number,
): { amount: number; total: number; rate: number; corrected: boolean } | null {
  if (!amount || amount <= 0 || !total || total <= 0) return null
  // 仅当推导税率明显异常才尝试校正
  const current = deriveTaxRate(amount, tax)
  if (!current) return null
  // 已经标准，无需校正
  if (STANDARD_VAT_RATES.includes(current.rate)) return null

  const candidates: Array<{ amount: number; total: number }> = []
  // 常见 leading-1 场景：千位、万位多了 1
  for (const base of [1000, 10000, 100000]) {
    if (amount > base) candidates.push({ amount: amount - base, total: total - base })
    if (amount > base * 10) candidates.push({ amount: amount - base * 10, total: total - base * 10 })
  }
  // 也尝试只减 amount 或只减 total（防不对称脏值）
  for (const base of [1000, 10000, 100000]) {
    if (amount > base) candidates.push({ amount: amount - base, total })
    if (total > base) candidates.push({ amount, total: total - base })
  }

  const TOLERANCE = 0.02
  for (const cand of candidates) {
    if (cand.amount <= 0 || cand.total <= 0) continue
    const derived = deriveTaxRate(cand.amount, tax)
    if (!derived) continue
    if (!STANDARD_VAT_RATES.includes(derived.rate)) continue
    const recomputed = round2(cand.amount + tax)
    if (Math.abs(recomputed - cand.total) > TOLERANCE && Math.abs(cand.total - round2(cand.amount * (1 + derived.rate / 100))) > TOLERANCE) {
      continue
    }
    return { amount: cand.amount, total: cand.total, rate: derived.rate, corrected: true }
  }
  return null
}

function parseMoney(s: string): number {
  const cleaned = s.replace(/[¥￥\s,]/g, '')
  const n = Number(cleaned)
  return isNaN(n) ? 0 : n
}

// 货币/金额字段永不超过 2 位小数；OCR 偶发把「单价」列识别成超长小数
// （如 698.2300884956），属噪声。任何 ≥4 位小数的数字统一四舍五入为 2 位，
// 既消除噪声、又不影响合法 1~3 位小数（数量 1.5 / 1.234kg）。
// 注意：本函数只清理文本，金额/价税合计提取仍由「恰好 2 位小数」的正则约束，
// 故 ≥4 位小数的脏值本就不会被当金额读取；此函数主要保证入库 parsed 数据干净。
export function normalizeMoneyDecimals(s: string): string {
  return s.replace(/(\d+\.\d{4,})/g, (_m: string, p1: string) => {
    const n = Number(p1)
    if (isNaN(n)) return p1
    return (Math.round(n * 100) / 100).toFixed(2)
  })
}

function cleanCompany(s: string): string {
  return s.trim().replace(/\s+/g, ' ')
}

// 把「被拆开写」的标签归并：仅去除 CJK 字符之间的空白，保留数字/字母间距。
// 例：「销 售 方 信 息」→「销售方信息」；「755.66 83.02」保持原样（小数点不被吞）。
function collapseCjk(t: string): string {
  const re = new RegExp(`(${ENTCLASS})\\s+(${ENTCLASS})`, 'g')
  let out = t
  for (let i = 0; i < 12; i++) {
    const next = out.replace(re, '$1$2')
    if (next === out) break
    out = next
  }
  return out
}

// 数电票文字层常把「每个字形」用单空格拆开（如「1 6 3 6 . 2 8」「购 买 方」），
// 导致数字/小数点被拆散，正则 \d+.\d{2} 抓不到。仅合并「每个字符都逐字空格分隔」的
// [\d.%] 连续串（即字形级拆开）：如 1 6 3 6 . 2 8 → 1636.28、发票号逐字空格 → 完整号码。
// 关键：要求 run 末尾之后是「空白/结尾」而非另一个数字（负向预查 (?<!\S)），
// 避免把「数量 1 + 金额 83.02」这类「单数字空格 + 连续数字」误拼成 183.02。
// 汉字、字母不碰，避免把模型号 G701 与税率 13% 黏连。
function depod(t: string): string {
  return t.replace(/(?<![\d.%A-Za-z])([\d.%](?: [\d.%])+)(?!\S)/g, (_m: string, run: string) => run.replace(/ /g, ''))
}

// 归一标签：剥掉夹在标签里的噪音（统一社会信用代码/纳税人识别号/信息），
// 并把「购买方信息/销售方信息」收敛成「购买方/销售方」，便于后续锚定。
function normLabels(t: string): string {
  let s = collapseCjk(t)
  const map: [RegExp, string][] = [
    // 先剥噪音（顺序在前，避免污染后续标签）
    [new RegExp(`统\\s*一\\s*信\\s*用\\s*代\\s*码\\s*\\/\\s*纳\\s*税\\s*人\\s*识\\s*别\\s*号`, 'g'), ''],
    [new RegExp(`统\\s*一\\s*信\\s*用\\s*代\\s*码`, 'g'), ''],
    [new RegExp(`纳\\s*税\\s*人\\s*识\\s*别\\s*号`, 'g'), ''],
    // 注意：不删除裸「信息」，否则会误删公司名内部的「信息技术」等词。
    // 标签前缀收敛
    [new RegExp(`购\\s*买\\s*方\\s*信\\s*息`, 'g'), '购买方'],
    [new RegExp(`购\\s*买\\s*方`, 'g'), '购买方'],
    [new RegExp(`购\\s*方`, 'g'), '购买方'],
    [new RegExp(`销\\s*售\\s*方\\s*信\\s*息`, 'g'), '销售方'],
    [new RegExp(`销\\s*售\\s*方`, 'g'), '销售方'],
    [new RegExp(`销\\s*方`, 'g'), '销售方'],
    [new RegExp(`卖\\s*方`, 'g'), '销售方'],
    [new RegExp(`购\\s*货\\s*单\\s*位`, 'g'), '购买方'],
    [new RegExp(`销\\s*货\\s*单\\s*位`, 'g'), '销售方'],
    // 其他常见标签归一（仅用于阅读友好，提取主要靠 名称：/价税合计 等）
    [new RegExp(`价\\s*税\\s*合\\s*计`, 'g'), '价税合计'],
    [new RegExp(`合\\s*计`, 'g'), '合计'],
    [new RegExp(`小\\s*写`, 'g'), '小写'],
    [new RegExp(`开\\s*票\\s*日\\s*期`, 'g'), '开票日期'],
    [new RegExp(`发\\s*票\\s*号\\s*码`, 'g'), '发票号码'],
    [new RegExp(`纳\\s*税\\s*人\\s*识\\s*别\\s*号`, 'g'), '纳税人识别号'],
    [new RegExp(`统\\s*一\\s*信\\s*用\\s*代\\s*码`, 'g'), '统一社会信用代码'],
    [new RegExp(`税\\s*率\\s*\\/\\s*征\\s*收\\s*率`, 'g'), '税率/征收率'],
    [new RegExp(`不\\s*含\\s*税\\s*金\\s*额`, 'g'), '不含税金额'],
    [new RegExp(`电\\s*子\\s*发\\s*票`, 'g'), '电子发票'],
  ]
  for (const [re, rep] of map) s = s.replace(re, rep)
  // 货币符号 artifact 归一（京东等 PDF 字体子集映射异常：价税合计行的 ¥ 被抽成 ´ U+00B4 锐音符 / ¤ U+00A4 通用货币符）。
  // 这类字符在中文发票文本中不会作为真实内容出现，归一为 ¥ 可同时修数电票分支与通用路径的同类漏抓。
  s = s.replace(/[´¤]/g, '¥')
  return s
}

// 抓取所有「名称：<实体>」锚点（顺序 = 购买方 → 销售方）。
// 后缀锚定（SUFFIX）避免吞掉名称内部的 科技/贸易/信息；并跳过「酒店/房型/项目…名称」等复合标签。
function extractNameAnchors(norm: string): string[] {
  const re = new RegExp(`名称\\s*[：:]\\s*(${ENTCLASS}{1,30}?(?:${SUFFIX}))`, 'g')
  const out: string[] = []
  let m: RegExpExecArray | null
  while ((m = re.exec(norm))) {
        const idx = m.index ?? 0
        const pre = norm.slice(Math.max(0, idx - 6), idx)
    // 跳过复合标签：酒店名称 / 房型名称 / 项目名称 / 费用名称 / 商品名称 / 服务名称
    if (/(酒店|房型|项目|费用|商品|服务)名称/.test(pre)) continue
    const name = cleanCompany(m[1])
    if (name.length >= 4) out.push(name)
  }
  return out
}

// 广义销售方兜底（无购销方标签时，如酒店账单 / 商户 / 平台）。
function extractSellerLabels(norm: string): string[] {
  const re = new RegExp(`(酒店名称|商户名称|平台名称|销售方|销货单位)\\s*[：:]\\s*(${ENTCLASS}{1,30}?(?:${SUFFIX}))`, 'g')
  const out: string[] = []
  let m: RegExpExecArray | null
  while ((m = re.exec(norm))) {
    const name = cleanCompany(m[2])
    if (name.length >= 4) out.push(name)
  }
  return out
}

// 广义实体兜底：乘客（TO:/乘客/乘机人）、任意中文实体串（排除已知关键字）。
function extractEntities(norm: string): { sellers: string[]; buyers: string[]; passengers: string[] } {
  const sellers: string[] = []
  const buyers: string[] = []
  const passengers: string[] = []

  // 乘客 / 客人（去哪儿账单 TO: 沈雷）
  const pRe = new RegExp(`(?:TO|乘客|客人|乘机人)\\s*[：:]\\s*([${CJK}A-Za-z·]{1,12})`, 'g')
  let m: RegExpExecArray | null
  while ((m = pRe.exec(norm))) passengers.push(cleanCompany(m[1]))

  // 任意「中文实体串」作为兜底销售方（后缀锚定 + 排除已知关键字）
  const genericRe = new RegExp(`(${ENTCLASS}{1,30}?(?:${SUFFIX}))`, 'g')
  const STOP = /(?:发票|金额|日期|税额|税率|合计|电话|订单号|开户|银行|账号|地址|备注|开票人|项目|消费|明细|客服|下载|次数|规格|单位|数量|单价|名称)/
  while ((m = genericRe.exec(norm))) {
    const w = cleanCompany(m[1])
    if (w.length < 4 || STOP.test(w)) continue
    sellers.push(w)
  }
  return { sellers: [...new Set(sellers)], buyers, passengers }
}

// 纳税人识别号 / 统一社会信用代码：
// 18 位(含字母) 或 15 位(纯数字)。按「连续字母数字区间」切分，正确处理两税号被标签
// 剥离后「无缝拼接」的情况（如 购买方税号紧跟 销售方税号：...P4U9144...）。
// 规则：区间长度恰为 18（或 15）→ 整段即一个税号；长度为 18/15 的整数倍(>1) → 等分成多个；
// 其余长度（如 19/20/22 位的发票号、车次号）一律跳过，避免把发票号当成税号。
function extractTaxNos(norm: string): string[] {
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
  const alnumRuns = [...norm.matchAll(/[0-9A-Z]+/g)].map((m) => m[0])
  splitRuns(alnumRuns, 18)
  if (out.length) return out
  const numRuns = [...norm.matchAll(/[0-9]+/g)].map((m) => m[0])
  splitRuns(numRuns, 15)
  return out
}

// 发票号码：标签锚定优先；其次取「18~22 位最长数字串」（数电票可为 19 位、且逐字空格分隔），
// 排除紧跟 "/" 的银行账号（数电票顺序中发票号在备注银行账号之前 → 取第一个）。
function extractInvoiceNo(norm: string, taxNos: string[]): string | undefined {
  const labelRe = /发票号码\s*[：:]?\s*([0-9]{8,22})/
  const lm = norm.match(labelRe)
  if (lm) return lm[1]
  const runs = [...norm.matchAll(/\d{18,22}/g)].map((x) => x[0])
  for (const r of runs) {
    const idx = norm.indexOf(r)
    const next = idx >= 0 && idx + r.length < norm.length ? norm[idx + r.length] : ''
    if (next !== '/' && !taxNos.some((t) => t.includes(r) || r.includes(t))) return r
  }
  return undefined
}

// 开票日期：年-月-日 / YYYY-MM-DD / YYYY MM DD / YYYYMMDD。
function extractDate(norm: string): string | undefined {
  const patterns = [
    /(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日/,
    /(\d{4})[-\/.](\d{1,2})[-\/.](\d{1,2})/,
    /(\d{4})\s+(\d{1,2})\s+(\d{1,2})/,
    /(\d{4})(\d{2})(\d{2})/,
  ]
  for (const p of patterns) {
    const m = norm.match(p)
    if (m) {
      const y = m[1]
      const mo = m[2].padStart(2, '0')
      const d = m[3].padStart(2, '0')
      if (Number(y) >= 2000 && Number(y) <= 2100 && Number(mo) <= 12 && Number(d) <= 31)
        return `${y}-${mo}-${d}`
    }
  }
  return undefined
}

// 价税合计：优先「价税合计」后首个 ¥ 数（大写夹在中间）；「合计（小写）」次之；
// 账单类（去哪儿）用「实付金额 / 票价」末列 ¥（贪婪，取到最后一个 ¥）。
function extractTotal(norm: string): number | undefined {
  let m = norm.match(/价税合计[\s\S]*?[¥￥]\s*([\d,]+\.\d{2})/)
  if (m) return parseMoney(m[1])
  m = norm.match(/合计\s*（小写）\s*[¥￥]?\s*([\d,]+\.\d{2})/)
  if (m) return parseMoney(m[1])
  m = norm.match(/(实付金额|票价)[\s\S]*[¥￥]\s*([\d,]+\.\d{2})/)
  if (m) return parseMoney(m[2])
  return undefined
}

function cleanItemName(s: string): string {
  return s
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/[【】]/g, '')
    .replace(/[*\s]/g, ' ')
    .replace(/名称[:：]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

// 明细行：以「*xxx*」为锚点切分每条，取该行「金额 税率% 税额」三元组（最后一组）
// 的（金额, 税额, 税率）；无三元组时退化为该行末两位两位小数。跳过单价超长小数泄漏。
// 扫描区截断到首个「合计 / 价税合计 / 小写」之前，避免单行锚点把 合计/价税合计 行的小数吞进本条。
export function extractLineItems(norm: string): ParsedLineItem[] {
  const items: ParsedLineItem[] = []
  const cut = norm.search(/合计|价税合计|小写/)
  const body = cut >= 0 ? norm.slice(0, cut) : norm
  const anchorRe = /\*([^*]+)\*/g
  const anchors = [...body.matchAll(anchorRe)].map((m) => ({ idx: m.index ?? 0, raw: m[0] }))
  if (anchors.length === 0) return items

  for (let i = 0; i < anchors.length; i++) {
    const start = anchors[i].idx
    const end = i + 1 < anchors.length ? anchors[i + 1].idx ?? body.length : body.length
    const seg = body.slice(start, end)
    const name = cleanItemName(anchors[i].raw)
    if (!name) continue

    // 主规则：金额 税率% 税额（取最后一组，规避跨锚点单价泄漏）
    const triples = [...seg.matchAll(/(-?[\d,]+\.\d{2})\s+(\d{1,2})\s*%\s+(-?[\d,]+\.\d{2})/g)]
    let amount: number | undefined
    let tax: number | undefined
    let rate: number | undefined
    if (triples.length) {
      const last = triples[triples.length - 1]
      amount = parseMoney(last[1])
      tax = parseMoney(last[3])
      rate = Number(last[2])
    } else {
      const decs = [...seg.matchAll(/-?[\d,]+\.\d{2}/g)].map((x) => parseMoney(x[0]))
      if (decs.length < 2) continue
      amount = decs[decs.length - 2]
      tax = decs[decs.length - 1]
      const rm = seg.match(/(\d{1,2})\s*%/)
      rate = rm ? Number(rm[1]) : undefined
    }
    items.push({ name, amount: round2(amount || 0), tax: round2(tax || 0), taxRate: rate })
  }
  return items
}

// 数电票明细行：「税率%[单位] 金额 税额」（如 13%个 883.12 114.80），可多行 → 多明细。
// 关联最近的「*名称*」锚点作为行项目名。返回按行拆分的 ParsedLineItem[]。
function extractEinvoiceItems(normE: string): ParsedLineItem[] {
  const eRe = /(\d{1,2})\s*%\s*[个块台套件张只]?\s+(\d+.\d{1,2})\s+(\d+.\d{1,2})/g
  const ms = [...normE.matchAll(eRe)]
  if (ms.length === 0) return []
  const anchors: { idx: number; name: string }[] = []
  const aRe = /\*([^*]+)\*/g
  let am: RegExpExecArray | null
  while ((am = aRe.exec(normE))) anchors.push({ idx: am.index ?? 0, name: cleanItemName(am[0]) })
  const items: ParsedLineItem[] = []
  for (const m of ms) {
    const rate = Number(m[1])
    const amount = parseMoney(m[2])
    const tax = parseMoney(m[3])
    let name = ''
    for (let i = anchors.length - 1; i >= 0; i--) {
      if (anchors[i].idx < (m.index ?? 0)) {
        name = anchors[i].name
        break
      }
    }
    items.push({ name: name || '*', amount: round2(amount), tax: round2(tax), taxRate: rate })
  }
  return items
}

/** 提取「合计」行数据（合计不含税金额、合计税额、价税合计）。
 *  京东等优惠发票有额外负号行，合计行为权威来源。
 *  返回 { summaryAmount, summaryTax, summaryTotal }，找不到时全部为 undefined。 */
function extractSummaryLine(norm: string): { summaryAmount?: number; summaryTax?: number; summaryTotal?: number } {
  // 找「合计」或「小计」标签后的数字区域
  const m = norm.match(/[合小]计[\s\S]{0,80}?(-?[\d,]+\.\d{2})\s+(-?[\d,]+\.\d{2})(?:\s+(-?[\d,]+\.\d{2}))?/)
  if (!m) return {}
  const r: { summaryAmount?: number; summaryTax?: number; summaryTotal?: number } = {}
  r.summaryAmount = parseMoney(m[1])
  r.summaryTax = parseMoney(m[2])
  if (m[3] !== undefined) r.summaryTotal = parseMoney(m[3])
  return r
}

// 开票项目（*xxx* 形式，取首个）。
function extractItem(norm: string): string | undefined {
  const m = norm.match(/\*\s*([一-鿿A-Za-z0-9]+)\s*\*/)
  if (m) return m[1]
  return undefined
}


// 数电票购销方：税号提取最稳，名称取「各自税号紧前」的 CJK 后缀实体；
// 布局重排（标签挤页眉、名称甩页中）或与日期黏连时仍稳。前置日期残留（年/月/日/数字/空白）一并剥除。
function extractEinvoiceParties(norm: string, taxNos: string[]): { buyer?: string; seller?: string } {
  const lastEntityBefore = (taxNo: string): string | undefined => {
    const idx = norm.indexOf(taxNo)
    if (idx < 0) return undefined
    // 税号前 80 字符窗口（兼容名称与税号跨行）；去尾部空白/换行后从末尾回扫名称字符，
    // 遇 数字/字母（税号/银行账号/型号残留）即止。
    const win = norm.slice(Math.max(0, idx - 80), idx).replace(/\s+$/, '')
    let s = ''
    for (let i = win.length - 1; i >= 0; i--) {
      const ch = win[i]
      if (/[0-9A-Za-z]/.test(ch)) break
      s = ch + s
      if (s.length > 40) break
    }
    // 去除前置日期残留（年/月/日/数字/空白/标点）
    const cleaned = s.replace(/^[0-9年月光日时分秒.\/\-（）()\s]+/, '')
    const name = cleanCompany(cleaned)
    return name.length >= 4 ? name : undefined
  }
  const out: { buyer?: string; seller?: string } = {}
  if (taxNos.length >= 1) {
    const b = lastEntityBefore(taxNos[0])
    if (b) out.buyer = b
  }
  if (taxNos.length >= 2) {
    const s2 = lastEntityBefore(taxNos[1])
    if (s2) out.seller = s2
  }
  return out
}
export function extractInvoiceFields(text: string): ParsedInvoice {
  const result: ParsedInvoice = { rawText: text }
  if (!text) return result
  const norm = normLabels(normalizeMoneyDecimals(depod(text)))
  // 数电票专用副本：不跑 normalizeMoneyDecimals（避免把粘连小数 22.5486 误圆成 22.55，
  // 破坏「税率%[单位] 金额 税额」中税额的精确 2 位提取）。
  const normE = normLabels(depod(text))

  // 1. 发票号码
  const taxNos = extractTaxNos(norm)
  const no = extractInvoiceNo(norm, taxNos)
  if (no) result.no = no

  // 2. 开票日期
  const date = extractDate(norm)
  if (date) result.date = date

  // 3. 购销方：名称锚点顺序优先；其次标签 / 广义实体 / 本企业兜底
  const names = extractNameAnchors(norm)
  const sellerLabels = extractSellerLabels(norm)
  const entities = extractEntities(norm)

  let buyerName: string | undefined
  let sellerName: string | undefined
  if (names.length >= 1) {
    buyerName = names[0]
    sellerName = names[1] || sellerLabels[0] || entities.sellers[0]
  } else {
    sellerName = sellerLabels[0] || entities.sellers[0]
    if (entities.passengers.length) buyerName = entities.passengers[0]
  }

  const selfHere = norm.replace(/\s/g, '').includes(SELF_NAME)
  const selfTaxHere = taxNos.includes(SELF_TAXNO)
  if (!buyerName) {
    if (selfHere || selfTaxHere) buyerName = SELF_NAME
  }
  if (!sellerName) {
    if (/12306|[\s(（]?[DG]\d{2,4}[\s)）]/.test(norm)) sellerName = '中国铁路'
    else if (entities.sellers.length) sellerName = entities.sellers[0]
  }

  // 4. 纳税人识别号：顺序即 购买方 → 销售方
  if (taxNos.length) {
    result.buyerTaxNo = taxNos[0]
    result.sellerTaxNo = taxNos[taxNos.length - 1]
  }

  // —— 数电票（电子发票/增值税专用发票，detail 行以「税率%[单位] 金额 税额」呈现）——
  // 关键金额在「¥ 金额 ¥ 税额」与「价税合计（大写） ¥ 总额」两处，且逐字空格拆开。
  // 走专用分支：避免被通用逻辑的「合计」截断、顺序错配、或 normalizeMoneyDecimals 破坏粘连小数。
  // 判定放宽（仅服务京东这一种新格式，不误伤已有 fixture）：
  //  · 原条件：税率带单位字（%[个块台套件张只]）→ 阿里/海利士/宝之谷/极途/拓骏成。
  //  · 新增：京东电子发票「裸税率%」（税额黏税率、无单位字，如 76.1613%）+ ¥金额¥税额 对。
  //    用「\d+\.\d{2}\d{1,2}%」锚定「税额.xx 直接黏 税率yy%」（无空格），避免把普通「金额 空格 税率%」(如 323.06 6%) 误拽进分支。
  if (
    /%\s*[个块台套件张只]/.test(normE) ||
    (/电子发票|增值税专用发票/.test(normE) && /\d+\.\d{2}\d{1,2}%/.test(normE) && /[¥￥]\s*[\d,]+\.\d{2}\s*[¥￥]/.test(normE))
  ) {
    const pair = normE.match(/[¥￥]\s*([\d,]+\.\d{2})\s*[¥￥]\s*([\d,]+\.\d{2})/)
    if (pair) {
      result.amount = round2(parseMoney(pair[1]))
      result.tax = round2(parseMoney(pair[2]))
    }
    // 价税合计：取「价税合计（大写）…」之后【最后一个】¥ 数（总额恒在末位）
    const totM = normE.match(/价税合计[\s\S]*[¥￥]\s*([\d,]+\.\d{2})(?![\s\S]*[¥￥])/)
    if (totM) result.total = round2(parseMoney(totM[1]))
    else {
      const all = [...normE.matchAll(/[¥￥]\s*([\d,]+\.\d{2})/g)].map((x) => parseMoney(x[1]))
      if (all.length) result.total = round2(all[all.length - 1])
    }
    // 税率：明细「%个」优先；否则由 税额/金额 反推吸附标准 VAT
    const rateM = normE.match(/(\d{1,2})\s*%\s*[个块台套件张只]?/)
    let rate: number | undefined
    if (rateM) rate = Number(rateM[1])
    if (rate === undefined || !STANDARD_VAT_RATES.includes(rate)) {
      const dr = deriveTaxRate(result.amount || 0, result.tax ?? 0)
      if (dr) rate = dr.rate
    }
    if (rate !== undefined) result.taxRate = rate
    // 明细行（invoice_details 粒度）：逐行「%个 金额 税额」；多行为多明细。
    const items = extractEinvoiceItems(normE)
    result.items = items.length
      ? items
      : result.amount
        ? [{ name: '*', amount: result.amount, tax: result.tax ?? 0, taxRate: rate }]
        : []
    // 购销方：税号紧前反查（布局重排/名称与日期黏连仍稳），失败再退回通用逻辑
    // 仅在能区分购买方/销售方两个税号时才用数电票专用反查覆盖
    // （避免京东个人票仅 1 个销售方税号时把销售方误当购买方）。
    if (taxNos.length >= 2) {
      const parties = extractEinvoiceParties(normE, taxNos)
      result.buyerName = parties.buyer ?? buyerName
      result.sellerName = parties.seller ?? sellerName
    }
    const item = extractItem(normE)
    if (item) result.item = item
    return result
  }

  // 5. 明细行 + 价税合计
  const items = extractLineItems(norm)
  result.items = items
  if (items.length > 0) {
    // 金额/税额：恒取「所有明细行求和」。
    // 数电票多明细行（如 RGB摄像头 + 自动回充套件）按行取首两小数再求和，
    // 比依赖可能误读的「合计」行更稳；京东等负号明细由明细行本身承载。
    const itemAmount = round2(items.reduce((s, it) => s + it.amount, 0))
    const itemTax = round2(items.reduce((s, it) => s + it.tax, 0))
    result.amount = itemAmount
    result.tax = itemTax

    const sl = extractSummaryLine(norm)
    // 价税合计：优先「价税合计」标签后 ¥ 数（extractTotal），其次合计行，再其次推算
    const total = extractTotal(norm)
    if (total !== undefined) {
      result.total = total
    } else if (sl.summaryTotal !== undefined) {
      result.total = sl.summaryTotal
    } else {
      result.total = round2(itemAmount + itemTax)
    }
    // 税率：明细一致取之；否则由 税额/金额 反推吸附标准 VAT（更稳，规避逐字空格导致的脏 % 字符）
    const rates = [...new Set(items.map((it) => it.taxRate).filter((r) => r !== undefined))] as number[]
    if (rates.length === 1) result.taxRate = rates[0]
    if (result.taxRate === undefined) {
      const dr = deriveTaxRate(result.amount, result.tax)
      if (dr) result.taxRate = dr.rate
    }
  } else {
    const total = extractTotal(norm)
    if (total !== undefined) {
      result.total = total
    } else {
      // 无标签/无明细（火车票等）：取最大两位小数金额，其次合理整数
      const decs = [...norm.matchAll(/[\d,]+\.\d{2}/g)].map((x) => parseMoney(x[0]))
      const validDecs = decs.filter((d) => d > 0 && d < 1e7)
      if (validDecs.length) result.total = Math.max(...validDecs)
      else {
        const ints = [...norm.matchAll(/(?<![\d])\d{1,5}(?![\d])/g)].map((x) => Number(x[0]))
        const cand = ints.filter((n) => n > 0 && n <= 10000)
        if (cand.length) result.total = Math.max(...cand)
      }
    }
  }

  // 6. 税率（独立出现，仅当明细未给出时）
  if (result.taxRate === undefined) {
    const rateMatch = norm.match(/(\d{1,2})\s*%/)
    if (rateMatch) result.taxRate = Number(rateMatch[1])
  }

  // 7. 开票项目
  const item = extractItem(norm)
  if (item) result.item = item

  result.buyerName = buyerName
  result.sellerName = sellerName
  return result
}

// 校验识别结果：只检查核心四字段（发票号/金额/税额/价税合计）。
// 非核心字段（日期/购销方/明细名/单价/数量）缺失不影响「可入库」判定。
export function validateInvoice(p: ParsedInvoice): ValidationResult {
  const missing: string[] = []
  if (!p.no || !/^\d{8,20}$/.test(p.no)) missing.push('发票号码')
  if (!p.amount || p.amount <= 0) missing.push('合计金额')
  if (p.tax === undefined || p.tax === null || p.tax < 0) missing.push('合计税额')
  if (!p.total || p.total <= 0) missing.push('价税合计')
  return { ok: missing.length === 0, missing, parsed: p }
}

// 公式核对：权威判定，抓识别错误。
// 1. 税率由 税额/金额 推导并吸附标准 VAT 税率；
// 2. 校验 amount+tax≈total（容差 0.02 元）且 total/(1+rate)≈amount；
// 3. 若推导税率异常，尝试 leading-1 自动校正；
// 4. 返回 InvoiceValidation，供 parser 写入 parsed.validation 并作为入库闸门。
export function verifyInvoice(p: ParsedInvoice): InvoiceValidation {
  const warnings: string[] = []
  let amount = p.amount || 0
  let tax = p.tax ?? 0
  let total = p.total || 0
  let corrected = false
  let original: { amount?: number; total?: number } | undefined

  // 核心三数必须都识别到且为正（税额可为 0）
  if (amount <= 0 || total <= 0) {
    return { passed: false, corrected: false, message: '金额或价税合计未识别', warnings: ['金额、税额、价税合计必须全部识别'] }
  }

  const TOLERANCE = 0.02

  // 第一步：推导税率
  let rateInfo = deriveTaxRate(amount, tax)
  if (!rateInfo) {
    return { passed: false, corrected: false, message: '无法推导税率（金额无效）', warnings }
  }

  // 第二步：若税率异常，尝试 leading-1 校正
  if (!STANDARD_VAT_RATES.includes(rateInfo.rate)) {
    const fixed = tryCorrectLeadingOne(amount, tax, total)
    if (fixed) {
      original = { amount, total }
      amount = fixed.amount
      total = fixed.total
      corrected = true
      rateInfo = { rate: fixed.rate, derived: fixed.rate }
      warnings.push(`已自动校正 leading-1 脏值：金额 ${original.amount}→${amount}，价税合计 ${original.total}→${total}`)
    }
  }

  // 第三步：公式核对
  const sumCheck = round2(amount + tax)
  const divideCheck = round2(total / (1 + rateInfo.rate / 100))
  let passed = true
  if (Math.abs(sumCheck - total) > TOLERANCE) {
    passed = false
    warnings.push(`价税合计 ${total} 与 金额${amount}+税额${tax}=${sumCheck} 不一致`)
  }
  if (Math.abs(divideCheck - amount) > TOLERANCE) {
    passed = false
    warnings.push(`价税合计 ${total}/(1+${rateInfo.rate}%)≈${divideCheck} 与 金额${amount} 不一致`)
  }

  // 税额为负直接不通过
  if (tax < 0) {
    passed = false
    warnings.push('税额不能为负数')
  }

  return {
    passed,
    rate: rateInfo.rate,
    derivedRate: rateInfo.derived,
    corrected,
    correctedAmount: corrected ? amount : undefined,
    correctedTotal: corrected ? total : undefined,
    original: corrected ? original : undefined,
    message: passed ? undefined : (warnings[0] || '核心三数不自洽'),
    warnings,
  }
}
