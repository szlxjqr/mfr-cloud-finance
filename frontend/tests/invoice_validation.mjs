// 发票公式核对权威判定 —— 离线回归测试。
// 验证：核心三数自洽、税率推导、leading-1 自动校正。
//
// 运行：node frontend/tests/invoice_validation.mjs

import { execSync } from 'node:child_process'
import { readFileSync, mkdirSync, rmSync } from 'node:fs'
import { pathToFileURL } from 'node:url'
import path from 'node:path'

const __dirname = path.dirname(new URL(import.meta.url).pathname)
const root = path.resolve(__dirname, '..')
const tsFile = path.join(root, 'src/utils/invoiceFields.ts')
const buildDir = path.join(root, '.invoice-test-build')
const fxDir = path.join(__dirname, 'fixtures/invoices')

rmSync(buildDir, { recursive: true, force: true })
mkdirSync(buildDir, { recursive: true })
const tsc = path.join(root, 'node_modules/typescript/bin/tsc')
execSync(
  `node "${tsc}" "${tsFile}" --outDir "${buildDir}" --module esnext --target es2020 --moduleResolution bundler --lib es2020,dom --skipLibCheck --ignoreConfig`,
  { stdio: 'inherit', cwd: root },
)
const { extractInvoiceFields, verifyInvoice, validateInvoice } = await import(
  pathToFileURL(path.join(buildDir, 'invoiceFields.js')).href,
)

const TOLERANCE = 0.02
let pass = 0, fail = 0

function assert(name, cond, msg) {
  if (cond) {
    pass++
    console.log(`  ✓ ${name}`)
  } else {
    fail++
    console.log(`  ✗ ${name}: ${msg}`)
  }
}

function runFixture(name, expect) {
  const text = readFileSync(path.join(fxDir, `${name}.txt`), 'utf8')
  const p = extractInvoiceFields(text)
  const v = verifyInvoice(p)
  console.log(`\n========== ${name}.txt ==========`)
  console.log(`  amount=${p.amount} tax=${p.tax} total=${p.total} rate=${p.taxRate} derivedRate=${v.derivedRate} passed=${v.passed} corrected=${v.corrected}`)
  if (expect.passed !== undefined) assert('公式核对通过', v.passed === expect.passed, `passed=${v.passed}`)
  if (expect.rate !== undefined) assert(`税率=${expect.rate}%`, Math.abs((v.rate ?? -1) - expect.rate) < TOLERANCE, `rate=${v.rate}`)
  if (expect.amount !== undefined) assert(`金额=${expect.amount}`, Math.abs((v.corrected ? v.correctedAmount : p.amount) - expect.amount) < TOLERANCE, `amount=${p.amount}`)
  if (expect.total !== undefined) assert(`价税合计=${expect.total}`, Math.abs((v.corrected ? v.correctedTotal : p.total) - expect.total) < TOLERANCE, `total=${p.total}`)
  if (expect.corrected !== undefined) assert(`自动校正=${expect.corrected}`, v.corrected === expect.corrected, `corrected=${v.corrected}`)
}

// 正常 13% 专票：应通过，税率 13
runFixture('vat_special', { passed: true, rate: 13, amount: 49.29, total: 55.70, corrected: false })

// 正常酒店 VAT 发票：应通过，税率 6%（19.38/323.06≈6%）
runFixture('hotel_vat', { passed: true, rate: 6, amount: 323.06, total: 342.44, corrected: false })

// leading-1 脏值：金额 1389.38→2389.38，价税合计 1570→2570，税额 180.62 正确
// 应自动校正回 amount=1389.38, total=1570.00, rate=13%
runFixture('leading_one_13pct', { passed: true, rate: 13, amount: 1389.38, total: 1570.00, corrected: true })

// 核心字段缺失校验
console.log('\n========== validateInvoice 核心字段校验 ==========')
const empty = extractInvoiceFields('')
const vr = validateInvoice(empty)
assert('空文本校验失败', !vr.ok && vr.missing.includes('发票号码') && vr.missing.includes('合计金额'), `missing=${vr.missing.join(',')}`)

console.log(`\n========== 汇总：pass=${pass}  fail=${fail} ==========`)
process.exit(fail > 0 ? 1 : 0)
