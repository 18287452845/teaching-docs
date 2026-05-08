# AGENTS.md

## 项目概述
`docs-site` 是基于 Astro + Starlight 的静态文档站点，用于展示教学文档内容，支持从外部源同步 Markdown 文件。

## 技术栈
- **框架**: Astro 6.1.9 + Starlight 0.38.4
- **运行时**: Node.js >= 22.12.0
- **包管理器**: pnpm 10.33.2
- **构建工具**: Astro (Vite)
- **内容管理**: Starlight 侧边栏导航 + 自动生成

## 目录结构
```
/workspace/projects/
├── .coze                    # Coze 项目配置
├── AGENTS.md               # 本文件
├── astro.config.mjs        # Astro 配置（含 Starlight 集成）
├── package.json            # 依赖和脚本
├── pnpm-lock.yaml          # 锁文件
├── tsconfig.json           # TypeScript 配置
├── public/                 # 静态资源
├── scripts/
│   └── run-sync.mjs        # 内容同步入口
├── src/
│   ├── assets/             # 图片等资源
│   ├── content/
│   │   ├── config.ts       # 内容集合配置
│   │   └── docs/           # 文档目录（Starlight 读取）
│   └── content.config.ts
├── mapping.json            # 源文件到站点路由映射
├── sync.py                 # Python 同步脚本
└── auto-sync.bat           # Windows 自动同步脚本
```

## 关键入口 / 核心模块
- **`pnpm dev`**: 启动 Astro 开发服务器（默认端口 4321）
- **`pnpm build`**: 构建静态站点到 `dist/` 目录
- **`pnpm sync`**: 从外部源同步 Markdown 文档
- **`astro.config.mjs`**: Starlight 配置，定义站点标题和侧边栏

## 运行与预览
- **开发**: `pnpm dev`
- **构建**: `pnpm build`
- **预览构建结果**: `pnpm preview`
- **端口**: Astro 默认 4321，preview 默认 4321

## 用户偏好与长期约束
1. Node.js 版本必须 >= 22.12.0
2. 优先使用 pnpm 管理依赖（已在 packageManager 中锁定）
3. 同步脚本依赖 Python 环境（sync.py）
4. 构建产物为纯静态文件，适合部署到 Cloudflare Pages

## 常见问题和预防
- **同步失败**: 检查 mapping.json 配置是否正确
- **构建报错**: 确认 Node 版本和 pnpm 版本符合要求

## Coze 集成配置

### `.coze` 关键字段
- `project.sub_id`: `30795a90`
- `project.requires`: `["nodejs-22"]`
- `project_type`: `web`
- `preview.preview_enable`: `enabled`

### 预览链路
- **dev.build**: `bash scripts/coze-preview-build.sh` - 安装依赖
- **dev.run**: `bash scripts/coze-preview-run.sh` - 启动 Astro dev server (0.0.0.0:5000)
- **验证方式**: `curl http://localhost:5000` 返回 200

### 部署链路
- **deploy.profile**: `kind=service`, `flavor=web`
- **deploy.build**: `bash scripts/coze-deploy-build.sh` - pnpm install + pnpm build
- **deploy.run**: `bash scripts/coze-deploy-run.sh` - pnpm astro preview (0.0.0.0:5000)

### Coze 专用脚本
```
scripts/
├── coze-preview-build.sh   # 预览构建脚本
├── coze-preview-run.sh     # 预览运行脚本（幂等）
├── coze-deploy-build.sh    # 部署构建脚本
├── coze-deploy-run.sh      # 部署运行脚本（幂等）
└── run-sync.mjs            # 内容同步入口
```

### 端口约束
- 预览和部署统一使用 **5000** 端口
- 禁止使用 9000 端口
