# NISHAT INFO HUB — V1.2 সম্পূর্ণ পোর্টাল

Astro 5, TypeScript, Tailwind CSS, Pages CMS ও Cloudflare Pages-এর static বাংলা তথ্য পোর্টাল। মূল V1.2 ZIP-এর আটটি লেখা ও সব route রাখা হয়েছে। নতুন সরকারি খবর বা নিয়োগ বিজ্ঞপ্তি যোগ করা হয়নি।

## নিজের কম্পিউটারে চালানো

Node.js 22 LTS ব্যবহার করুন।

```sh
npm install
npm run check
npm run build
npm test
npm run test:publication
npx playwright install chromium
npm run test:browser
npm run dev
```

মূল ZIP-এর article অপরিবর্তিত আছে কি না দেখতে `npm run test:restoration` চালানো যায়। এটি শুধু restoration audit-এর জন্য; পরবর্তী CMS সম্পাদনার পরে hash বদলানো স্বাভাবিক, তাই নিয়মিত CI-তে এই পরীক্ষা চলে না।

ব্রাউজারে `http://localhost:4321` খুলুন। Production build দেখার জন্য `npm run preview` চালান। Browser test থেকে `preview/home-desktop.png`, `preview/home-mobile.png`, `preview/home-dark.png` তৈরি হয়। GitHub Actions-এর `portal-preview-and-validation` artifact-এ preview ও build পাওয়া যাবে।

## Cloudflare Pages সংযোগ

**আপনি প্রকাশের অনুমোদন দেওয়ার পরই নিচের deployment ধাপগুলো করুন।** এই পরিবর্তনে production deploy বা main branch merge করা হয়নি।

1. GitHub PR-এর preview ও checks দেখুন। সব ঠিক থাকলে PR merge করুন।
2. Cloudflare dashboard → Workers & Pages → Create application → Pages → Connect to Git নির্বাচন করুন।
3. GitHub account যুক্ত করে `Nishat2001-hub/Nishat-info-hub` repository বেছে নিন।
4. Production branch `main`, framework `Astro`, build command `npm run build`, output directory `dist`, root directory খালি রাখুন।
5. Environment variables-এ `NODE_VERSION=22` এবং `SITE_URL=https://আপনার-আসল-ডোমেইন` দিন। `SITE_URL`-এ path বা query দেবেন না। Cloudflare-এর বরাদ্দ করা `.pages.dev` URL-ও ব্যবহার করা যায়।
6. Save and Deploy চাপলে প্রকাশ হবে। সাইট, `/sitemap-index.xml`, `/robots.txt`, article link ও mobile menu পরীক্ষা করুন।
7. Custom domain যোগ করলে `SITE_URL` বদলে আবার build/deploy করুন। Canonical, sitemap ও robots একই ঠিকানা ব্যবহার করবে।

Preview branch চালু থাকলে development branch-এর জন্য আলাদা preview deployment হতে পারে। Production branch হিসেবে development branch বাছবেন না। Cloudflare static hosting-এর জন্য Worker adapter, database বা paid service লাগবে না।

## কোড ছাড়াই লেখা প্রকাশ — Pages CMS

1. https://app.pagescms.org এ GitHub দিয়ে লগইন করুন। এই repository এবং সঠিক branch নির্বাচন করুন। PR review চলাকালে development branch ব্যবহার করুন; অনুমোদিত production publication-এর জন্য `main`।
2. **আর্টিকেল → New entry** চাপুন। ছোট, স্থায়ী filename/slug দিন, যেমন `office-guide`। Publish করার পর filename বদলালে URL বদলে যাবে।
3. শিরোনাম, সংক্ষিপ্ত বিবরণ, বিভাগ, প্রকাশের তারিখ ও বিস্তারিত লিখুন। Media picker দিয়ে ছবি upload করতে পারেন। ছবি `public/uploads`-এ থাকে।
4. **প্রধান খবর** চালু করলে Featured অংশে আসবে। **প্রধান খবরের ক্রম**-এ ছোট সংখ্যা আগে: `1` প্রধান বড় প্রতিবেদন, পরেরগুলো পাশে।
5. **আলোচিত বিষয়** চালু করলে Trending অংশে আসবে। এটি সম্পাদক নির্বাচিত তালিকা; পাঠকের সংখ্যা মাপা হয় না। কোনো নির্বাচিত লেখা না থাকলে সর্বশেষ প্রকাশিত লেখা দেখায়।
6. যাচাই শেষ হলে **খসড়া** বন্ধ করে Save করুন। নতুন লেখা শুরুতে খসড়া থাকে। ভবিষ্যতের তারিখের লেখা build-এর সময় বাদ যায়।
7. CMS save GitHub commit তৈরি করে। Cloudflare সংযুক্ত থাকলে ওই branch অনুযায়ী rebuild হবে। Static site হওয়ায় ভবিষ্যতের তারিখ পার হলেই স্বয়ংক্রিয়ভাবে লেখা প্রকাশ হয় না: সেদিন নতুন build/retry deployment চালাতে হবে।
8. সরকারি তথ্যের জন্য **মূল উৎসের লিংক** এবং প্রযোজ্য হলে **আবেদন লিংক** দিন; প্রকৃত কর্তৃপক্ষের প্রকাশনা যাচাই করুন। এগুলো ঐচ্ছিক।
9. **সাইটের যোগাযোগ** থেকে প্রকৃত ইমেইল ও Facebook URL দিন। কোনো কাল্পনিক যোগাযোগের তথ্য রাখা হয়নি।

## কী কাজ করে

- Featured, Trending, pause করা যায় এমন সর্বশেষ লেখার ticker, তারপর category grid ও latest posts।
- Bengali search ও category filter; query URL-এ থাকে, back navigation-এ বজায় থাকে।
- System preference ও সংরক্ষিত পছন্দ অনুযায়ী dark mode; keyboard ও mobile navigation।
- Browser tab-এ প্রথমবার সংক্ষিপ্ত logo intro; Astro ClientRouter page transition। Reduced-motion preference-এ decorative animation বন্ধ। JavaScript ছাড়া মূল লেখা ও menu ব্যবহার করা যায়।
- SEO metadata, canonical, Article structured data, sitemap, generated robots.txt, favicon ও share image।
- Draft/future content homepage, archive, article routes ও sitemap থেকে বাদ।

## Structure ও audit

`src/content/articles/` মূল কনটেন্ট; `src/pages/` routes; `src/layouts/Base.astro` layout; `src/styles/global.css` styles; `.pages.yml` CMS configuration। `docs/RESTORATION-AUDIT.md`-এ restoration ও পরীক্ষা সংক্রান্ত তথ্য আছে। মূল V1.2 README `docs/V1.2-ORIGINAL-README.md`-এ সংরক্ষিত।

বর্তমান লেখাগুলো মূল source-এর শিক্ষামূলক নমুনা। প্রকাশের আগে আপনার সম্পাদকীয় যাচাই এবং প্রকৃত যোগাযোগের তথ্য প্রয়োজন। কোনো analytics, বিজ্ঞাপন বা paid service যোগ করা হয়নি।
