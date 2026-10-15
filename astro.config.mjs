import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';
const site = process.env.SITE_URL || 'https://nishat-info-hub.pages.dev';
const parsed = new URL(site);
if (!['http:', 'https:'].includes(parsed.protocol) || parsed.pathname !== '/' || parsed.search || parsed.hash) throw new Error('SITE_URL must be the site origin, e.g. https://example.com');
export default defineConfig({ site: parsed.origin, trailingSlash: 'always', integrations: [tailwind({ applyBaseStyles: false }), sitemap({ filter: page => !page.endsWith('/404/') })], output: 'static' });
