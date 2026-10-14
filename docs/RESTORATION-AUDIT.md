# Restoration audit

## Baseline

The repository main commit `105ada75d491d654463ae4d13e5a12584d903953` contained only README.md, package.json, astro.config.mjs, tailwind.config.mjs, tsconfig.json and a misplaced root content.config.ts. It had no source routes, layouts, article content, CMS configuration or public assets.

The authoritative attachment is `NISHAT_INFO_HUB_V1_2_TRANSITIONS.zip`. It differs from the earlier V1.1 archive only in README.md and Base.astro. All eight original articles are restored byte for byte; their SHA-256 hashes are recorded in tests/original-content.json. The one-time `npm run test:restoration` audit verifies these hashes; it is deliberately excluded from ongoing CI so legitimate CMS edits remain possible. All original routes are retained.

## Repairs and completion

- Restore missing src/, public/, .pages.yml and .gitignore; Astro discovers the collection in src/content.config.ts. The root entry re-exports it for compatibility.
- Preserve the V1.2 first-tab logo intro intent and replace click-delay navigation with Astro ClientRouter transitions. Search and theme listeners initialize on each route change; reduced motion and missing browser storage are supported.
- Centralize publication filtering so drafts and future articles are not built into archive or direct article routes.
- Correct footer category links to the article filter. Enable Tailwind typography and display CMS images on cards/articles.
- Add responsive navigation, dark mode, skip link, keyboard focus, ticker pause, live search result status, SEO metadata, JSON-LD and generated robots.txt.
- Retain the featured/trending editorial model and original category list. CMS includes contact settings; optional empty fields are accepted and external links require HTTP(S).
- Add CI for installation, Astro/TypeScript checks, production build, local link checks, content preservation and Playwright interaction/preview tests.

## Verification

Local content-preservation and route-source checks pass. Local dependency installation initially failed because the execution sandbox cannot connect to its network proxy; `npm run build` consequently reported `astro: not found`. See the PR checks for subsequent CI validation. A successful source check alone does not establish a successful production build.

No production deployment, merge or content deletion is part of this change. Contact details remain unset until supplied by the owner. Static future-dated publication requires a rebuild after the date arrives.
