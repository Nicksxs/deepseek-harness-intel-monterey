# Third-party notices

This repository distributes a patch against DeepSeek Harness and a bootstrap script. It does not bundle Electron, Node.js, Python, LibreOffice, npm dependencies, or application binaries.

## DeepSeek Harness

- Upstream: https://github.com/deepseek-ai/deepseek-harness
- Pinned revision: `639ed015397290b3745d163aafe02ffee4aa3f84`
- License: MIT, Copyright (c) 2026 DeepSeek; the complete notice is retained in [LICENSE](LICENSE)
- Original third-party notices: https://github.com/deepseek-ai/deepseek-harness/blob/639ed015397290b3745d163aafe02ffee4aa3f84/THIRD_PARTY_NOTICES.md

The patch contains modified excerpts of upstream MIT-licensed code and documentation. The bootstrap downloads the complete upstream source, retaining its LICENSE, THIRD_PARTY_NOTICES.md, vendored licenses, and dependency manifests. Their licenses remain applicable. The adapter's MIT license does not relicense any third-party package.

## Downloaded runtimes and dependencies

Electron, Node.js, Python, LibreOffice and other packages retain their own license notices. The patched upstream pnpm lockfile records the Electron version and dependency closure; scripts/primary-runtime/lock.json records standalone runtime hashes. When redistributing a built application, preserve the licenses and notices for everything included in that build. This repository supplies no prebuilt distribution or claim that all binary redistribution obligations have been independently audited.

DeepSeek and other product names identify compatibility targets. This project is unofficial and is not endorsed by their owners.
