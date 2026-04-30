# docs-site

`docs-site` 是基于 Astro + Starlight 的静态文档站点，用来承接 `../tnote` 中整理好的 Obsidian 内容，并作为 GitHub / Cloudflare Pages 的发布目录。

## 常用命令

```bash
node -v
pnpm install
pnpm sync
pnpm dev
```

命令说明：

- `pnpm sync`: 从 `../tnote/课程讲义` 同步 Markdown 到 `src/content/docs/`
- `pnpm sync:show`: 查看当前源文件和站点文件的映射关系
- `pnpm dev`: 本地启动站点
- `pnpm build`: 仅构建当前站点内容
- `pnpm build:local`: 先同步，再构建
- `pnpm check`: 运行 Astro 内容检查

运行当前项目前，请确认 `Node.js >= 22.12.0`。

## 目录约定

- `src/content/docs/`: Starlight 实际读取的文档目录
- `mapping.json`: 源文件到站点路由文件名的映射表
- `sync.py`: 同步脚本
- `scripts/run-sync.mjs`: 跨平台同步入口

## Cloudflare Pages

如果把当前 `docs-site` 目录单独推送到 GitHub 仓库，Cloudflare Pages 可使用以下配置：

- Build command: `pnpm install --frozen-lockfile && pnpm build`
- Build output directory: `dist`
- Node.js: 22.12+
