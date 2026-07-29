import { execSync } from 'node:child_process'
import { readFileSync, mkdirSync, rmSync } from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const __dirname = path.dirname(new URL(import.meta.url).pathname)
const root = path.resolve(__dirname, '..')
const buildDir = path.join(root, '.invoice-test-build-real950')
rmSync(buildDir, { recursive: true, force: true })
mkdirSync(buildDir, { recursive: true })
const tsc = path.join(root, 'node_modules/typescript/bin/tsc')
for (const f of ['invoiceFields.ts', 'invoiceDual.ts']) {
  execSync(
    `node "${tsc}" "${path.join(root, 'src/utils', f)}" --outDir "${buildDir}" --module esnext --target es2020 --moduleResolution bundler --lib es2020,dom --skipLibCheck --ignoreConfig`,
    { stdio: 'inherit', cwd: root },
  )
}
const { extractInvoiceFields } = await import(pathToFileURL(path.join(buildDir, 'invoiceFields.js')).href)
const { extractInvoiceFieldsV2, dualRecognize } = await import(pathToFileURL(path.join(buildDir, 'invoiceDual.js')).href)

const text = readFileSync(path.join(__dirname, 'fixtures/invoices/flight_itinerary_950_real_ocr.txt'), 'utf8')
const gate = dualRecognize(text, extractInvoiceFields, extractInvoiceFieldsV2)
console.log('=== 950 real OCR dualRecognize ===')
console.log('consistent =', gate.consistent)
console.log('diffs:', JSON.stringify(gate.diffs))
const r1 = gate.r1, r2 = gate.r2
console.log(`r1: type=${r1.type} no=${r1.no} total=${r1.total} amount=${r1.amount} tax=${r1.tax} seller=${r1.sellerName}`)
console.log(`r2: type=${r2.type} no=${r2.no} total=${r2.total} amount=${r2.amount} tax=${r2.tax} seller=${r2.sellerName}`)
