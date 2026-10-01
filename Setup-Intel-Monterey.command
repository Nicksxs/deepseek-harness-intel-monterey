#!/bin/bash
# Download the pinned upstream source, verify it, apply the included patch, and launch.
set -euo pipefail
BASE="$(cd "$(dirname "$0")" && pwd)"
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE
export GIT_CEILING_DIRECTORIES="$BASE"
REVISION=639ed015397290b3745d163aafe02ffee4aa3f84
SOURCE_SHA256=bbc09e888e1df3aa37be049abdb7720951e76442d21e5432365d87a465d628f1
DEST="$BASE/deepseek-harness-intel"
WORK=''
fail() { printf '\n错误：%s\n' "$*" >&2; exit 1; }
cleanup() { if [[ -n "$WORK" && -d "$WORK" ]]; then rm -rf "$WORK"; fi; }
trap cleanup EXIT
trap 'printf "\n操作未完成。请保留错误输出；校验失败时不会运行下载的源码。\n" >&2' ERR
[[ "$(uname -s)" == Darwin && "$(uname -m)" == x86_64 ]] || fail '此包仅面向 Intel Mac。'
[[ ! -e "$DEST" ]] || fail "目录已存在，不会覆盖。后续启动请运行：bash \"$DEST/Start-Intel-Monterey.command\"；若上次准备失败，请检查后自行移走旧目录。"
[[ -f "$BASE/intel-monterey.patch" ]] || fail '找不到随包附带的 intel-monterey.patch，请完整解压 ZIP。'
for tool in curl shasum tar git node pnpm; do
  command -v "$tool" >/dev/null || fail "缺少 $tool，请先按使用说明准备工具。"
done
xcode-select -p >/dev/null 2>&1 || fail '请先完成 Xcode Command Line Tools 安装：xcode-select --install'
node -e 'if(process.arch!=="x64" || process.versions.node.split(".")[0]!=="22" || Number(process.versions.node.split(".")[1])<19)process.exit(1)' || fail '需要 x64 Node.js 22.19 或更新的 22.x；推荐22.23.3。'
[[ "$(pnpm --version)" == 11.7.0 ]] || fail '请准备 pnpm 11.7.0。'
WORK="$(mktemp -d "$BASE/.harness-setup.XXXXXX")"
printf '\n正在从官方 GitHub 下载固定版本源码（约32MB）…\n'
curl --fail --location --proto '=https' --tlsv1.2 --retry 2 --connect-timeout 30 --max-time 600 \
  "https://github.com/deepseek-ai/deepseek-harness/archive/$REVISION.tar.gz" -o "$WORK/source.tar.gz"
printf '%s  %s\n' "$SOURCE_SHA256" "$WORK/source.tar.gz" | shasum -a 256 -c -
mkdir "$WORK/source"
tar -xzf "$WORK/source.tar.gz" --strip-components=1 -C "$WORK/source"
(
  cd "$WORK/source"
  git apply --check "$BASE/intel-monterey.patch"
  git apply "$BASE/intel-monterey.patch"
  printf '%s\n' "$REVISION" > SOURCE_REVISION
)
cp "$BASE/使用说明.txt" "$BASE/VERIFICATION.txt" "$WORK/source/"
# The destination was absent; never overwrite an existing source checkout.
[[ ! -e "$DEST" ]] || fail '准备期间目标目录已出现，已停止，不覆盖文件。'
mv "$WORK/source" "$DEST"
printf '\n源码及补丁准备完成。接下来检查工具、安装项目依赖并编译桌面程序。\n'
bash "$DEST/Start-Intel-Monterey.command"
