// 双识别（识别器① × 识别器②）离线回归测试。
//
// 做法：现场 tsc 编译 invoiceFields.ts 与 invoiceDual.ts，
// 在 fixtures/invoices/*.txt 上验证：
//   1) 识别器② 在已知样本上与①结果一致（双识别闸门应为 consistent）；
//   2) 注入一处不一致（篡改价税合计）→ dualRecognize 应判 consistent=false。
// 运行：node frontend/tests/invoice_dual.mjs   （建议从仓库前端根目录执行）

import { execSync } from 'node:child_process'
import { readFileSync, readdirSync, mkdirSync, rmSync } from 'node:fs'
import { pathToFileURL } from 'node:url'
import path from 'node:path'

const __dirname = path.dirname(new URL(import.meta.url).pathname)
const root = path.resolve(__dirname, '..') // frontend/
const tsFile = path.join(root, 'src/utils/invoiceFields.ts')
const dualFile = path.join(root, 'src/utils/invoiceDual.ts')
const buildDir = path.join(root, '.reparse-build')
const fxDir = path.join(__dirname, 'fixtures/invoices')

rmSync(buildDir, { recursive: true, force: true })
mkdirSync(buildDir, { recursive: true })
const tsc = path.join(root, 'node_modules/typescript/bin/tsc')
execSync(
  `node "${tsc}" "${tsFile}" "${dualFile}" --outDir "${buildDir}" --module esnext --target es2020 --moduleResolution bundler --lib es2020,dom --skipLibCheck --ignoreConfig`,
  { stdio: 'inherit', cwd: root },
)
const { extractInvoiceFields, validateInvoice } = await import(
  pathToFileURL(path.join(buildDir, 'invoiceFields.js')).href,
)
const { extractInvoiceFieldsV2, dualRecognize } = await import(
  pathToFileURL(path.join(buildDir, 'invoiceDual.js')).href,
)

// 已知真值（与 invoice_accuracy.mjs 同源，实体虚构）
const EXPECTED = {
  vat_special: { no: '8811700000999999990', seller: '金星智能科技有限公司', total: 55.70, amount: 49.29 },
  flight_multi: { no: '8821700000999999990', seller: '南天国际旅行社有限公司', total: 889.00, amount: 838.68 },
  hotel_bill: { no: undefined, seller: '长江明珠大酒店', total: 592.33 },
  hotel_vat: { no: '8831200000999999990', seller: '西湖云栖酒店管理有限公司', total: 342.44, amount: 323.06 },
  train_ticket: { no: '88449165860009999990', seller: '中国铁路', total: 630.00 },
  // OCR 把「单价」列识别成 10 位小数（698.2300884956），金额仍为 2 位（698.23）。
  // 双识别闸门应判一致（两识别器均只读取 2 位小数金额，超长小数被忽略）。
  hotel_vat_10dec: { no: '8831200000999999990', seller: '西湖云栖酒店管理有限公司', total: 789.00, amount: 698.23 },
}

const norm = (s) => (s || '').replace(/\s+/g, '')
let pass = 0, fail = 0
const ok = (label, cond, extra = '') => {
  if (cond) { pass++; console.log(`  ✓ ${label} ${extra}`) }
  else { fail++; console.log(`  ✗ ${label} ${extra}`) }
}

console.log('\n========== 1) 识别器② 精度（应≈①/已知真值）==========')
for (const f of readdirSync(fxDir).filter((f) => f.endsWith('.txt')).sort()) {
  const stem = f.replace(/\.txt$/, '')
  if (!EXPECTED[stem]) continue
  const text = readFileSync(path.join(fxDir, f), 'utf8')
  const r2 = extractInvoiceFieldsV2(text)
  const exp = EXPECTED[stem]
  console.log(`\n--- ${f} ---`)
  ok('no', exp.no === undefined ? r2.no === undefined : r2.no === exp.no, `got=${r2.no ?? '(空)'}`)
  ok('seller', norm(r2.sellerName).includes(norm(exp.seller)) || norm(exp.seller).includes(norm(r2.sellerName || '')), `got=${r2.sellerName ?? '(空)'}`)
  ok('total', Math.abs(Number(r2.total) - exp.total) <= 0.02, `got=${r2.total}`)
  if (exp.amount !== undefined) ok('amount', Math.abs(Number(r2.amount) - exp.amount) <= 0.02, `got=${r2.amount}`)
}

console.log('\n========== 2) 双识别闸门 dualRecognize ==========')
console.log('\n--- 2a) 已知样本应一致（consistent=true）---')
for (const f of readdirSync(fxDir).filter((f) => f.endsWith('.txt')).sort()) {
  const stem = f.replace(/\.txt$/, '')
  if (!EXPECTED[stem]) continue
  const text = readFileSync(path.join(fxDir, f), 'utf8')
  const g = dualRecognize(text, extractInvoiceFields, extractInvoiceFieldsV2)
  const r1 = extractInvoiceFields(text)
  const v = validateInvoice(r1)
  // 仅校验能被①有效解析的样本（无效样本不参与一致性断言）
  if (v.missing.length) { console.log(`  · 跳过 ${f}（①自身未完整识别）`); continue }
  ok(`${f} consistent`, g.consistent === true, g.consistent ? '' : `diffs=${JSON.stringify(g.diffs)}`)
}

console.log('\n--- 2b) 双识别结论不一致 → 应判 inconsistent ---')
// 注：篡改"源文本"会让两套识别器读到同一份篡改结果、仍会一致；
// 真正要防的是"两套算法给出不同结论"，故用自定义 r2Fn 模拟一处结论分歧。
{
  const text = readFileSync(path.join(fxDir, 'vat_special.txt'), 'utf8')
  // 篡改价税合计 → r1 取标签首 ¥=99.99，r2 由金额+税额反推=55.70 → 分歧
  const tampered = text.replace('¥55.70', '¥99.99')
  const g = dualRecognize(tampered, extractInvoiceFields, extractInvoiceFieldsV2)
  ok('价税合计分歧 → consistent=false', g.consistent === false, `diffs=${JSON.stringify(g.diffs)}`)
}
{
  const text = readFileSync(path.join(fxDir, 'vat_special.txt'), 'utf8')
  // 模拟识别器②把发票号码识别成另一串 → 与①不一致
  const g = dualRecognize(text, extractInvoiceFields, (t) => {
    const r = extractInvoiceFieldsV2(t)
    r.no = '8811700000999999991'
    return r
  })
  ok('发票号码分歧 → consistent=false', g.consistent === false, `diffs=${JSON.stringify(g.diffs)}`)
}

console.log(`\n========== 汇总：pass=${pass}  fail=${fail} ==========`)
process.exit(fail > 0 ? 1 : 0)
