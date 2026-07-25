// 发票文件解析工具：支持 OFD / PDF / PNG 三种格式的真实字段提取。
// OFD: 本质是 ZIP 包，内部为 XML，直接解压并提取结构化字段。
// PDF: 文本型 PDF 用 pdfjs 提取文字（需 cMap 才能正确解码数电票等 CID 字体）；
//      若文字过少（扫描件/字体无法解码）则回退渲染图片做 OCR。
// PNG: 通过 tesseract.js 做中文 OCR，再从文字中匹配字段。
//
// 纯字段提取逻辑已抽到 invoiceFields.ts（无浏览器依赖，可 Node 单测）；
// 本文件只负责「文件 -> 文本」与「OCR 兜底」，并复用 invoiceFields 的提取/校验。

import JSZip from 'jszip'
import * as pdfjsLib from 'pdfjs-dist'
// @ts-ignore - Vite 会将 worker 文件处理为 URL
import PdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

pdfjsLib.GlobalWorkerOptions.workerSrc = PdfWorker

// cMap / 标准字体：pdfjs 解码 CID 字体（数电票常见）必须，置于 public/ 下随构建发布
const CMAP_URL = '/cmaps/'
const CMAP_PACKED = true
const STANDARD_FONT_DATA_URL = '/standard_fonts/'

// 复用纯字段提取（来自 invoiceFields.ts）
import { extractInvoiceFields, extractLineItems, validateInvoice, verifyInvoice } from './invoiceFields'
import type { ParsedInvoice, ParsedLineItem, ValidationResult, VerifyResult } from './invoiceFields'
export { extractInvoiceFields, extractLineItems, validateInvoice, verifyInvoice }
export type { ParsedInvoice, ParsedLineItem, ValidationResult, VerifyResult }

// 判断提取文本是否过空（标签与值相隔极远或字体无法解码），决定是否需要 OCR 兜底
function looksEmpty(text: string): boolean {
  const hasCompany = /(公司|酒店|企业|厂|店|中心|集团|税务局|铁路)/.test(text)
  const hasLongDigit = /\d{8,}/.test(text)
  const hasChinese = /[一-鿿]/.test(text)
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

// ===== PDF 文字提取（版面感知）=====
// 把每个字形按 (y 行, x 列) 归位：同一行内字形直接拼接（不插空格），
// 行间用换行分隔。这样「销 售 方 信 息」会还原成「销售方信息」，
// 而带小数点的金额（如 755.66 83.02）虽同行拼接为 755.6683.02，
// 但小数点天然锚定，字段提取时按 *.dd 仍可分出 755.66 / 83.02，不受影响。
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
    const items = content.items.filter((it: any) => 'str' in it && it.str)
    if (!items.length) {
      text += '\n'
      continue
    }
    // 按 y 行分组（四舍五入到 3 单位，容忍基线抖动）
    const lines = new Map<number, any[]>()
    for (const it of items) {
      const t = it as any
      const y = Math.round((t.transform[5] ?? 0) / 3) * 3
      if (!lines.has(y)) lines.set(y, [])
      lines.get(y)!.push(it)
    }
    const ys = [...lines.keys()].sort((a, b) => b - a) // 从上到下
    for (const y of ys) {
      const row = lines.get(y)!.sort((a, b) => ((a as any).transform[4] ?? 0) - ((b as any).transform[4] ?? 0))
      text += row.map((it) => it.str).join('') + '\n'
    }
    text += '\n'
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
// 离线化：worker / wasm 核心 / 中文字库均置于 public/tesseract/ 随构建发布，
// 不再从 CDN（jsdelivr）拉取，OCR 运行时零联网。
// 字库需先执行 `npm run setup:ocr`（scripts/fetch-tesseract-lang.mjs）拉取一次。
const TESS_WORKER_PATH = '/tesseract/worker.min.js'
const TESS_CORE_PATH = '/tesseract/core/tesseract-core.wasm.js'
const TESS_LANG_PATH = '/tesseract/lang/'

async function ocrToText(input: File | HTMLCanvasElement): Promise<string> {
  const Tesseract = await import('tesseract.js')
  const worker = await Tesseract.createWorker('chi_sim+eng', 1, {
    workerPath: TESS_WORKER_PATH,
    corePath: TESS_CORE_PATH,
    langPath: TESS_LANG_PATH,
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

  // 文字足够则直接用文字解析
  if (!looksEmpty(rawText)) {
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
