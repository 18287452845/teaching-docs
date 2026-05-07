// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
  site: 'https://teaching-docs.pages.dev',
  output: 'static',
  image: {
    service: {
      entrypoint: 'astro/assets/services/noop',
    },
  },
  integrations: [
    starlight({
      title: '教学文档',
      sidebar: [
        {
          label: 'Windows 服务器安全配置',
          autogenerate: { directory: 'windows-server-security' },
        },
        {
          label: '数据库系统管理和运维',
          autogenerate: { directory: 'database-admin' },
        },
      ],
      lastUpdated: true,
    }),
  ],
});
