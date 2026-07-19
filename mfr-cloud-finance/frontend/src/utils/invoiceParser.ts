// 发票文件解析工具：支持 OFD / PDF / PNG 三种格式的真实字段提取
// OFD: 本质是 ZIP 包，内部为 XML，直接解压并提取结构化字段
// PDF: 文本型 PDF 直接提取文字，扫描型退回预览
// PNG: 通过 tesseract.js 做中文 OCR，再从文字中匹配字段

import JSZip from 'jszip'
import * as pdfjsLib from 'pdfjs-dist'
// @ts-ignore - Vite 会将 worker 文件处理为 URL
import PdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

pdfjsLib.GlobalWorkerOptions.workerSrc = PdfWorker

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

const CODE_RE = /(?:发票代码|代码|电子发票代码|发票代码|电子发票代码)[^\d]{0,10}(\d{10,12})/
const NO_RE = /(?:发票号码|号码|电子发票号码|发票号码|电子发票号码|发票号码|No[.．]?)[^\d]{0,10}(\d{8,20})/i

function parseMoney(s: string): number {
  const cleaned = s.replace(/[¥￥\s,]/g, '')
  const n = Number(cleaned)
  return isNaN(n) ? 0 : n
}

// 从任意文本中用正则提取发票常见字段
export function extractInvoiceFields(text: string): ParsedInvoice {
  const result: ParsedInvoice = { rawText: text }
  if (!text) return result

  // 1. 发票代码（有标签优先）
  const codeMatch = text.match(CODE_RE)
  if (codeMatch) {
    result.code = codeMatch[1]
  } else {
    // 无标签时，按 10/12 位数字推断
    const fallback = text.match(/\b(\d{12})\b/) || text.match(/\b(\d{10})\b/)
    if (fallback) result.code = fallback[1]
  }

  // 2. 发票号码（有标签优先）
  const noMatch = text.match(NO_RE)
  if (noMatch) {
    result.no = noMatch[1]
  } else {
    // 无标签时，按 8/20 位数字推断
    const fallback = text.match(/\b(\d{20})\b/) || text.match(/\b(\d{8})\b/)
    if (fallback) result.no = fallback[1]
  }

  // 3. 开票日期：2026年05月18日 / 2026-05-18 / 2026/05/18 / 20260518
  const dateMatch =
    text.match(/(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日/) ||
    text.match(/(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})/) ||
    text.match(/(\d{4})(\d{2})(\d{2})/)
  if (dateMatch) {
    const y = dateMatch[1]
    const m = dateMatch[2].padStart(2, '0')
    const d = dateMatch[3].padStart(2, '0')
    // 简单校验
    if (Number(y) >= 2000 && Number(y) <= 2100 && Number(m) <= 12 && Number(d) <= 31) {
      result.date = `${y}-${m}-${d}`
    }
  }

  // 4. 销售方名称
  // 优先匹配 "销售方" 附近的公司名，或 "名称：" 后的公司名
  const sellerPatterns = [
    /(?:销售方|销方|卖方|销售者)[^\n]{0,60}(?:名称|全称)[:：\s]*([\u4e00-\u9fa5A-Za-z0-9（）()&.·\-\s]{2,80}公司)/,
    /(?:销售方|销方|卖方|销售者)[:：\s]*([\u4e00-\u9fa5A-Za-z0-9（）()&.·\-\s]{2,80}公司)/,
    /(?:名\s*称)[:：\s]*([\u4e00-\u9fa5A-Za-z0-9（）()&.·\-\s]{2,80}公司)/,
    /([\u4e00-\u9fa5A-Za-z0-9（）()&.·\-\s]{4,80}有限公司)/,
    /([\u4e00-\u9fa5A-Za-z0-9（）()&.·\-\s]{4,80}公司)/,
  ]
  for (const p of sellerPatterns) {
    const m = text.match(p)
    if (m) {
      result.sellerName = m[1].trim().replace(/\s+/g, ' ')
      break
    }
  }

  // 5. 纳税人识别号（统一社会信用代码 18 位）
  const taxNoMatch = text.match(/(?:纳税人识别号|识别号|税号|统一社会信用代码)[:：\s]*([0-9A-Z]{18})/)
  if (taxNoMatch) result.sellerTaxNo = taxNoMatch[1]

  // 6. 金额 / 税额 / 价税合计
  const amountMatch = text.match(/(?:不含税金额|金额合计|合计金额|金额)[:：\s]*([¥￥]?\s*[\d,]+\.\d{2})/)
  if (amountMatch) result.amount = parseMoney(amountMatch[1])

  const taxMatch = text.match(/(?:税额)[:：\s]*([¥￥]?\s*[\d,]+\.\d{2})/)
  if (taxMatch) result.tax = parseMoney(taxMatch[1])

  const totalMatch =
    text.match(/(?:价税合计|小写)[:：\s]*([¥￥]?\s*[\d,]+\.\d{2})/) ||
    text.match(/(?:价税合计|合\s*计)[\s\S]{0,40}?(?:[¥￥])?\s*([\d,]+\.\d{2})/)
  if (totalMatch) result.total = parseMoney(totalMatch[1])

  // 7. 税率
  const rateMatch = text.match(/(?:税率|征收率)[:：\s]*(\d{1,2})\s*%/)
  if (rateMatch) result.taxRate = Number(rateMatch[1])

  return result
}

// 校验识别结果：核心字段缺失则返回失败
export function validateInvoice(p: ParsedInvoice): ValidationResult {
  const missing: string[] = []
  if (!p.code || !/^\d{10,12}$/.test(p.code)) missing.push('发票代码')
  if (!p.no || !/^\d{8,20}$/.test(p.no)) missing.push('发票号码')
  if (!p.date) missing.push('开票日期')
  if (!p.sellerName || p.sellerName.length < 4) missing.push('销售方名称')
  if ((!p.total || p.total === 0) && (!p.amount || p.amount === 0)) missing.push('金额/价税合计')
  return { ok: missing.length === 0, missing, parsed: p }
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

// ===== PDF 解析 =====
export async function parsePdf(file: File): Promise<{ parsed: ParsedInvoice; text: string }> {
  const buf = await file.arrayBuffer()
  const pdf = await pdfjsLib.getDocument({ data: buf }).promise
  let text = ''
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i)
    const content = await page.getTextContent()
    const strings = content.items.map((it: any) => ('str' in it ? it.str : '')).join(' ')
    text += strings + '\n'
  }
  const parsed = extractInvoiceFields(text)
  parsed.type = parsed.type || '增值税专用发票'
  return { parsed, text }
}

// ===== PNG 解析（OCR）=====
export async function parsePng(file: File): Promise<ParsedInvoice> {
  const Tesseract = await import('tesseract.js')
  const worker = await Tesseract.createWorker('chi_sim+eng', 1, {
    logger: () => {},
  })
  try {
    const { data } = await worker.recognize(file)
    const text = data.text || ''
    const parsed = extractInvoiceFields(text)
    parsed.type = parsed.type || '增值税专用发票'
    return parsed
  } finally {
    await worker.terminate()
  }
}

// 根据文件类型分发解析
export async function parseInvoiceFile(file: File): Promise<ParsedInvoice> {
  const name = file.name.toLowerCase()
  const isPdf = file.type === 'application/pdf' || name.endsWith('.pdf')
  const isOfd = name.endsWith('.ofd') || file.type === 'application/ofd'
  const isPng = file.type.startsWith('image/') || /\.(png|jpg|jpeg)$/.test(name)

  if (isOfd) return parseOfd(file)
  if (isPdf) return (await parsePdf(file)).parsed
  if (isPng) return parsePng(file)
  return parseOfd(file)
}
