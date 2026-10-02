# DeepSeek Harness Intel Monterey 适配补丁

非官方、实验性的 DeepSeek Harness 桌面源码适配层，目标是 Intel Mac 和 macOS Monterey 12.6.6。它不是 DeepSeek 官方发行版，也不是已经实机验证、可直接安装的 DMG。

本仓库仅提供补丁和下载启动脚本。完整源码从官方 GitHub 的固定提交下载，校验 SHA256 后应用补丁并本地构建。未经 macOS 实机验证，不保证所有功能可用。

## 解决什么

- 桌面 Electron 固定为 **43.7.7**。Electron 44 已停止支持 macOS 12
- 仅 `mac-x64` 独立 Node 运行环境固定为 **22.23.3**；其他平台保留上游24.21.0。Node24 macOS二进制要求13.5+
- 修复生成的开发版 `.app` 从 Finder 冷启动时遗漏主运行环境目录的问题
- 提供中文工具检查、校验和启动流程；不自动安装系统工具，不关闭 Gatekeeper，不移除上游签名、公证或更新保护

Electron 固定会影响这份源码副本的所有桌面构建。此适配层面向 Intel Monterey，其他系统应优先使用官方版本。

## 使用

先自行准备：

1. 完整 x64 **Node.js 22.23.3**（最低22.19，同属22.x），包含 `include/node/node_api.h`。从 [Node官方目录](https://nodejs.org/dist/v22.23.3/) 获取完整发行版，不要只复制一个 node 可执行文件
2. **pnpm 11.7.0**。安装 Node 后可执行 `npm install -g pnpm@11.7.0`
3. **Xcode Command Line Tools** 和 Git。缺少时先执行 `xcode-select --install` 并完成系统安装提示
4. 网络和足够磁盘空间；首次需要下载约32MB源码，以及更大的项目依赖和运行环境

下载本仓库 ZIP 并完整解压，或克隆本仓库。在终端进入本仓库目录后运行：

```sh
bash ./Setup-Intel-Monterey.command
```

也可以双击该 `.command` 文件；如果 Finder 的 PATH 找不到 Node/pnpm，请改用已配置工具的终端。

脚本在本仓库下创建 `deepseek-harness-intel`，不覆盖已有目录。源码下载、校验和补丁应用成功后，它安装项目依赖、编译并启动桌面程序。编译失败时保留终端完整错误输出；后续从已准备的源码目录重试：

```sh
bash ./deepseek-harness-intel/Start-Intel-Monterey.command
```

首次成功构建后可打开：

```text
deepseek-harness-intel/apps/desktop/.desktop-build/development/Harness Dev.app
```

这是依赖源码的开发版 `.app`。不要单独复制 `.app`，或移动、删除源码目录、node_modules和运行环境。首次使用在界面中配置账号或 API Key；不要将密钥提交到仓库。更多说明见[使用说明](使用说明.txt)。

## 已下载源码的启动顺序修复

若旧版在 `tsx scripts/dev.ts` 报 `ERR_MODULE_NOT_FOUND`，指向 `@deepseek-ai/dsh-app-boot/lib/index.js`，原因是桌面开发启动器在执行自己的构建步骤之前，就静态导入了尚未生成的工作区产物。启动脚本现在先完成一次根目录 `pnpm run build`，再用 `pnpm run start:desktop` 跳过重复构建并启动。构建失败时不会继续启动。

无需重新下载源码。更新本适配仓库后，可只修复已有的启动脚本：

```sh
node ./repair-existing-source.mjs "/path/to/deepseek-harness-intel"
```

修复工具核对固定源码版本，只替换已知旧脚本的最后一条启动命令，保留其他内容与执行权限，并创建 `.before-build-order-fix` 备份；未知版本、不同启动命令或已有备份会停止，不覆盖。重复修复已完成的脚本不会产生改动。它不安装依赖、不启动应用。随后在原源码目录运行 `bash ./Start-Intel-Monterey.command`。

安装阶段列出的其他CPU或操作系统工作区的 `Unsupported platform` 警告，不等同于这次缺失构建产物错误。Node22.23.2满足本适配要求的22.19+，无需为了该错误升级到22.23.3。

## 固定来源与校验

- 上游：[deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)
- 提交：`639ed015397290b3745d163aafe02ffee4aa3f84`
- [固定源码归档](https://github.com/deepseek-ai/deepseek-harness/archive/639ed015397290b3745d163aafe02ffee4aa3f84.tar.gz)
- 归档 SHA256：`bbc09e888e1df3aa37be049abdb7720951e76442d21e5432365d87a465d628f1`
- Node22.23.3 darwin-x64归档SHA256：`8a677b0219178efd6eb0e475457c4afb452b521a92f6e67845a73bd85727f2a8`

若官方重新生成归档导致校验失败，脚本会停止。不要跳过校验；更新固定值前应重新核对完整来源和补丁。补丁可在 [intel-monterey.patch](intel-monterey.patch) 中审查。

## 验证状态

| 检查 | 结果 |
| --- | --- |
| 固定归档SHA256及真实源码补丁应用 | 通过 |
| 运行环境、Finder启动变量及打包目标单元测试 | 30项通过，Linux执行 |
| Host TypeScript（Electron43类型） | 通过，4GB堆 |
| 针对性lint、JSDoc、文档配对及相对链接 | 通过 |
| 脚本语法、模拟Mac准备路径、已有目录/坏校验拒绝 | 通过 |
| 完整应用构建 | 未完成；验证环境的tsx IPC被沙箱阻止 |
| macOS12.6.6实机UI、原生模块、Python及LibreOffice | 未验证 |
| 签名、公证、DMG及升级安装 | 未验证，未提供 |

完整记录见 [VERIFICATION.txt](VERIFICATION.txt)。模拟平台测试不是Mac实机测试。不要据此宣称生产可用。

## 安全与维护

- 上游开发模式保留本机调试端口，关闭DevTools窗口不等于关闭调试端口；不要暴露到不可信网络
- 这是旧系统兼容方案，不承诺长期安全维护。应跟踪Electron43的安全更新和生命周期；系统升级后优先使用受支持的官方客户端
- 运行前阅读上游[安全说明](https://github.com/deepseek-ai/deepseek-harness/blob/639ed015397290b3745d163aafe02ffee4aa3f84/SAFETY.md)
- 不要在issue、日志或补丁中包含API Key、账号token、个人目录内容或其他私密信息

兼容性依据：[Electron44发布说明](https://www.electronjs.org/blog/electron-44-0)、[Node24迁移说明](https://nodejs.org/en/blog/migrations/v22-to-v24)、[Node22平台支持](https://github.com/nodejs/node/blob/v22.x/BUILDING.md)。

## 开发与贡献

运行 `/bin/bash -n Setup-Intel-Monterey.command` 检查语法，运行 `python3 tests/test_shell_guards.py` 测试缺少工具的错误提示和变量边界（无需下载源码）。测试使用 `/bin/bash`，以覆盖 macOS 系统自带的 Bash，而不是其他已安装版本。可将经校验的官方归档路径传给测试程序：

```sh
python3 tests/test_bootstrap.py /path/to/639ed015397290b3745d163aafe02ffee4aa3f84.tar.gz
```

测试不下载依赖、不构建应用；平台与构建工具使用隔离的模拟程序，SHA256、解压和补丁应用使用真实工具。提交改动时请说明macOS版本、CPU、命令、结果和未验证范围。不要添加签名凭证或已生成的应用包。

## 许可证

此适配层使用 [MIT](LICENSE)；保留DeepSeek上游版权与许可文本。第三方依赖的许可不因此改变，见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。本仓库没有第三方二进制。若分发构建产物，请保留它们自身的许可和通知。
