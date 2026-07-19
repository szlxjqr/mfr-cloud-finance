// 发票文件解析工具：支持 OFD / PDF / PNG 三种格式的真实字段提取
// OFD: 本质是 ZIP 包，内部为 XML，直接解压并提取结构化字段
// PDF: 文本型 PDF 用 pdfjs 提取文字（需 cMap 才能正确解码数电票等 CID 字体）；
//      若文字过少（扫描件/字体无法解码）则回退渲染图片做 OCR
// PNG: 通过 tesseract.js 做中文 OCR，再从文字中匹配字段

import JSZip from 'jszip'
import * as pdfjsLib from 'pdfjs-dist'
// @ts-ignore - Vite 会将 worker 文件处理为 URL
import PdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

pdfjsLib.GlobalWorkerOptions.workerSrc = PdfWorker

// cMap / 标准字体：pdfjs 解码 CID 字体（数电票常见）必须，置于 public/ 下随构建发布
const CMAP_URL = '/cmaps/'
const CMAP_PACKED = true
const STANDARD_FONT_DATA_URL = '/standard_fonts/'

export interface ParsedInvoice {
  type?: string
  code?: string
  no?: string
  date?: string
  sellerName?: string
  sellerTaxNo?: string
  amount?: number
  tax?: number
  total?: number
  taxRate?: number
  item?: string
  account?: string
  rawText?: string
}

export interface ValidationResult {
  ok: boolean
  missing: string[]
  parsed: ParsedInvoice
}

function parseMoney(s: string): number {
  const cleaned = s.replace(/[¥￥\s,]/g, '')
  const n = Number(cleaned)
  return isNaN(n) ? 0 : n
}

// 把发票中「被拆开写」的标签归并成连续词，便于正则匹配
// （如「合 计」「销 售 方」「金 额」在提取文本里常带空格）
function normLabels(t: string): string {
  const map: [RegExp, string][] = [
    [/购\s*买\s*方/g, '购买方'],
    [/销\s*售\s*方/g, '销售方'],
    [/金\s*额/g, '金额'],
    [/税\s*额/g, '税额'],
    [/名\s*称/g, '名称'],
    [/合\s*计/g, '合计'],
    [/价\s*税\s*合\s*计/g, '价税合计'],
    [/小\s*写/g, '小写'],
    [/发\s*票\s*号\s*码/g, '发票号码'],
    [/开\s*票\s*人/g, '开票人'],
    [/纳\s*税\s*人\s*识\s*别\s*号/g, '纳税人识别号'],
    [/统\s*一\s*信\s*用\s*代\s*码/g, '统一社会信用代码'],
    [/税\s*率\s*\/\s*征\s*收\s*率/g, '税率/征收率'],
    [/不\s*含\s*税\s*金\s*额/g, '不含税金额'],
  ]
  for (const [re, rep] of map) t = t.replace(re, rep)
  return t
}

// 从任意文本中用正则提取发票常见字段
export function extractInvoiceFields(text: string): ParsedInvoice {
  const result: ParsedInvoice = { rawText: text }
  if (!text) return result
  const norm = normLabels(text)

  // 1. 发票号码 / 发票代码
  //    数电票：发票号码为 16-20 位纯数字，且无发票代码
  //    旧版票：发票号码 8-10 位、发票代码 10-12 位
  const digitRuns = [...norm.matchAll(/\d{8,20}/g)].map((m) => m[0])
  const longNo = digitRuns.find((r) => r.length >= 16 && r.length <= 20)
  if (longNo) {
    result.no = longNo
  } else {
    const codeCandidate = digitRuns.find((r) => r.length === 10 || r.length === 12)
    if (codeCandidate) result.code = codeCandidate
    const noCandidate = digitRuns.find(
      (r) => r.length >= 8 && r.length <= 10 && r !== codeCandidate,
    )
    result.no = noCandidate || (digitRuns.length ? digitRuns.sort((a, b) => b.length - a.length)[0] : result.no)
  }

  // 2. 开票日期：2026年07月03日 / 2026-07-03 / 20260703
  const dateMatch =
    norm.match(/(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日/) ||
    norm.match(/(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})/) ||
    norm.match(/(\d{4})(\d{2})(\d{2})/)
  if (dateMatch) {
    const y = dateMatch[1]
    const m = dateMatch[2].padStart(2, '0')
    const d = dateMatch[3].padStart(2, '0')
    if (Number(y) >= 2000 && Number(y) <= 2100 && Number(m) <= 12 && Number(d) <= 31) {
      result.date = `${y}-${m}-${d}`
    }
  }

  // 3. 销售方名称：收集所有公司名，取最后一个（发票中购买方在前、销售方在后）
  const compRe =
    /([\u4e00-\u9fa5A-Za-z0-9（）()·\-]{2,40}(?:科技有限公司|有限公司|有限责任公司|股份公司|集团))/g
  const comps = [...norm.matchAll(compRe)].map((m) => m[1].trim().replace(/\s+/g, ' '))
  if (comps.length) result.sellerName = comps[comps.length - 1]

  // 4. 纳税人识别号（统一社会信用代码 18 位）：取最后一个（销售方）
  //    边界断言避免误匹配长数字串（如 20 位发票号）的前 18 位
  const taxRuns = [...norm.matchAll(/(?<![0-9A-Z])[0-9A-Z]{18}(?![0-9A-Z])/g)].map((m) => m[0])
  if (taxRuns.length) result.sellerTaxNo = taxRuns[taxRuns.length - 1]

  // 5-7. 金额类：收集全部「¥xx.xx」金额，按大小分配
  //     发票中标签常与数值相距很远（甚至分处不同阅读区），故不依赖标签 proximity
  //     约定：最大=价税合计，次大=金额(不含税)，最小=税额
  const amounts = [...norm.matchAll(/(?:¥|￥)\s*([\d,]+\.\d{2})/g)].map((m) => parseMoney(m[1]))
  const uniqAmts = [...new Set(amounts)].sort((a, b) => b - a)
  if (uniqAmts.length) result.total = uniqAmts[0]
  if (uniqAmts.length > 1 && uniqAmts[1] < uniqAmts[0]) result.amount = uniqAmts[1]
  if (uniqAmts.length > 2 && uniqAmts[uniqAmts.length - 1] < uniqAmts[0])
    result.tax = uniqAmts[uniqAmts.length - 1]

  // 8. 税率（独立出现的 数字%）
  const rateMatch = norm.match(/(\d{1,2})\s*%/)
  if (rateMatch) result.taxRate = Number(rateMatch[1])

  // 9. 开票项目（*xxx* 形式）
  const itemMatch = norm.match(/\*\s*([\u4e00-\u9fa5A-Za-z0-9]+)\s*\*/)
  if (itemMatch) result.item = itemMatch[1]

  return result
}

// 校验识别结果：核心字段缺失则返回失败（发票代码在新版数电票中已取消，设为可选）
export function validateInvoice(p: ParsedInvoice): ValidationResult {
  const missing: string[] = []
  if (!p.no || !/^\d{8,20}$/.test(p.no)) missing.push('发票号码')
  if (!p.date) missing.push('开票日期')
  if (!p.sellerName || p.sellerName.length < 4) missing.push('销售方名称')
  if ((!p.total || p.total === 0) && (!p.amount || p.amount === 0)) missing.push('金额/价税合计')
  return { ok: missing.length === 0, missing, parsed: p }
}

// 判断提取文本是否过空（标签与值相隔极远或字体无法解码），决定是否需要 OCR 兜底
function looksEmpty(norm: string): boolean {
  const hasCompany = /(公司|酒店|企业|厂|店|中心|集团|税务局)/.test(norm)
  const hasLongDigit = /\d{8,}/.test(norm)
  const hasChinese = /[一-鿿]/.test(norm)
  return !hasCompany && !hasLongDigit && !hasChinese
}

// ===== OFD 解析 =====
export async function parseOfd(file: File): Promise<ParsedInvoice> {
  const buf = await file.arrayBuffer()
  const zip = await JSZip.loadAsync(buf)
  let text = ''
  const xmlFiles = Object.keys(zip.files).filter((n) => n.toLowerCase().endsWith('.xml'))
  for (const name of xmlFiles) {
    const content = await zip.files[name].async('string')
    const plain = content
      .replace(/<[^>]+>/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/\s+/g, ' ')
    text += plain + '\n'
  }
  const parsed = extractInvoiceFields(text)
  parsed.type = parsed.type || '电子发票'
  return parsed
}

// ===== PDF 文字提取 =====
async function extractPdfText(buf: ArrayBuffer): Promise<string> {
  const pdf = await pdfjsLib.getDocument({
    data: buf,
    cMapUrl: CMAP_URL,
    cMapPacked: CMAP_PACKED,
    standardFontDataUrl: STANDARD_FONT_DATA_URL,
  }).promise
  let text = ''
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i)
    const content = await page.getTextContent()
    const strings = content.items.map((it: any) => ('str' in it ? it.str : '')).join(' ')
    text += strings + '\n'
  }
  return text
}

// ===== PDF 渲染某一页为 canvas（用于 OCR 兜底）=====
async function renderPageToCanvas(
  pdf: any,
  pageIndex: number,
  scale = 2,
): Promise<HTMLCanvasElement> {
  const page = await pdf.getPage(pageIndex)
  const viewport = page.getViewport({ scale })
  const canvas = document.createElement('canvas')
  canvas.width = Math.ceil(viewport.width)
  canvas.height = Math.ceil(viewport.height)
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('无法创建画布上下文')
  await page.render({ canvasContext: ctx, viewport }).promise
  return canvas
}

// 使用 tesseract 识别图片/画布文字（PNG 与 PDF 兜底共用）
async function ocrToText(input: File | HTMLCanvasElement): Promise<string> {
  const Tesseract = await import('tesseract.js')
  const worker = await Tesseract.createWorker('chi_sim+eng', 1, {
    logger: () => {},
  })
  try {
    const { data } = await worker.recognize(input)
    return data.text || ''
  } finally {
    await worker.terminate()
  }
}

// ===== PDF 解析（文字优先，过空则 OCR 兜底）=====
export async function parsePdf(file: File): Promise<ParsedInvoice> {
  const buf = await file.arrayBuffer()
  const rawText = await extractPdfText(buf)
  const norm = normLabels(rawText)

  // 文字足够则直接用文字解析
  if (!looksEmpty(norm)) {
    const parsed = extractInvoiceFields(rawText)
    parsed.type = parsed.type || '增值税专用发票'
    return parsed
  }

  // 兜底：渲染各页做 OCR
  const pdf = await pdfjsLib.getDocument({
    data: buf,
    cMapUrl: CMAP_URL,
    cMapPacked: CMAP_PACKED,
    standardFontDataUrl: STANDARD_FONT_DATA_URL,
  }).promise
  let ocrText = ''
  for (let i = 1; i <= pdf.numPages; i++) {
    try {
      const canvas = await renderPageToCanvas(pdf, i)
      ocrText += (await ocrToText(canvas)) + '\n'
    } catch (e) {
      console.warn('PDF 第', i, '页渲染失败', e)
    }
  }
  const parsed = extractInvoiceFields(ocrText)
  parsed.type = parsed.type || '增值税专用发票'
  return parsed
}

// ===== PNG / JPG 解析（OCR）=====
export async function parsePng(file: File): Promise<ParsedInvoice> {
  const text = await ocrToText(file)
  const parsed = extractInvoiceFields(text)
  parsed.type = parsed.type || '增值税专用发票'
  return parsed
}

// 根据文件类型分发解析
export async function parseInvoiceFile(file: File): Promise<ParsedInvoice> {
  const name = file.name.toLowerCase()
  const isPdf = file.type === 'application/pdf' || name.endsWith('.pdf')
  const isOfd = name.endsWith('.ofd') || file.type === 'application/ofd'
  const isPng = file.type.startsWith('image/') || /\.(png|jpg|jpeg)$/.test(name)

  if (isOfd) return parseOfd(file)
  if (isPdf) return parsePdf(file)
  if (isPng) return parsePng(file)
  return parseOfd(file)
}
