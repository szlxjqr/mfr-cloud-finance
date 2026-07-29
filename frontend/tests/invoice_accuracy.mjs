// 发票字段解析 —— 离线回归测试（不依赖网络，不提交任何真实发票）。
//
// 做法：用本项目自带的 typescript 把 src/utils/invoiceFields.ts 现场编译成 ESM，
// 再对每个 fixtures/invoices/*.txt（脱敏文本）跑 extractInvoiceFields，
// 与下方 EXPECTED 对照。所有公司名 / 税号 / 金额均为虚构，仅保留真实票面「版式结构」，
// 用于锁死解析逻辑（名称顺序=购→销、金额 税率% 税额 三元组、价税合计、火车票中国铁路等）。
//
// 运行：node frontend/tests/invoice_accuracy.mjs   （建议从仓库前端根目录执行）

import { execSync } from 'node:child_process'
import { readFileSync, readdirSync, mkdirSync, rmSync } from 'node:fs'
import { pathToFileURL } from 'node:url'
import path from 'node:path'

const __dirname = path.dirname(new URL(import.meta.url).pathname)
const root = path.resolve(__dirname, '..') // frontend/
const tsFile = path.join(root, 'src/utils/invoiceFields.ts')
const buildDir = path.join(root, '.invoice-test-build')
const fxDir = path.join(__dirname, 'fixtures/invoices')

// 1) 本地 tsc 现场编译 invoiceFields.ts（纯逻辑、无浏览器依赖）
rmSync(buildDir, { recursive: true, force: true })
mkdirSync(buildDir, { recursive: true })
const tsc = path.join(root, 'node_modules/typescript/bin/tsc')
execSync(
  `node "${tsc}" "${tsFile}" --outDir "${buildDir}" --module esnext --target es2020 --moduleResolution bundler --lib es2020,dom --skipLibCheck --ignoreConfig`,
  { stdio: 'inherit', cwd: root },
)
const { extractInvoiceFields, validateInvoice } = await import(
  pathToFileURL(path.join(buildDir, 'invoiceFields.js')).href,
)

// 2) 脱敏真值（版式与真实样本一致，实体全部虚构）
const EXPECTED = {
  vat_special: {
    no: '8811700000999999990', date: '2026-07-20',
    buyer: '北极星贸易有限公司', seller: '金星智能科技有限公司',
    bTax: '91110000MA0000011B', sTax: '92110000MA0000022C',
    total: 55.70, amount: 49.29, tax: 6.41,
  },
  flight_multi: {
    no: '8821700000999999990', date: '2026-06-28',
    buyer: '北极星贸易有限公司', seller: '南天国际旅行社有限公司',
    bTax: '93110000MA0000033D', sTax: '94110000MA0000044E',
    total: 889.00, amount: 838.68, tax: 50.32,
  },
  hotel_bill: {
    no: undefined, date: '2026-06-13',
    buyer: undefined, seller: '长江明珠大酒店',
    total: 592.33,
  },
  hotel_vat: {
    no: '8831200000999999990', date: '2026-07-03',
    buyer: '北极星贸易有限公司', seller: '西湖云栖酒店管理有限公司',
    bTax: '91110000MA0000011B', sTax: '95110000MA0000055F',
    total: 342.44, amount: 323.06, tax: 19.38,
  },
  // 铁路电子客票（真实 PDF 文字层，pdfplumber 抽出）：票面仅印「票价=总价(含税)」，不印单独税额；
  // 销售方=中国铁路（票面「XX税务局」是开票机关），无销售方税号。按 9% 倒算金额/税额（方案A）。
  'train_real_26429165800003736397_627.5': {
    no: '26429165800003736397', date: '2026-06-27',
    buyer: '深圳市流形机器人科技有限公司', seller: '中国铁路',
    bTax: '91440300MAKF9C8P4U', sTax: undefined,
    total: 627.5, amount: 575.69, tax: 51.81, type: '铁路电子客票',
  },
  'train_real_26449165860003460657_70': {
    no: '26449165860003460657', date: '2026-06-27',
    buyer: '深圳市流形机器人科技有限公司', seller: '中国铁路',
    bTax: '91440300MAKF9C8P4U', sTax: undefined,
    total: 70.00, amount: 64.22, tax: 5.78, type: '铁路电子客票',
  },
  'train_real_26449165860003460673_630': {
    no: '26449165860003460673', date: '2026-06-27',
    buyer: '深圳市流形机器人科技有限公司', seller: '中国铁路',
    bTax: '91440300MAKF9C8P4U', sTax: undefined,
    total: 630.00, amount: 577.98, tax: 52.02, type: '铁路电子客票',
  },
  'train_real_26959124659000113965_94': {
    no: '26959124659000113965', date: '2026-06-27',
    buyer: '深圳市流形机器人科技有限公司', seller: '中国铁路',
    bTax: '91440300MAKF9C8P4U', sTax: undefined,
    total: 94.00, amount: 86.24, tax: 7.76, type: '铁路电子客票',
  },
  // 航空运输电子客票行程单：票价/燃油均不含税，民航发展基金为非税附加费（不进 VAT）。
  // 价税合计 = 票价688.07 + 燃油137.61 + 税额74.32 = 900.00（≠ 票面合计 950.00）。
  flight_itinerary: {
    no: '26958893211046753401', date: '2026-06-11',
    buyer: '深圳市流形机器人科技有限公司', seller: '北京嘉信浩远信息技术有限公司',
    bTax: '91440300MAKF9C8P4U', sTax: undefined,
    total: 900.00, amount: 825.68, tax: 74.32,
    nonTaxAmount: 50.00, ticketNo: '8932716534855',
  },
  flight_itinerary_660: {
    no: '26318781111046757199', date: '2026-06-13',
    buyer: '深圳市流形机器人科技有限公司', seller: '中国东方航空股份有限公司',
    bTax: '91440300MAKF9C8P4U', sTax: undefined,
    total: 610.00, amount: 559.63, tax: 50.37,
    nonTaxAmount: 50.00, ticketNo: '7812168781969',
  },
  // 660 行程单 + OCR 前导 1 噪声：发票号被多识别一个前导 1（21 位）→ 应自动剥离还原为 20 位真号。
  flight_itinerary_660_leading1: {
    no: '26318781111046757199', date: '2026-06-13',
    buyer: '深圳市流形机器人科技有限公司', seller: '中国东方航空股份有限公司',
    bTax: '91440300MAKF9C8P4U', sTax: undefined,
    total: 610.00, amount: 559.63, tax: 50.37,
    nonTaxAmount: 50.00, ticketNo: '7812168781969',
  },
  // 去哪儿网酒店专票：标签/值分块排版，之前会把销售方抓成「日深圳市...」。
  qunar_hotel_vat: {
    no: '26127000000333204200', date: '2026-07-03',
    buyer: '深圳市流形机器人科技有限公司', seller: '去哪儿网（天津）国际旅行社有限公司武清分公司',
    bTax: '91440300MAKF9C8P4U', sTax: '91120222MA82BC2U42',
    total: 592.33, amount: 558.80, tax: 33.53,
  },
  // 杭州酒店专票真实 pdfjs 文字层：标签与值被 pdf.js 完全重排，验证税号前后窗口反查购销方。
  hotel_einvoice_hangzhou_pdfjs: {
    no: '26332000005732165041', date: '2026-07-03',
    buyer: '深圳市流形机器人科技有限公司', seller: '杭州呈华酒店管理有限公司',
    bTax: '91440300MAKF9C8P4U', sTax: '91330108MA2GNMJT9L',
    total: 342.44, amount: 323.06, tax: 19.38,
  },
  // 950 行程单真实 OCR 文本：票价/燃油/基金标签全丢，只剩金额列；验证金额列推断 + fixMoneySpaces。
  flight_itinerary_950_ocr: {
    no: '26958893211046753401', date: '2026-06-28',
    buyer: '深圳市流形机器人科技有限公司', seller: '北京嘉信浩远信息技术有限公司',
    bTax: '91440300MAKF9C8P4U', sTax: undefined,
    total: 900.00, amount: 825.68, tax: 74.32,
    nonTaxAmount: 50.00, ticketNo: '8932716534855', type: '航空运输电子客票行程单',
  },
  // 河源酒店专票真实 pdfjs 文字层：购销方名被税务局监制章干扰，验证销售方过滤。
  hotel_einvoice_heyuan_pdfjs: {
    no: '26442000007537807276', date: '2026-07-03',
    buyer: '北极星贸易有限公司', seller: '河源云端酒店管理有限公司',
    bTax: '91110000MA0000011B', sTax: '91441600MA00000HEY',
    total: 293.00, amount: 276.42, tax: 16.58,
  },
  // 武汉去哪儿网酒店账单（非发票收据）：无票号无税额，验证收据兜底路径。
  hotel_bill_wuhan_qunar: {
    no: undefined, date: '2026-06-13',
    buyer: undefined, seller: '武汉长江明珠酒店',
    total: 592.33, amount: 592.33, tax: 0,
  },
}

const norm = (s) => (s || '').replace(/\s+/g, '')
const num = (x) => (x == null ? NaN : Number(x))
function cmp(field, got, exp) {
  if (exp === undefined) return got === undefined ? '·' : 'info'
  if (field === 'no' || field === 'bTax' || field === 'sTax') {
    return got === exp ? 'ok' : `✗ got=${got ?? '(空)'}`
  }
  if (field === 'total' || field === 'amount' || field === 'tax') {
    return num(got) === exp ? 'ok' : `✗ got=${got ?? '(空)'}`
  }
  const g = norm(String(got ?? '')), e = norm(String(exp ?? ''))
  if (!g && e) return `✗ got=${got ?? '(空)'}`
  if (g === e || g.includes(e) || e.includes(g)) return 'ok'
  return `✗ got=${got ?? '(空)'}`
}

const rows = (p) => [
  ['no', p.no, EXPECTED[p._k].no],
  ['date', p.date, EXPECTED[p._k].date],
  ['buyer', p.buyerName, EXPECTED[p._k].buyer],
  ['seller', p.sellerName, EXPECTED[p._k].seller],
  ['bTax', p.buyerTaxNo, EXPECTED[p._k].bTax],
  ['sTax', p.sellerTaxNo, EXPECTED[p._k].sTax],
  ['total', p.total, EXPECTED[p._k].total],
  ['amount', p.amount, EXPECTED[p._k].amount],
  ['tax', p.tax, EXPECTED[p._k].tax],
  ['nonTax', p.nonTaxAmount, EXPECTED[p._k].nonTaxAmount],
  ['ticketNo', p.ticketNo, EXPECTED[p._k].ticketNo],
  ['type', p.type, EXPECTED[p._k].type],
]

let pass = 0, fail = 0
for (const f of readdirSync(fxDir).filter((f) => f.endsWith('.txt')).sort()) {
  const stem = f.replace(/\.txt$/, '')
  if (!EXPECTED[stem]) continue
  const text = readFileSync(path.join(fxDir, f), 'utf8')
  const p = extractInvoiceFields(text)
  p._k = stem
  const v = validateInvoice(p)
  console.log(`\n========== ${f} ==========`)
  for (const [fld, got, exp] of rows(p)) {
    const flag = cmp(fld, got, exp)
    if (flag === 'ok') pass++
    else if (flag.startsWith('✗')) fail++
    console.log(`  ${fld.padEnd(8)} got=${String(got ?? '∅').padEnd(28)} ${flag}`)
  }
  if (v.missing.length) console.log(`  [validate] missing: ${v.missing.join(', ')}`)
}

console.log(`\n========== 汇总：pass=${pass}  fail=${fail} ==========`)
process.exit(fail > 0 ? 1 : 0)
