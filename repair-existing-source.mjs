/** Repair only the known launcher ordering in an existing pinned source directory. */
import { constants, copyFileSync, readFileSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'

try {
  if (process.argv.length !== 3) throw new Error('用法：node repair-existing-source.mjs "已有的 deepseek-harness-intel 目录"')
  const directory = resolve(process.argv[2])
  if (readFileSync(join(directory, 'SOURCE_REVISION'), 'utf8').trim() !== '639ed015397290b3745d163aafe02ffee4aa3f84') {
    throw new Error('源码版本不匹配，未修改任何文件。')
  }
  const path = join(directory, 'Start-Intel-Monterey.command')
  const source = readFileSync(path, 'utf8')
  const fixed = '# Build workspace exports before loading the Desktop launcher.\npnpm run build\npnpm run start:desktop\n'
  if (source.endsWith(fixed)) {
    console.log('启动顺序已经修复，无需修改。')
  } else {
    const original = 'pnpm run dev:desktop\n'
    if (!source.endsWith(original) || source.split(original).length !== 2) {
      throw new Error('启动脚本与已知版本不同，未覆盖你的修改。')
    }
    copyFileSync(path, `${path}.before-build-order-fix`, constants.COPYFILE_EXCL)
    writeFileSync(path, source.slice(0, -original.length) + fixed)
    console.log('已修复启动顺序并保留原脚本备份。未下载源码、安装依赖或启动应用。')
    console.log('现在可在原源码目录运行：bash ./Start-Intel-Monterey.command')
  }
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error))
  process.exitCode = 1
}
