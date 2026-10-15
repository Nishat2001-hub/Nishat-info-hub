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

Local one-time content preservation and route-source checks passed. GitHub Actions completed npm install, npm ci, Astro/TypeScript checks (0 errors, 0 warnings), a 17-page production build, internal link/asset/metadata tests, draft/future publication regression tests and five Playwright tests, including automated WCAG A/AA checks on the homepage and article page in light and dark modes. Desktop, mobile, dark screenshots and built output are in the CI artifact.

Validation run: https://github.com/Nishat2001-hub/Nishat-info-hub/actions/runs/38611514999

The local sandbox could not connect to its network proxy, so dependency installation, build and browser validation were performed in GitHub Actions, not falsely reported as a local success.

## Dependency audit limitation

`npm audit` reports 12 advisories in the required Astro 5 / Tailwind 3 dependency tree (1 critical, 6 high, 4 moderate, 1 low). npm recommends a major Astro 7 / Tailwind 4 migration for the complete fix; that would change the requested stack. The full JSON report is included in CI artifacts. The audit step records these findings and is non-blocking; a green build does not mean the dependency audit is clean.

This project builds static HTML, has no deployed Astro server, server islands, SSR authorization or image-optimization endpoint, and displays uploads as ordinary images. These boundaries limit exposure but do not amount to a blanket assurance that all advisories are inapplicable. Keep the development server private, review advisories before production approval, and plan a supported framework upgrade separately. No forced major upgrade has been made.

No production deployment, merge or content deletion is part of this change. Contact details remain unset until supplied by the owner. Static future-dated publication requires a rebuild after the date arrives.
