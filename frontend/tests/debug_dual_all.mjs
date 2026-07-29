import { execSync } from 'node:child_process'
import { readFileSync, readdirSync, mkdirSync, rmSync } from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const __dirname = path.dirname(new URL(import.meta.url).pathname)
const root = path.resolve(__dirname, '..')
const buildDir = path.join(root, '.invoice-test-build-all')
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

const fxDir = path.join(__dirname, 'fixtures/invoices')
const files = readdirSync(fxDir).filter((f) => f.endsWith('.txt')).sort()
let fail = 0
const fails = []
for (const name of files) {
  const text = readFileSync(path.join(fxDir, name), 'utf8')
  const gate = dualRecognize(text, extractInvoiceFields, extractInvoiceFieldsV2)
  if (!gate.consistent) {
    fail++
    fails.push(`  [FAIL] ${name}  ${JSON.stringify(gate.diffs)}`)
  }
}
console.log(`双识别回归：总 ${files.length} 个 fixture，不一致 ${fail} 个`)
if (fails.length) console.log(fails.join('\n'))
