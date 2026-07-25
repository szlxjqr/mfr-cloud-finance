#!/usr/bin/env node
/**
 * 重新解析发票箱中所有发票的 rawText，用最新的 extractInvoiceFields（负号+合计行版）
 * 用法：node scripts/reparse_invoices.mjs < input.json > output.json
 * input.json: [{ id, rawText }]
 * output.json: [{ id, newJson }] （newJson 是序列化后的 ParsedInvoice JSON 字符串）
 */
import { execSync } from 'node:child_process'
import { readFileSync, mkdirSync, rmSync } from 'node:fs'
import { pathToFileURL } from 'node:url'
import path from 'node:path'

const __dirname = path.dirname(new URL(import.meta.url).pathname)
const root = path.resolve(__dirname, '..') // frontend/
const tsFile = path.join(root, 'src/utils/invoiceFields.ts')
const buildDir = path.join(root, '.reparse-build')

// 1. 编译 invoiceFields.ts → JS
rmSync(buildDir, { recursive: true, force: true })
mkdirSync(buildDir, { recursive: true })
execSync(
  `node "${path.join(root, 'node_modules/.bin/tsc')}" "${tsFile}" --outDir "${buildDir}" --module esnext --target es2020 --moduleResolution bundler --lib es2020,dom --skipLibCheck --ignoreConfig`,
  { cwd: root, stdio: 'pipe' },
)

// 2. 加载编译后的模块
const modPath = pathToFileURL(path.join(buildDir, 'invoiceFields.js')).href
const { extractInvoiceFields } = await import(modPath)

// 3. 读 stdin 的发票列表
const inputStr = readFileSync('/dev/stdin', 'utf-8').trim()
const rows = JSON.parse(inputStr)

const results = []
for (const row of rows) {
  const { id, rawText } = row
  if (!rawText) {
    results.push({ id, error: '无 rawText' })
    continue
  }
  try {
    const parsed = extractInvoiceFields(rawText)
    // 去掉 rawText（已有）
    delete parsed.rawText
    // 序列化回 JSON 字符串
    const newJson = JSON.stringify(parsed)
    results.push({ id, newJson })
  } catch (e) {
    results.push({ id, error: String(e) })
  }
}

// 输出结果
process.stdout.write(JSON.stringify(results, null, 2))
