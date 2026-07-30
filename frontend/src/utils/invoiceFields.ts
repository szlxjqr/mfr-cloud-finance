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
  /** 非增值税金额（如机票行程单的民航发展基金），不计入价税合计 / 税额，仅作报销附加费展示 */
  nonTaxAmount?: number
  /** 电子客票号码（行程单专用，区别于 20 位发票号码） */
  ticketNo?: string
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
  /** 彻底拒绝入库（非 needs_review 可人工放行）：如购买方为个人姓名。 */
  reject?: boolean
  rejectReason?: string
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

// 判断「购买方」是否为自然人姓名（而非企业）。用于入库拦截：个人消费的发票不能报销入库。
// 规则：含企业后缀（SUFFIX）→ 企业；纯中文 2-4 字且无后缀 → 自然人；其余（含字母/数字/≥5字/本名）→ 非个人。
function isPersonalName(name?: string): boolean {
  if (!name) return false
  const n = name.replace(/\s+/g, '')
  if (!n) return false
  if (n === SELF_NAME) return false
  if (new RegExp(`(?:${SUFFIX})$`).test(n)) return false
  if (/^[一-鿿]{2,4}$/.test(n)) return true
  return false
}

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

// OCR 偶发把「50.00」拆成「50. 00」；只合并恰好 2 位小数被空格拆开的情况。
function fixMoneySpaces(s: string): string {
  return s.replace(/(\d+)\.\s*(\d{2})(?!\d)/g, '$1.$2')
}

function cleanCompany(s: string): string {
  // 剥除企业名前残留的「年/月/日/：」等日期/标点前缀（数电票分块排版常见）。
  return s
    .trim()
    .replace(/\s+/g, ' ')
    .replace(/^[\s:：年月日\-/]+/, '')
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
function extractEntities(norm: string, rawText?: string): { sellers: string[]; buyers: string[]; passengers: string[] } {
  const sellers: string[] = []
  const buyers: string[] = []
  const passengers: string[] = []

  // 乘客 / 客人（去哪儿账单 TO: 沈雷）。必须在**未 collapseCjk 的原始文本**上匹配，
  // 否则「沈雷\n感谢您...」会被 collapse 成「沈雷感谢您...」，导致乘客名被拉长污染。
  const pSrc = rawText || norm
  const pRe = new RegExp(`(?:TO|乘客|客人|乘机人)\\s*[：:]\\s*([${CJK}A-Za-z·]{1,12})(?=$|\\s|[^${CJK}A-Za-z·])`, 'g')
  let m: RegExpExecArray | null
  while ((m = pRe.exec(pSrc))) passengers.push(cleanCompany(m[1]))

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

// 发票号码 OCR「前导 1」脏值校正：数电票 / 行程单的 20 位发票号被多识别一个前导 1 → 21 位，
// 会触发 validateInvoice 的「发票号码缺失」误判（其正则 ^\d{8,20}$ 上限为 20）。
// 合法发票号码恒为 8~20 位；恰好 21 位且以 '1' 开头几乎必为前导 1 脏值，剥离即可还原。
// （仅处理「长度本身已非法」的 21 位场景，避免对合法 20 位号误删首位。）
function correctInvoiceNoLeadingOne(no?: string): { value: string; corrected: boolean } {
  if (!no) return { value: '', corrected: false }
  if (/^1\d{20}$/.test(no)) return { value: no.slice(1), corrected: true }
  return { value: no, corrected: false }
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

// 价税合计：优先「价税合计」标签后的**最后一个** ¥ 金额（大写在前、小写在后，
// 中间可能夹杂脏金额如 ¥276.42 ¥16.58）；「合计（小写）」次之；
// 账单类（去哪儿）用「实付金额 / 票价」末列 ¥（贪婪，取到最后一个 ¥）。
function extractTotal(norm: string): number | undefined {
  // 改「最后一个 prefix-¥」：河源等发票大写后先出现合计金额/税额，最后才是小写价税合计。
  // 用 negative lookbehind 排除 suffix-¥（如 558.80¥ 33.53¥）被误当 prefix-¥。
  let m = norm.match(/价税合计[\s\S]*(?<![\d.])[¥￥]\s*([\d,]+\.\d{2})(?![\s\S]*(?<![\d.])[¥￥])/)
  if (m) return parseMoney(m[1])
  m = norm.match(/合计\s*（小写）\s*[¥￥]?\s*([\d,]+\.\d{2})/)
  if (m) return parseMoney(m[1])
  m = norm.match(/(实付金额|票价)[\s\S]*(?<![\d.])[¥￥]\s*([\d,]+\.\d{2})/)
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
  // 数电票分块排版时，合计金额/税额可能出现在「合计」标签之后 200+ 字符处（如杭州酒店：
  // 先出现备注+明细行，最后才是 323.06 19.38）。放宽窗口到 500 字符。
  let textAfter = norm.match(/[合小]计([\s\S]{0,500})/)?.[1] || ''
  // 同一行内的「金额 税额」对才认，避免跨行把「342.44\n323.06」黏成一对、把真正的 323.06/19.38 拆散。
  // 同时去掉 ¥/￥ 符号，让「¥827.86 ¥107.63」也能成对提取。
  textAfter = textAfter.replace(/[¥￥]/g, ' ')
  const pairs = [...textAfter.matchAll(/(-?[\d,]+\.\d{2})[^\S\n\r]+(-?[\d,]+\.\d{2})(?![\d])/g)]
  // 优先选「金额+税额」推导税率能吸附到标准 VAT 率的组合（过滤掉 323.06 323.06 这类脏对）。
  for (const m of pairs) {
    const a = parseMoney(m[1])
    const t = parseMoney(m[2])
    const dr = deriveTaxRate(a, t)
    if (dr && STANDARD_VAT_RATES.includes(dr.rate)) {
      return { summaryAmount: a, summaryTax: t }
    }
  }
  // 回退：第一对数字
  if (pairs.length) {
    return { summaryAmount: parseMoney(pairs[0][1]), summaryTax: parseMoney(pairs[0][2]) }
  }
  return {}
}

// 开票项目（*xxx* 形式，取首个）。
function extractItem(norm: string): string | undefined {
  const m = norm.match(/\*\s*([一-鿿A-Za-z0-9]+)\s*\*/)
  if (m) return m[1]
  return undefined
}


// 数电票购销方：税号提取最稳，名称取「各自税号紧前」的 CJK 后缀实体；
// 布局重排（标签挤页眉、名称甩页中）或与日期黏连时仍稳。前置日期残留（年/月/日/数字/空白）一并剥除。
function extractEinvoiceParties(norm: string): { buyer?: string; seller?: string } {
  // 数电票文字层被 pdf.js 重排后，购销方名称可能落在税号之前或之后，且可能被日期/人名污染
  // （如「2026年07月03日王大成深圳市流形机器人科技有限公司杭州呈华酒店管理有限公司」）。
  // 策略：1) 贪婪提取最长 CJK+SUFFIX 串；2) 超长且含多个后缀的长串按后缀拆成子候选；
  //    子候选若包含本企业名，取本企业名子串；3) 去重后按出现顺序分配（购买方在前、销售方在后）。
  const suffixRe = new RegExp(`(?:${SUFFIX})$`)
  const companyRe = new RegExp(`(${ENTCLASS}{2,}(?:${SUFFIX}))`, 'g')
  // 拆分脏拼接长串时只用「有限公司」类核心后缀，避免把「XX分公司」等分支后缀误拆成独立公司。
  const coreSuffix = '股份有限公司|有限责任公司|有限公司'
  const suffixSplitRe = new RegExp(`(${coreSuffix})`, 'g')
  const companies: { name: string; idx: number }[] = []
  let m: RegExpExecArray | null
  while ((m = companyRe.exec(norm)) !== null) {
    const raw = cleanCompany(m[1])
    if (raw.length < 4) continue
    const suffixCount = [...raw.matchAll(suffixSplitRe)].length
    // 含多个核心后缀（如「A有限公司B有限公司」）几乎一定是脏拼接，优先拆分再合并。
    let parts: string[] =
      suffixCount > 1
        ? (() => {
            const outParts: string[] = []
            let last = 0
            let sm: RegExpExecArray | null
            while ((sm = suffixSplitRe.exec(raw)) !== null) {
              outParts.push(raw.slice(last, sm.index + sm[0].length))
              last = sm.index + sm[0].length
            }
            return outParts
          })()
        : [raw]
    // 合并被误拆的相邻部分（如「杭州呈华酒店」+「管理有限公司」）
    const merged: string[] = []
    for (let i = 0; i < parts.length; i++) {
      const cur = parts[i]
      const next = parts[i + 1]
      if (next && !/公司$/.test(cur) && /公司$/.test(cur + next)) {
        merged.push(cur + next)
        i++
      } else {
        merged.push(cur)
      }
    }
    parts = merged
    for (const part of parts) {
      let name = cleanCompany(part)
      if (name.length < 4) continue
      const selfPos = name.indexOf(SELF_NAME)
      if (selfPos > 0) name = SELF_NAME
      if (name === SELF_NAME || suffixRe.test(name)) {
        companies.push({ name, idx: m.index })
      }
    }
  }
  // 本企业名兜底（可能不符合通用后缀规则，但 SELF_NAME 已知）
  let selfIdx = norm.indexOf(SELF_NAME)
  while (selfIdx >= 0) {
    if (!companies.some((c) => c.idx === selfIdx)) {
      companies.push({ name: SELF_NAME, idx: selfIdx })
    }
    selfIdx = norm.indexOf(SELF_NAME, selfIdx + 1)
  }
  // 去重（同名保留首次）
  const seen = new Set<string>()
  const unique = companies.filter((c) => {
    if (seen.has(c.name)) return false
    seen.add(c.name)
    return true
  })

  // 过滤掉税务局/发票监制章等政府机关名，避免其因出现位置早而被错当成销售方。
  const isGov = (n: string) => /税务|发票|监制|国家/.test(n)
  const out: { buyer?: string; seller?: string } = {}
  if (unique.length >= 2) {
    // 报销场景：本企业恒为购买方；无本企业时再按标签顺序推断。
    const selfIdx = unique.findIndex((c) => c.name === SELF_NAME)
    if (selfIdx >= 0) {
      // 优先取非政府机关的另一方（如酒店公司），避免把「XX税务局」当销售方。
      const otherCandidates = unique.filter((_, i) => i !== selfIdx && !isGov(_.name))
      const otherIdx = otherCandidates.length
        ? unique.findIndex((c) => c.name === otherCandidates[0].name)
        : (selfIdx === 0 ? 1 : 0)
      out.buyer = unique[selfIdx].name
      out.seller = unique[otherIdx].name
  } else {
    // 非本企业报销场景：购销方均排除税务局/发票监制章等政府机关名。
    const nonGov = unique.filter((c) => !isGov(c.name))
    const buyerLabelIdx = norm.indexOf('购买方')
    const sellerLabelIdx = norm.indexOf('销售方')
    if (nonGov.length >= 2) {
      if (sellerLabelIdx >= 0 && buyerLabelIdx >= 0 && sellerLabelIdx < buyerLabelIdx) {
        out.buyer = nonGov[1].name
        out.seller = nonGov[0].name
      } else {
        out.buyer = nonGov[0].name
        out.seller = nonGov[1].name
      }
    } else if (nonGov.length === 1) {
      out.seller = nonGov[0].name
    }
  }
  } else if (unique.length === 1) {
    if (unique[0].name === SELF_NAME) out.buyer = SELF_NAME
    else if (!isGov(unique[0].name)) out.seller = unique[0].name
  }
  return out
}
export function extractInvoiceFields(text: string): ParsedInvoice {
  const result: ParsedInvoice = { rawText: text }
  if (!text) return result
  const norm = normLabels(normalizeMoneyDecimals(fixMoneySpaces(depod(text))))
  // 数电票专用副本：不跑 normalizeMoneyDecimals（避免把粘连小数 22.5486 误圆成 22.55，
  // 破坏「税率%[单位] 金额 税额」中税额的精确 2 位提取）。
  const normE = normLabels(fixMoneySpaces(depod(text)))

  // 1. 发票号码（含 OCR 前导 1 校正：21 位→20 位）
  const taxNos = extractTaxNos(norm)
  const rawNo = extractInvoiceNo(norm, taxNos)
  const noFix = correctInvoiceNoLeadingOne(rawNo)
  if (noFix.value) result.no = noFix.value

  // 2. 开票日期
  const date = extractDate(norm)
  if (date) result.date = date

  // 3. 购销方：名称锚点顺序优先；其次标签 / 广义实体 / 本企业兜底
  const names = extractNameAnchors(norm)
  const sellerLabels = extractSellerLabels(norm)
  const entities = extractEntities(norm, text)

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

  // 4b. 两税号场景：用「税号紧前窗口」反查购销方名，修复标签/值分块排版的电子发票
  // （如去哪儿酒店专票把销售方/购买方值块排在税号之前，通用实体兜底会抓错）。
  // 过滤：只接受以企业后缀结尾或为本企业的名称，防止把标签文字（统一社会信用代码/：）当名称。
  const suffixRe = new RegExp(`(?:${SUFFIX})$`)
  const isValidParty = (n?: string) =>
    !!n && (n === SELF_NAME || suffixRe.test(n))
  if (taxNos.length >= 2) {
    const parties = extractEinvoiceParties(normE)
    if (isValidParty(parties.buyer)) buyerName = parties.buyer
    if (isValidParty(parties.seller)) sellerName = parties.seller
  }

  // —— 航空运输电子客票行程单（航司 / 代理开票，含民航发展基金）——
  // 结构特殊：票面「合计」含【非增值税】的民航发展基金，真正的价税合计 = 票价 + 燃油附加费 + 增值税税额。
  // 字段对齐（已与老板确认）：票价、燃油附加费均为不含税；增值税税额独立；民航发展基金为非税附加费。
  // 计算：amount = 票价 + 燃油附加费；tax = 增值税税额；total = amount + tax（= 价税合计，不含基金）。
  // 民航发展基金 + 其他税费记入 nonTaxAmount，不进 VAT 公式，仅作报销附加费。
  // OCR 场景下标签可能全丢，只剩「CNY 688.07 CNY 137.61 CNY 50.00 CNY 0.00 CNY 950.00」这种金额列，
  // 此时按列序推断：最后一个是票面合计（含基金），前面若干列按「应税金额 / 非税附加费」组合，用 9% 税率反推校验。
  const isAviation =
    (/电子客票行程单|航空运输电子客票|行程单|客票号码|电子客票/.test(norm) &&
      (/填开单位|票价|民航|燃油|其他税费|购买方名称/.test(norm) ||
        /(?:CNY|¥|￥)\s*[\d,]+\.\d{2}/.test(norm))) ||
    // OCR 噪声场景：标题关键字可能错字/丢失，但「客票号码 + 填开单位 + 金额」足够判定为行程单。
    (/客票号码|电子客票/.test(norm) && /填开单位/.test(norm) && /(?:CNY|¥|￥)/.test(norm))
  if (isAviation) {
    const moneyAfter = (re: RegExp, def?: number): number | undefined => {
      const m = norm.match(re)
      return m ? parseMoney(m[1]) : def
    }

    // 1) 标签法：票面文字层干净时直接用。
    const fareLbl = moneyAfter(/票价[\s¥￥CNYcny]*([\d,]+\.\d{2})/)
    const fuelLbl = moneyAfter(/燃油附加费[\s¥￥CNYcny]*([\d,]+\.\d{2})/)
    const taxLbl = moneyAfter(/增值税税额[\s¥￥CNYcny]*([\d,]+\.\d{2})/)
    const fundLbl = moneyAfter(/民航发展基金[\s¥￥CNYcny]*([\d,]+\.\d{2})/, 0)
    const otherLbl = moneyAfter(/其他税费[\s¥￥CNYcny]*([\d,]+\.\d{2})/, 0)

    // 2) 金额列推断（OCR 标签丢失时）：连续金额列，最后一个是票面合计。
    //    行程单列序一般为：票价 燃油附加费 [民航发展基金] [其他税费] 合计。
    //    把末尾 0~2 个小金额当 nonTax，其余当应税金额，用标准 VAT 率反推税额。
    const allAmounts = [...norm.matchAll(/[¥￥CNYcny]\s*([\d,]+\.\d{2})/g)].map((m) =>
      parseMoney(m[1]),
    )
    type Layout = { amount: number; tax: number; total: number; nonTax: number; taxRate: number }
    const inferByAmounts = (): Layout | null => {
      if (allAmounts.length < 4) return null
      const totalPaid = allAmounts[allAmounts.length - 1]
      const tryNonTax = (nonTaxCount: number): Layout | null => {
        const taxableCount = allAmounts.length - 1 - nonTaxCount
        if (taxableCount < 1) return null
        const nonTaxItems = allAmounts.slice(taxableCount, allAmounts.length - 1)
        const taxableItems = allAmounts.slice(0, taxableCount)
        const nonTax = round2(nonTaxItems.reduce((a, b) => a + b, 0))
        const amount = round2(taxableItems.reduce((a, b) => a + b, 0))
        const tax = round2(totalPaid - amount - nonTax)
        const dr = deriveTaxRate(amount, tax)
        if (!dr) return null
        // 行程单只可能是 9%（机票）；13% 留给极少数货运/其他应税服务兜底。
        if (![9, 13].includes(dr.rate)) return null
        // 推导值与标准率偏差应在 2 个百分点内
        if (Math.abs(dr.derived - dr.rate) > 2) return null
        return { amount, tax, total: round2(amount + tax), nonTax, taxRate: dr.rate }
      }
      // 优先尝试末尾 2 项为 nonTax（常见：基金+其他税费），再 1 项，最后 0 项
      for (const c of [2, 1, 0]) {
        const layout = tryNonTax(c)
        if (layout) return layout
      }
      return null
    }
    // OCR 严重退化时只剩「票价/合计」两列（甚至只有 3 个金额），无法分离基金/燃油；
    // 此时直接按 9% 由 total 倒推 amount+tax，保证 total/tax 可用（基金 breakdown 放弃）。
    const inferFromTotalOnly = (): Layout | null => {
      if (allAmounts.length < 2) return null
      const totalPaid = allAmounts[allAmounts.length - 1]
      if (totalPaid <= 0) return null
      const RATE = 9
      const amount = round2(totalPaid / (1 + RATE / 100))
      const tax = round2(totalPaid - amount)
      if (amount <= 0 || tax < 0) return null
      return { amount, tax, total: totalPaid, nonTax: 0, taxRate: RATE }
    }

    const ticketNo = (norm.match(/电子客票号码[\s：:]*([0-9]{10,20})/) || [])[1] ||
                     (norm.match(/客票号码[\s：:]*([0-9]{10,20})/) || [])[1]
    const rateM = norm.match(/增值税税率\s*(\d{1,2})\s*%/)
    const explicitRate = rateM ? Number(rateM[1]) : undefined

    let amount = 0
    let tax = 0
    let total = 0
    let nonTax = 0
    let taxRate: number | undefined = explicitRate

    if (fareLbl && fuelLbl && taxLbl) {
      amount = round2(fareLbl + fuelLbl)
      tax = round2(taxLbl)
      total = round2(amount + tax)
      nonTax = round2((fundLbl || 0) + (otherLbl || 0))
    } else {
      const layout = inferByAmounts() || inferFromTotalOnly()
      if (layout) {
        amount = layout.amount
        tax = layout.tax
        total = layout.total
        nonTax = layout.nonTax
        taxRate = taxRate ?? layout.taxRate
      }
    }

    if (amount > 0 && total > 0) {
      result.amount = amount
      result.tax = tax
      result.total = total
      result.taxRate =
        taxRate !== undefined ? taxRate : (deriveTaxRate(amount, tax)?.rate ?? undefined)
      result.type = '航空运输电子客票行程单'
      if (nonTax > 0) result.nonTaxAmount = nonTax
      if (ticketNo) result.ticketNo = ticketNo
      // 行程单没有 20 位发票号码，以电子客票号码作为唯一识别码通过校验。
      if (ticketNo && !result.no) result.no = ticketNo
      // 销售方：优先「填开单位」，其次排除本企业的实体；行程单不含销售方税号
      const issuer = (norm.match(new RegExp(`填开单位[\\s：:]*(${ENTCLASS}{2,30}?(?:${SUFFIX}))`)) || [])[1]
      if (issuer) result.sellerName = cleanCompany(issuer)
      else if (!sellerName && entities.sellers.length) {
        const s = entities.sellers.find((x) => x !== SELF_NAME && !x.includes('流形'))
        if (s) result.sellerName = s
      } else if (sellerName) result.sellerName = sellerName
      // 购买方：航空行程单取真实「购买方名称」栏（公司抬头），旅客姓名归 passenger，不污染购买方字段。
      // 避免把自然人旅客误判为购买方触发拦截；票面无购买方名称时留空（不取旅客姓名）。
      const buyerLabel = (norm.match(/购买方名称[\s：:]*([一-鿿（）()·\-\/]{2,30}?(?:${SUFFIX}))/) || [])[1]
      let realBuyer: string | undefined
      if (buyerLabel) realBuyer = cleanCompany(buyerLabel)
      else if (selfHere || selfTaxHere) realBuyer = SELF_NAME
      result.buyerName = realBuyer
      result.sellerTaxNo = undefined
      result.items = [{ name: '*', amount, tax, taxRate: result.taxRate }]
      return result
    }
    // 金额未能识别全 → 降级走通用逻辑兜底
  }

  // —— 数电票（电子发票/增值税专用发票，detail 行以「税率%[单位] 金额 税额」呈现）——
  //  · 原条件：税率带单位字（%[个块台套件张只]）→ 阿里/海利士/宝之谷/极途/拓骏成。
  //  · 新增：京东电子发票「裸税率%」（税额黏税率、无单位字，如 76.1613%）+ ¥金额¥税额 对。
  //    用「\d+\.\d{2}\d{1,2}%」锚定「税额.xx 直接黏 税率yy%」（无空格），避免把普通「金额 空格 税率%」(如 323.06 6%) 误拽进分支。
  const isEinvoiceWithUnit = /%\s*[个块台套件张只]/.test(normE)
  const isJdEinvoice =
    /电子发票|增值税专用发票/.test(normE) &&
    /\d+\.\d{2}\d{1,2}%/.test(normE) &&
    /[¥￥]\s*[\d,]+\.\d{2}\s*[¥￥]/.test(normE)
  // 标签/值分块排版：明细行呈现为「金额 税额 税率%」或「金额 税率% 税额」（无 ¥ 前缀、无单位字），如杭州/河源酒店专票。
  const isLooseEinvoice =
    /电子发票|增值税专用发票/.test(normE) &&
    (
      /([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+\d{1,2}%/.test(normE) || // 金额 税额 税率%
      /([\d,]+\.\d{2})\s+\d{1,2}\s*%\s+[\d,]+\.\d{2}/.test(normE) // 金额 税率% 税额
    )
  if (isEinvoiceWithUnit || isJdEinvoice || isLooseEinvoice) {
    // 金额/税额：优先「合计」行（最权威）；其次 ¥金额¥税额 对；最后才尝试明细行三元组。
    // 杭州等 OCR 把税率脏成「19.386%」，明细三元组会抓错；合计行 323.06 19.38 始终可靠。
    const sl = extractSummaryLine(normE)
    if (sl.summaryAmount !== undefined && sl.summaryTax !== undefined) {
      const dr = deriveTaxRate(sl.summaryAmount, sl.summaryTax)
      if (dr && STANDARD_VAT_RATES.includes(dr.rate)) {
        result.amount = sl.summaryAmount
        result.tax = sl.summaryTax
      }
    }

    if (result.amount === undefined) {
      const pair = normE.match(/[¥￥]\s*([\d,]+\.\d{2})\s*[¥￥]\s*([\d,]+\.\d{2})/)
      if (pair) {
        result.amount = round2(parseMoney(pair[1]))
        result.tax = round2(parseMoney(pair[2]))
      } else {
        // 宽松 A：金额 税额 税率%（税率前紧邻的两个 2 位小数）
        const loose = normE.match(/([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+(\d{1,2})\s*%/)
        if (loose) {
          result.amount = round2(parseMoney(loose[1]))
          result.tax = round2(parseMoney(loose[2]))
        }
        // 宽松 B：金额 税率% 税额（河源等分块排版）
        if (result.amount === undefined) {
          const loose2 = normE.match(/([\d,]+\.\d{2})\s+(\d{1,2})\s*%\s+([\d,]+\.\d{2})/)
          if (loose2) {
            result.amount = round2(parseMoney(loose2[1]))
            result.tax = round2(parseMoney(loose2[3]))
          }
        }
      }
    }
    // 价税合计：优先「价税合计…」之后最后一个 prefix-¥ 金额（suffix-¥ 如 558.80¥ 不算）。
    const totM = normE.match(/价税合计[\s\S]*(?<![\d.])[¥￥]\s*([\d,]+\.\d{2})(?![\s\S]*(?<![\d.])[¥￥])/)
    if (totM) result.total = round2(parseMoney(totM[1]))
    else {
      // 只取真正的 prefix-¥（¥ 前不是数字/小数点），避免「558.80¥ 33.53」把 suffix ¥ 当 prefix 抓到 33.53。
      const all = [...normE.matchAll(/(?<![\d.])[¥￥]\s*([\d,]+\.\d{2})/g)].map((x) => parseMoney(x[1]))
      if (all.length) result.total = round2(all[all.length - 1])
      else {
        const allBare = [...normE.matchAll(/([\d,]+\.\d{2})/g)].map((x) => parseMoney(x[1]))
        if (allBare.length) result.total = round2(Math.max(...allBare))
      }
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
      const parties = extractEinvoiceParties(normE)
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
    // 明细被截断或排在合计之后时（河源/杭州等分块排版），从「合计」行取金额/税额。
    const sl = extractSummaryLine(norm)
    if (sl.summaryAmount !== undefined && sl.summaryTax !== undefined) {
      result.amount = sl.summaryAmount
      result.tax = sl.summaryTax
    }

    const total = extractTotal(norm)
    if (total !== undefined) {
      result.total = total
    } else if (sl.summaryTotal !== undefined) {
      result.total = sl.summaryTotal
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

    // 税率：由合计行金额/税额反推吸附标准 VAT
    if (result.taxRate === undefined && result.amount && result.tax !== undefined) {
      const dr = deriveTaxRate(result.amount, result.tax)
      if (dr) result.taxRate = dr.rate
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

  // 火车票 / 铁路电子客票（无标签版式，含 12306 / 中国铁路 / D·G+车次）：
  //  · 票面仅印「票价 = 总价(含税)」，不印单独税额；铁路增值税率 9%，
  //    按 total/(1+9%) 倒算 金额/税额，使 amount+tax≈total 自洽、公式闸门通过（方案A）。
  //  · 销售方恒为「中国铁路」；票面「XX税务局」是开票机关、非销售方，须压过通用实体兜底。
  //  · 火车票不印销售方税号，清掉「单税号落 taxNos[last]」误带成的买方税号。
  if (/12306|中国铁路|[\s(（]?[DG]\d{2,4}[\s)）]/.test(norm)) {
    if (sellerName !== '中国铁路') sellerName = '中国铁路'
    result.sellerTaxNo = undefined
    if (result.total && (!result.amount || result.amount <= 0)) {
      const RATE = 9
      const amount = round2(result.total / (1 + RATE / 100))
      const tax = round2(result.total - amount)
      result.amount = amount
      result.tax = tax
      result.taxRate = RATE
      if (!result.type) result.type = '铁路电子客票'
      if (!result.items || !result.items.length) {
        result.items = [{ name: '*', amount, tax, taxRate: RATE }]
      }
    }
  }

  // 非发票类票据兜底：消费明细 / 酒店账单 / 订单详情 / 平台账单等。
  // 这类 PDF 无发票号码、无价税结构，但报销需要「销售方 + 总金额」。
  const hasInvoiceMarker = /电子发票|增值税专用发票|普通发票|发票号码|统一社会信用代码|纳税人识别号/.test(norm)
  const hasReceiptMarker = /消费明细|酒店账单|订单详情|平台账单|账单/.test(norm)
  if (!hasInvoiceMarker && hasReceiptMarker && result.total && !result.amount) {
    const total = result.total
    result.amount = total
    result.tax = 0
    result.taxRate = 0
    result.type = '其他票据'
    // 销售方优先用已提取的「酒店名称」标签，避免自定义正则跨行吞入日期。
    const receiptSeller = sellerLabels[0] || norm.match(/酒店名称\s*[：:]\s*([^\n]{2,40})/)?.[1]
    if (receiptSeller) sellerName = cleanCompany(receiptSeller)
    // 购买方：乘客/入住人优先，无则兜底本企业。
    if (entities.passengers.length) buyerName = entities.passengers[0]
    else if (selfHere || selfTaxHere) buyerName = SELF_NAME
  }

  result.buyerName = buyerName
  result.sellerName = sellerName
  return result
}

// 是否为非发票类票据（消费明细 / 酒店账单 / 平台账单等）。
function isReceipt(p: ParsedInvoice): boolean {
  const norm = (p.rawText || '').replace(/\s/g, '')
  const hasInvoiceMarker = /电子发票|增值税专用发票|普通发票|发票号码|统一社会信用代码|纳税人识别号/.test(norm)
  const hasReceiptMarker = /消费明细|酒店账单|订单详情|平台账单|账单|实付金额|酒店名称/.test(norm)
  return !hasInvoiceMarker && hasReceiptMarker
}

// 校验识别结果：只检查核心四字段（发票号/金额/税额/价税合计）。
// 非核心字段（日期/购销方/明细名/单价/数量）缺失不影响「可入库」判定。
// 非发票类票据（消费明细/酒店账单等）无发票号码，校验放宽为只核金额/税额/价税合计。
export function validateInvoice(p: ParsedInvoice): ValidationResult {
  const missing: string[] = []
  const receipt = isReceipt(p)
  // OCR 前导 1 脏值：21 位（20 位真号 + 前导 1）先剥离再校验，避免误判「发票号码缺失」。
  const chkNo = correctInvoiceNoLeadingOne(p.no).value
  if (!receipt && (!chkNo || !/^\d{8,20}$/.test(chkNo))) missing.push('发票号码')
  if (!p.amount || p.amount <= 0) missing.push('合计金额')
  if (p.tax === undefined || p.tax === null || p.tax < 0) missing.push('合计税额')
  if (!p.total || p.total <= 0) missing.push('价税合计')
  // 入库拦截：仅对「发票」类凭证（类型含「发票」：增值税专用发票/普通发票/电子发票/数电票等）
  // 做个人购买方拦截——购买方为自然人姓名（非企业）的不能报销入库。
  // 火车票、机票行程单、酒店/订单账单（其他票据）及未识别类型一律豁免，
  // 避免把旅客/入住人姓名误判为个人购买方（老板要求：飞机要看清楚字段，旅客≠购买方）。
  const isInvoiceType = !!p.type && p.type.includes('发票')
  const personal = isInvoiceType && isPersonalName(p.buyerName)
  if (personal) missing.push('购买方为个人姓名，不能入库')
  return {
    ok: missing.length === 0,
    missing,
    parsed: p,
    reject: personal,
    rejectReason: personal ? '购买方为个人姓名，不能入库' : undefined,
  }
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
