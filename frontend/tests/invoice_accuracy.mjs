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
  train_ticket: {
    no: '88449165860009999990', seller: '中国铁路',
    total: 630.00, sTax: '93110000MA0000011B',
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
  const g = norm(got), e = norm(exp)
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
