import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';
const articles=defineCollection({loader:glob({pattern:'**/*.md',base:'./src/content/articles'}),schema:z.object({title:z.string(),description:z.string(),category:z.string(),pubDate:z.coerce.date(),updatedDate:z.coerce.date().optional(),draft:z.boolean().default(false),featured:z.boolean().default(false),featuredOrder:z.number().int().min(0).default(100),trending:z.boolean().default(false),image:z.string().optional(),sourceUrl:z.string().url().optional(),applyUrl:z.string().url().optional()})});
export const collections={articles};
