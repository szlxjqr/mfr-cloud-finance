// 构建前把 pdfjs 的 cMap 与标准字体复制到 public/，供浏览器解码 CID 字体（数电票常见）
// 这些文件体积大、随 pdfjs-dist 版本变化，故从 node_modules 生成，不纳入 git
import { cp, mkdir } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = resolve(__dirname, '..')
const src = resolve(root, 'node_modules/pdfjs-dist')
const dest = resolve(root, 'public')

async function copyDir(name) {
  const from = resolve(src, name)
  const to = resolve(dest, name)
  if (!existsSync(from)) {
    console.warn(`[copy-pdfjs-assets] 未找到 ${from}，跳过`)
    return
  }
  await mkdir(to, { recursive: true })
  await cp(from, to, { recursive: true })
  console.log(`[copy-pdfjs-assets] 已复制 ${name} -> public/${name}`)
}

await copyDir('cmaps')
await copyDir('standard_fonts')
