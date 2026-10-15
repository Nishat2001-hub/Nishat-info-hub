import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';
import { categories } from './data/categories';
const blankToUndefined = (value: unknown) => value === '' || value === null ? undefined : value;
const optionalUrl = z.preprocess(blankToUndefined, z.string().url().refine(value => /^https?:\/\//.test(value), 'Use an HTTP or HTTPS link').optional());
const articles = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/articles' }),
  schema: z.object({
    title: z.string().min(1), description: z.string().min(1),
    category: z.string().refine(value => categories.includes(value), 'Select a configured category'),
    pubDate: z.coerce.date(),
    updatedDate: z.preprocess(blankToUndefined, z.coerce.date().optional()),
    draft: z.boolean().default(true), featured: z.boolean().default(false),
    featuredOrder: z.number().int().min(0).default(100), trending: z.boolean().default(false),
    image: z.preprocess(blankToUndefined, z.string().refine(value => /^\/(?!\/)/.test(value) || /^https?:\/\//.test(value), 'Use a local image path or HTTP(S) URL').optional()),
    sourceUrl: optionalUrl, applyUrl: optionalUrl,
  }),
});
export const collections = { articles };
