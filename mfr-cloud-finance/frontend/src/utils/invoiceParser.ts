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

// 从任意文本中用正则提取发票常见字段
export function extractInvoiceFields(text: string): ParsedInvoice {
  const result: ParsedInvoice = { rawText: text }
  if (!text) return result

  // 发票代码：10 或 12 位
  const codeMatch = text.match(/(?:发票代码|代码)[^\d]{0,6}(\d{10,12})/)
  if (codeMatch) result.code = codeMatch[1]

  // 发票号码：8 或 20 位
  const noMatch = text.match(/(?:发票号码|号码)[^\d]{0,6}(\d{8,20})/)
  if (noMatch) result.no = noMatch[1]

  // 开票日期：2026年05月18日 / 2026-05-18
  const dateMatch =
    text.match(/(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日/) ||
    text.match(/(\d{4})[-/](\d{1,2})[-/](\d{1,2})/)
  if (dateMatch) {
    const y = dateMatch[1]
    const m = dateMatch[2].padStart(2, '0')
    const d = dateMatch[3].padStart(2, '0')
    result.date = `${y}-${m}-${d}`
  }

  // 销售方名称
  const sellerMatch = text.match(/(?:销售方|销方|名称)[(（:：]?\s*([\u4e00-\u9fa5A-Za-z0-9（）()&.·\-]{2,40}公司|[\u4e00-\u9fa5A-Za-z0-9（）()&.·\-]{2,40}厂|[\u4e00-\u9fa5A-Za-z0-9（）()&.·\-]{2,40}店)/)
  if (sellerMatch) result.sellerName = sellerMatch[1].trim()

  // 纳税人识别号（统一社会信用代码 18 位）
  const taxNoMatch = text.match(/(?:纳税人识别号|识别号|税号)[^\w]{0,4}([0-9A-Z]{18})/)
  if (taxNoMatch) result.sellerTaxNo = taxNoMatch[1]

  // 金额 / 税额 / 价税合计
  const amountMatch = text.match(/(?:金额|不含税|金额合计)[^\d]{0,8}[:：]?\s*([¥￥]?\s*[\d,]+\.?\d*)/)
  if (amountMatch) result.amount = parseMoney(amountMatch[1])

  const taxMatch = text.match(/(?:税额)[^\d]{0,8}[:：]?\s*([¥￥]?\s*[\d,]+\.?\d*)/)
  if (taxMatch) result.tax = parseMoney(taxMatch[1])

  const totalMatch =
    text.match(/(?:价税合计|合计)[^\d]{0,8}[:：]?\s*([¥￥]?\s*[\d,]+\.?\d*)/) ||
    text.match(/(?:大写|小写)[^\d]{0,8}([¥￥]\s*[\d,]+\.?\d*)/)
  if (totalMatch) result.total = parseMoney(totalMatch[1])

  // 税率
  const rateMatch = text.match(/(?:税率|征收率)[^\d]{0,6}(\d{1,2})\s*%/)
  if (rateMatch) result.taxRate = Number(rateMatch[1])

  return result
}

function parseMoney(s: string): number {
  const cleaned = s.replace(/[¥￥\s,]/g, '')
  const n = Number(cleaned)
  return isNaN(n) ? 0 : n
}

// ===== OFD 解析 =====
export async function parseOfd(file: File): Promise<ParsedInvoice> {
  const buf = await file.arrayBuffer()
  const zip = await JSZip.loadAsync(buf)
  let text = ''
  // 遍历所有 XML 文件，收集文本节点内容
  const xmlFiles = Object.keys(zip.files).filter((n) => n.toLowerCase().endsWith('.xml'))
  for (const name of xmlFiles) {
    const content = await zip.files[name].async('string')
    // 去除标签，保留文本
    const plain = content
      .replace(/<[^>]+>/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/\s+/g, ' ')
    text += plain + '\n'
  }
  const parsed = extractInvoiceFields(text)
  // OFD 电子发票通常为增值税专用发票或电子发票
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
  // 动态导入 tesseract.js，避免无 PNG 场景也加载
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
  // 兜底：OFD 尝试
  return parseOfd(file)
}
