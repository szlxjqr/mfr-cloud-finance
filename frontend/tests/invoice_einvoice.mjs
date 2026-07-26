// 数电票（阿里）文字层样本 —— 离线回归测试。
// 验证：逐字空格 / 多明细行 / 发票号 19 位空格分隔，3 关键字段 + 公式自洽。
//
// 运行：node frontend/tests/invoice_einvoice.mjs

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
  if (cond) { pass++; console.log(`  ✓ ${name}`) }
  else { fail++; console.log(`  ✗ ${name}: ${msg}`) }
}

function runFixture(name, expect) {
  const text = readFileSync(path.join(fxDir, `${name}.txt`), 'utf8')
  const p = extractInvoiceFields(text)
  const v = verifyInvoice(p)
  const vr = validateInvoice(p)
  console.log(`\n========== ${name}.txt ==========`)
  console.log(`  no=${p.no}`)
  console.log(`  amount=${p.amount}  tax=${p.tax}  rate=${p.taxRate}%  total=${p.total}`)
  console.log(`  validate.ok=${vr.ok}  verify.passed=${v.passed}  derivedRate=${v.derivedRate}`)
  assert('发票号识别', p.no === expect.no, `no=${p.no}`)
  assert('金额正确', Math.abs(p.amount - expect.amount) < TOLERANCE, `amount=${p.amount}`)
  assert('税额正确', Math.abs(p.tax - expect.tax) < TOLERANCE, `tax=${p.tax}`)
  assert('价税合计正确', Math.abs(p.total - expect.total) < TOLERANCE, `total=${p.total}`)
  const expRate = expect.rate ?? 13
  assert(`税率=${expRate}%`, Math.abs((p.taxRate ?? -1) - expRate) < TOLERANCE, `rate=${p.taxRate}`)
  assert('公式自洽通过', v.passed === true, `passed=${v.passed}`)
  // 公式最终核对：金额 + 税额 ≈ 价税合计
  assert('金额+税额≈价税合计', Math.abs((p.amount + p.tax) - p.total) < TOLERANCE, `${(p.amount + p.tax)} vs ${p.total}`)
}

// 数电票（增值税专用发票）：逐字空格 + 单明细
runFixture('einvoice_ali_997', { no: '26442000007573664761', amount: 883.12, tax: 114.80, total: 997.92 })
// 数电票：单明细
runFixture('einvoice_ali_789', { no: '26442000008022731566', amount: 698.23, tax: 90.77, total: 789.00 })
// 数电票：逐字空格（含发票号 19 位空格分隔）+ 单明细（金额 1636.28 税额 212.72）
runFixture('einvoice_ali_1849', { no: '26442000008239533091', amount: 1636.28, tax: 212.72, total: 1849.00 })
// 数电票：多明细行（RGB摄像头 173.35/22.54 + 自动回充套件 654.51/85.09 = 827.86/107.63，合计 935.49）
runFixture('einvoice_ali_935', { no: '26442000008239534726', amount: 827.86, tax: 107.63, total: 935.49 })
// 数电票（天津海利士·服务器内存条）：普通发票、单明细、金额 4102.65 税额 533.35 价税合计 4636.00，税率 13%
runFixture('einvoice_tjhls_4636', { no: '26122000000986294521', amount: 4102.65, tax: 533.35, total: 4636.00 })
// 数电票（武汉宝之谷·电源）：普通发票、单明细、金额 651.77 税额 84.73 价税合计 736.50，税率 13%
runFixture('einvoice_bzg_736', { no: '26422000002627891131', amount: 651.77, tax: 84.73, total: 736.50 })
// 数电票（深圳极途智联·显卡）：普通发票、单明细、金额 3460.50 税额 34.60 价税合计 3495.10，税率 1%（征收率）
runFixture('einvoice_jtzl_3495', { no: '26952000003079065211', amount: 3460.50, tax: 34.60, total: 3495.10, rate: 1 })
// 数电票（深圳拓骏成·主板套装）：专票、单明细、金额 1644.25 税额 213.75 价税合计 1858.00，税率 13%（套），单价 10 位小数黏连
runFixture('einvoice_tjc_1858', { no: '26952000003079141321', amount: 1644.25, tax: 213.75, total: 1858.00 })
// 京东电子发票（普通发票）：标签倒序 + 裸税率黏连（76.1613% 无单位字）+ 政府补贴干扰行，金额 585.84 税额 76.16 价税合计 662.00，税率 13%
runFixture('einvoice_jd_662', { no: '26507000000213438551', amount: 585.84, tax: 76.16, total: 662.00 })
// 京东电子发票（普通发票）：含折扣负数行，金额 359.66(406.19-46.53) 税额 46.76(52.81-6.05) 价税合计 406.42，税率 13%（裸%黏连：52.8113% / -6.0513%）
runFixture('einvoice_jd2_406', { no: '26957000000158395934', amount: 359.66, tax: 46.76, total: 406.42 })
// 京东电子发票（增值税专用发票）：有购买方（深圳市流形机器人科技）+ 折扣负数行，金额 5043.36(5220.35-176.99) 税额 655.64(678.65-23.01) 价税合计 5699.00，税率 13%（裸%黏连：678.6513% / -23.0113%）
runFixture('einvoice_jd3_5699', { no: '26447000001433301728', amount: 5043.36, tax: 655.64, total: 5699.00 })
// 京东电子发票（增值税专用发票）：同销售方(广州晶东)+购买方(深圳流形)、东芝18TB硬盘、折扣负数行，金额 5165.58(5485.84-320.26) 税额 671.53(713.16-41.63) 价税合计 5837.11，税率 13%（裸%黏连：713.1613% / -41.6313%；价税合计符号为 ´ U+00B4 已由 normLabels 归一）
runFixture('einvoice_jd4_5837', { no: '26447000001433301166', amount: 5165.58, tax: 671.53, total: 5837.11 })
// 京东电子发票（增值税专用发票）：同模板、梵想2TB SSD、折扣负数行，金额 1320.44(1415.04-94.60) 税额 171.66(183.96-12.30) 价税合计 1492.10，税率 13%（裸%黏连：183.9613% / -12.3013%；价税合计符号 ´ U+00B4 已归一）
runFixture('einvoice_jd5_1492', { no: '26447000001433300015', amount: 1320.44, tax: 171.66, total: 1492.10 })
// 京东电子发票（增值税专用发票）：同模板、长城黑匣子09 AI机箱、折扣负数行，金额 356.46(453.98-97.52) 税额 46.34(59.02-12.68) 价税合计 402.80，税率 13%（裸%黏连：59.0213% / -12.6813%；价税合计符号 ´ U+00B4 已归一）
runFixture('einvoice_jd6_402', { no: '26447000001432310327', amount: 356.46, tax: 46.34, total: 402.80 })
// 京东电子发票（普通发票·首个「数量>1」明细）：长城朔风S120风扇 数量3 单价61.86 金额185.58、折扣负数行，金额 174.45(185.58-11.13) 税额 22.67(24.12-1.45) 价税合计 197.12，税率 13%（裸%黏连：24.1213% / -1.4513%；价税合计符号为正常 ¥）
runFixture('einvoice_jd7_197', { no: '26447000001446516422', amount: 174.45, tax: 22.67, total: 197.12 })
// 京东电子发票（普通发票）：同模板、长城朔风S120风扇、多数量(个 3)+折扣负数行，金额 167.88(185.58-17.70) 税额 21.82(24.12-2.30) 价税合计 189.70，税率 13%（裸%黏连：24.1213% / -2.3013%；价税合计符号 ¥ 正常）
runFixture('einvoice_jd8_189', { no: '26447000001440569563', amount: 167.88, tax: 21.82, total: 189.70 })
// 京东电子发票（增值税专用发票）：同模板、梵想1TB SSD、折扣负数行，金额 775.18(777.88-2.70) 税额 100.77(101.12-0.35) 价税合计 875.95，税率 13%（裸%黏连：101.1213% / -0.3513%；价税合计符号 ´ U+00B4 已归一）
runFixture('einvoice_jd9_875', { no: '26447000001453308870', amount: 775.18, tax: 100.77, total: 875.95 })
// 京东电子发票（普通发票）：新前缀26337系列·销售方变「杭州京东霁纬信息技术有限公司」·购买方为个人「沈雷」(身份证号)·梵想500GB SSD·折扣负数行，金额 541.61(600.88-59.27) 税额 70.42(78.12-7.70) 价税合计 612.03，税率 13%（裸%黏连：78.1213% / -7.7013%；价税合计 ¥ 正常）
runFixture('einvoice_jd10_612', { no: '26337000000453256160', amount: 541.61, tax: 70.42, total: 612.03 })
// 京东电子发票（增值税专用发票）：新前缀26117系列·销售方变「北京京东达锐贸易有限公司」·单明细无折扣·品胜随身WiFi，金额 49.29 税额 6.41 价税合计 55.70，税率 13%（裸%黏连：6.4113%；价税合计符号 ´ U+00B4 已归一）
runFixture('einvoice_jd11_55', { no: '26117000001082322937', amount: 49.29, tax: 6.41, total: 55.70 })
// 京东电子发票（普通发票）：新前缀26377系列·销售方变「济南京东奥升贸易有限公司」·购买方为个人「沈雷」(身份证号)·梵想M.2移动硬盘盒·折扣负数行，金额 61.64(69.03-7.39) 税额 8.01(8.97-0.96) 价税合计 69.65，税率 13%（裸%黏连：8.9713% / -0.9613%；价税合计 ¥ 正常）
runFixture('einvoice_jd12_69', { no: '26377000000427294834', amount: 61.64, tax: 8.01, total: 69.65 })
// 京东电子发票（增值税专用发票·企业购）：销售方「广州晶东」+购买方「深圳流形」·单明细无折扣·京东PLUS企业会员年卡，金额 282.08 税额 16.92 价税合计 299.00，税率 **6%**（首个非13%京东票：16.926% 裸%黏连；价税合计符号 ´ U+00B4 已归一）
runFixture('einvoice_jd13_299', { no: '26447000001400970371', amount: 282.08, tax: 16.92, total: 299.00, rate: 6 })
// 京东电子发票（增值税专用发票·企业购）：销售方「广州晶东」+购买方「深圳流形」·单明细无折扣·京东京造纯牛奶(乳制品)·税率 **9%**（首个9%京东票：3.209% 裸%黏连=税额3.20+税率9%；价税合计符号 ´ U+00B4 已归一）
runFixture('einvoice_jd14_37', { no: '26447000001453308855', amount: 34.67, tax: 3.13, total: 37.80, rate: 9 })

console.log(`\n========== 汇总：pass=${pass}  fail=${fail} ==========`)
process.exit(fail > 0 ? 1 : 0)
