# NISHAT INFO HUB — v1.0

বাংলা তথ্য, চাকরি, প্রযুক্তি ও দাপ্তরিক গাইডের Astro static website।

## Local development

1. Node.js 20.3+ বা 22+ ইনস্টল করুন।
2. `npm install`
3. `npm run dev` — http://localhost:4321
4. `npm run build` — `dist/` তৈরি হবে।
5. `npm run preview` — production build পরীক্ষা।

## GitHub

নতুন GitHub repository তৈরি করে এই প্রজেক্টের **ভেতরের সব ফাইল** (লুকানো `.pages.yml` সহ) আপলোড করুন। সিক্রেট বা পাসওয়ার্ড commit করবেন না।

## Cloudflare Pages

Workers & Pages > Create application > Pages > Connect to Git > GitHub repository নির্বাচন করুন।
Build command: `npm run build`; output directory: `dist`; root directory: `/`।
Deploy হলে `*.pages.dev` ঠিকানা পাবেন।

**Important:** Cloudflare যে URL বরাদ্দ করবে সেটি `astro.config.mjs`-এর fallback URL এবং `public/robots.txt`-এ পরিবর্তন করুন; অথবা Cloudflare-এ `SITE_URL` environment variable দিন এবং `robots.txt`-এ আসল URL দিন। নিজস্ব ডোমেইন যুক্ত হলে একই কাজ করুন।

## Pages CMS

https://app.pagescms.org এ GitHub দিয়ে সাইন ইন করে repository নির্বাচন করুন। `.pages.yml` ফাইলের কারণে `articles` collection দেখতে পাবেন। নতুন আর্টিকেল তৈরি করুন; `draft: false` না করা পর্যন্ত সেটি ওয়েবসাইটে প্রকাশ হবে না। CMS commit হলে Cloudflare স্বয়ংক্রিয়ভাবে পুনরায় deploy করবে।

## Publication checklist

- [ ] নমুনা লেখা যাচাই ও প্রয়োজনমতো প্রতিস্থাপন
- [ ] যোগাযোগের প্রকৃত তথ্য যুক্ত করা
- [ ] সরকারি তথ্যের মূল উৎস, তারিখ ও সংশোধনী যাচাই
- [ ] গোপনীয়তা নীতি বাস্তব analytics/ad ব্যবহারের সঙ্গে সামঞ্জস্য করা
- [ ] favicon, logo, og-image প্রয়োজনমতো পরিবর্তন
- [ ] sitemap, robots, canonical-এ প্রকৃত URL যাচাই
- [ ] AdSense-এর আগে policy compliance ও original content যাচাই

## Limitations

নমুনা কনটেন্ট বাস্তব নিয়োগ বিজ্ঞপ্তি নয়। Google AdSense অনুমোদন বা আয় নিশ্চিত নয়। Static search কেবল প্রকাশিত আর্টিকেলের শিরোনাম/বিবরণে কাজ করে।


## Version 1.1 homepage changes
- Editorial lead story, manually curated via `featured: true` and `featuredOrder: 1`.
- Trending section via `trending: true`; falls back to newest published posts.
- Category grid moved below trending.
- Mobile menu uses native `<details>` without JavaScript.
- Future-dated posts and drafts excluded from homepage.
- Existing `/articles/<slug>/` paths retained.
- All current posts are illustrative educational examples, not breaking news.
- CMS article fields: featured, featuredOrder, trending.


## V1.2 — Page transitions

- On the first visit in a browser tab, a brief NISHAT INFO HUB logo introduction appears.
- Internal page navigation uses a subtle transition overlay.
- `prefers-reduced-motion` disables decorative animation.
- No paid service or additional dependency.
- Transition code is in `src/layouts/Base.astro`.
- GitHub mobile upload note: GitHub's mobile browser file picker often cannot upload directory trees. Use a desktop browser with drag-and-drop, GitHub's web editor where supported, or a Git client that preserves folders. Do not flatten `src/` and `public/` into the repository root.
