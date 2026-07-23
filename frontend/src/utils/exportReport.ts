/**
 * 报表导出工具（零新增依赖）
 * - Excel：用已依赖的 jszip 生成真正的 .xlsx（支持多 sheet，金额写为数字便于二次计算）
 * - PDF：独立打印窗口方案（克隆节点 + 注入样式 + @page A4），最稳、零依赖
 */

import JSZip from 'jszip'

export interface XlsxSheet {
  /** 工作表名（最长 31 字符，自动清洗） */
  name: string
  /** 二维数据，单元格可为 string / number / null */
  rows: (string | number | null)[][]
}

function escapeXml(s: unknown): string {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

/** 0-based 列号 → Excel 列名（A, B, ..., Z, AA...） */
function colRef(n: number): string {
  let s = ''
  let x = n + 1
  while (x > 0) {
    const r = (x - 1) % 26
    s = String.fromCharCode(65 + r) + s
    x = Math.floor((x - 1) / 26)
  }
  return s
}

/** 清洗工作表名：去除非法字符、限长 31 */
function sanitizeSheetName(name: string): string {
  let s = name.replace(/[\\/:?*[\]]/g, '').trim()
  if (!s) s = 'Sheet'
  return s.slice(0, 31)
}

/** 单个 worksheet 的 XML（含 sheetData） */
function sheetXml(rows: (string | number | null)[][]): string {
  const body = rows
    .map((row, ri) => {
      const cells = row
        .map((cell, ci) => {
          const ref = colRef(ci) + (ri + 1)
          if (cell === null || cell === undefined || cell === '') {
            return `<c r="${ref}"/>`
          }
          if (typeof cell === 'number' && Number.isFinite(cell)) {
            const v = Math.round(cell * 100) / 100
            return `<c r="${ref}" t="n"><v>${v}</v></c>`
          }
          return `<c r="${ref}" t="inlineStr"><is><t xml:space="preserve">${escapeXml(cell)}</t></is></c>`
        })
        .join('')
      return `<row r="${ri + 1}">${cells}</row>`
    })
    .join('')
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>${body}</sheetData></worksheet>`
}

async function buildXlsx(sheets: XlsxSheet[]): Promise<Blob> {
  const zip = new JSZip()
  const sheetXmls = sheets.map((s) => sheetXml(s.rows))

  const contentTypes = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
${sheets
    .map(
      (_, i) =>
        `<Override PartName="/xl/worksheets/sheet${i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`,
    )
    .join('\n')}
</Types>`
  zip.file('[Content_Types].xml', contentTypes)

  zip.file(
    '_rels/.rels',
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>`,
  )

  const workbook = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets>
${sheets
    .map(
      (s, i) =>
        `<sheet name="${escapeXml(sanitizeSheetName(s.name))}" sheetId="${i + 1}" r:id="rId${i + 1}"/>`,
    )
    .join('\n')}
</sheets>
</workbook>`
  zip.file('xl/workbook.xml', workbook)

  zip.file(
    'xl/_rels/workbook.xml.rels',
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
${sheets
    .map(
      (_, i) =>
        `<Relationship Id="rId${i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${i + 1}.xml"/>`,
    )
    .join('\n')}
</Relationships>`,
  )

  sheets.forEach((_, i) => zip.file(`xl/worksheets/sheet${i + 1}.xml`, sheetXmls[i]))

  return zip.generateAsync({
    type: 'blob',
    mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(url), 1500)
}

/** 导出真正的 .xlsx 文件（支持多工作表） */
export async function exportXlsx(filename: string, sheets: XlsxSheet[]) {
  if (!sheets.length) return
  const blob = await buildXlsx(sheets)
  triggerDownload(blob, filename.toLowerCase().endsWith('.xlsx') ? filename : filename + '.xlsx')
}

/** 打印当前报表节点为 PDF（浏览器「另存为 PDF」） */
export function printReport(title: string, el: HTMLElement | null | undefined) {
  if (!el) return
  const w = window.open('', '_blank', 'width=960,height=720')
  if (!w) {
    window.alert('导出 PDF 需要允许浏览器弹出窗口，请解除拦截后重试。')
    return
  }
  const styles = Array.from(document.querySelectorAll('style, link[rel="stylesheet"]'))
    .map((s) => s.outerHTML)
    .join('\n')
  const html = el.outerHTML

  w.document.open()
  w.document.write(
    `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${escapeXml(title)}</title>${styles}`,
  )
  w.document.write(`<style>
@page { size: A4; margin: 14mm; }
* { box-sizing: border-box; }
body { font-family: "Microsoft YaHei","PingFang SC","Hiragino Sans GB",sans-serif; color:#000; background:#fff; }
h1.rpt-title { text-align:center; font-size:18px; font-weight:700; margin:0 0 12px; }
.el-card { box-shadow:none !important; border:1px solid #dcdfe6 !important; }
.el-card__body { padding:12px !important; }
.toolbar { display:none !important; }
.el-table { box-shadow:none !important; }
.el-table::before { display:none !important; }
.el-table table { border-collapse:collapse !important; width:100%; }
.el-table th, .el-table td { border:1px solid #333 !important; padding:4px 8px !important; font-size:11px !important; }
.el-table .cell { line-height:1.4 !important; white-space:normal !important; }
.el-descriptions { margin-top:12px; }
.el-descriptions__body { border:1px solid #333; }
.el-descriptions__label, .el-descriptions__content { border:1px solid #333 !important; padding:4px 8px !important; font-size:11px; }
.hint { color:#666 !important; font-size:10px !important; }
.el-alert { display:none !important; }
.el-tabs__header, .el-tabs__nav, .el-tabs__item { display:none !important; }
.el-tabs__content { display:block !important; }
.el-tab-pane { display:block !important; }
</style>`)
  w.document.write(`</head><body>`)
  w.document.write(`<h1 class="rpt-title">${escapeXml(title)}</h1>`)
  w.document.write(html)
  w.document.write(
    `<p style="color:#999;font-size:10px;margin-top:10px;">导出时间：${new Date().toLocaleString(
      'zh-CN',
    )}　|　智慧经营</p>`,
  )
  w.document.write(`</body></html>`)
  w.document.close()

  const fire = () => {
    w.focus()
    w.print()
  }
  if (w.document.readyState === 'complete') fire()
  else w.onload = fire
}
