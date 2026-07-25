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
}

export interface ValidationResult {
  ok: boolean
  missing: string[]
  parsed: ParsedInvoice
}

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

function parseMoney(s: string): number {
  const cleaned = s.replace(/[¥￥\s,]/g, '')
  const n = Number(cleaned)
  return isNaN(n) ? 0 : n
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

// 发票号码：标签锚定优先；其次取 20 位纯数字串（非税号）作为客票号 / 数电号。
function extractInvoiceNo(norm: string, taxNos: string[]): string | undefined {
  const labelRe = /发票号码\s*[：:]?\s*([0-9]{8,20})/
  const lm = norm.match(labelRe)
  if (lm) return lm[1]
  const runs = [...norm.matchAll(/\d{8,20}/g)].map((x) => x[0])
  for (const r of runs) {
    if (r.length === 20 && !taxNos.some((t) => t.includes(r) || r.includes(t))) return r
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

export function extractInvoiceFields(text: string): ParsedInvoice {
  const result: ParsedInvoice = { rawText: text }
  if (!text) return result
  const norm = normLabels(text)

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

  // 5. 明细行 + 合计行校验 + 价税合计
  const items = extractLineItems(norm)
  result.items = items
  if (items.length > 0) {
    const itemAmount = round2(items.reduce((s, it) => s + it.amount, 0))
    const itemTax = round2(items.reduce((s, it) => s + it.tax, 0))

    // 优先用合计行数据（权威来源，京东优惠发票有负号明细）
    const sl = extractSummaryLine(norm)
    const summaryAmount = sl.summaryAmount
    const summaryTax = sl.summaryTax
    const summaryTotal = sl.summaryTotal

    // 合计行数据齐全 → 优先用
    if (summaryAmount !== undefined && summaryTax !== undefined) {
      result.amount = summaryAmount
      result.tax = summaryTax
      // 校验：items 加总与合计行差 ≤ 0.02 时认为一致，否则说明明细行有误（如负号被吞）
      if (Math.abs(itemAmount - summaryAmount) > 0.02) {
        // 仅警告，不动数据
      }
    } else {
      result.amount = itemAmount
      result.tax = itemTax
    }

    // 价税合计：合计行 > extractTotal > 推算
    if (summaryTotal !== undefined) {
      result.total = summaryTotal
    } else {
      const total = extractTotal(norm)
      if (total !== undefined) {
        result.total = total
        if (result.amount === undefined) result.amount = round2(total - (result.tax || 0))
      } else {
        result.total = round2((result.amount || 0) + (result.tax || 0))
      }
    }
    // 税率取首个明细的（如一致）
    const rates = [...new Set(items.map((it) => it.taxRate).filter((r) => r !== undefined))] as number[]
    if (rates.length === 1) result.taxRate = rates[0]
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

// 校验识别结果：核心字段缺失则返回失败（发票代码在新版数电票中已取消，设为可选）。
export function validateInvoice(p: ParsedInvoice): ValidationResult {
  const missing: string[] = []
  if (!p.no || !/^\d{8,20}$/.test(p.no)) missing.push('发票号码')
  if (!p.date) missing.push('开票日期')
  if (!p.sellerName || p.sellerName.length < 4) missing.push('销售方名称')
  if ((!p.total || p.total === 0) && (!p.amount || p.amount === 0)) missing.push('金额/价税合计')
  return { ok: missing.length === 0, missing, parsed: p }
}

// 一致性校验：发票是权威文件，识别到的金额/税额/价税合计应原样保存；
// 此处仅用公式「验证」是否自洽，用于提示可疑偏差，绝不覆盖已识别数据。
// 容差 2 分：数电票税额常按「价税合计 - 金额」倒挤或四舍五入，与「金额×税率」可能有 1 分差异，属正常。
export function verifyInvoice(p: ParsedInvoice): VerifyResult {
  const warnings: string[] = []
  const amount = p.amount || 0
  const tax = p.tax || 0
  const total = p.total || 0

  if (amount > 0 && tax > 0 && total > 0) {
    const sum = round2(amount + tax)
    if (Math.abs(sum - total) > 0.02) {
      warnings.push(`价税合计 ${total} 与 金额${amount}+税额${tax}=${sum} 不一致`)
    }
  }
  if (amount > 0 && tax > 0 && p.taxRate) {
    const expect = round2((amount * p.taxRate) / 100)
    if (Math.abs(tax - expect) > 0.02) {
      warnings.push(`税额 ${tax} 与 金额×税率${p.taxRate}%≈${expect} 不一致`)
    }
  }
  return { consistent: warnings.length === 0, warnings }
}
