// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
  site: 'https://docs-site.pages.dev',
  output: 'static',
  integrations: [
    starlight({
      title: '教学文档',
      defaultLocale: 'zh-CN',
      locales: {
        'zh-CN': { label: '简体中文', lang: 'zh-CN' },
      },
      sidebar: [
        {
          label: 'Windows 服务器安全配置',
          autogenerate: { directory: 'Windows 服务器安全配置' },
        },
        {
          label: '数据库系统管理和运维',
          autogenerate: { directory: '数据库系统管理和运维' },
        },
      ],
      lastUpdated: true,
    }),
  ],
});
