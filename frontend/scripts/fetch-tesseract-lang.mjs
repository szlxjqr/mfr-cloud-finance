// 一次性拉取 tesseract 中文字库到 public/tesseract/lang/，使 OCR 运行时零联网。
// 字库来自 tesseract.js 官方默认托管 tessdata.projectnaptha.com（与 tesseract.js 5.x 同源）；
// 注：原 jsdelivr 的 @tesseract.js-data 包已不可用（元数据 502 / 文件 400），故改走官方宿主。
// 用法：node scripts/fetch-tesseract-lang.mjs  （需联网一次；产物不入库，见 .gitignore）
import { createWriteStream } from 'node:fs'
import { mkdir } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import https from 'node:https'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUT_DIR = resolve(__dirname, '../public/tesseract/lang')
// @tesseract.js-data 提供的训练数据（.traineddata.gz）
const FILES = ['chi_sim.traineddata.gz', 'eng.traineddata.gz']
const BASE = 'https://tessdata.projectnaptha.com/4.0.0'

function fetchWithRedirect(url, dest, redirects = 0) {
  return new Promise((resolve, reject) => {
    if (redirects > 8) return reject(new Error('重定向过多：' + url))
    https
      .get(url, (res) => {
        if (res.statusCode && res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          const next = res.headers.location.startsWith('http')
            ? res.headers.location
            : new URL(res.headers.location, url).href
          res.resume()
          return resolve(fetchWithRedirect(next, dest, redirects + 1))
        }
        if (res.statusCode !== 200) {
          res.resume()
          return reject(new Error(`下载失败 ${res.statusCode}：${url}`))
        }
        const file = createWriteStream(dest)
        res.pipe(file)
        file.on('finish', () => file.close(() => resolve(dest)))
        file.on('error', reject)
      })
      .on('error', reject)
  })
}

await mkdir(OUT_DIR, { recursive: true })
for (const f of FILES) {
  const url = `${BASE}/${f}`
  const dest = resolve(OUT_DIR, f)
  process.stdout.write(`拉取 ${f} ... `)
  try {
    await fetchWithRedirect(url, dest)
    process.stdout.write('完成\n')
  } catch (e) {
    process.stdout.write('失败：' + e.message + '\n')
    process.exitCode = 1
  }
}
console.log('字库目录：', OUT_DIR)
