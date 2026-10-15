import { getCollection, type CollectionEntry } from 'astro:content';
export type Article = CollectionEntry<'articles'>;
export const isPublished = ({ data }: Pick<Article, 'data'>, now = Date.now()) => !data.draft && data.pubDate.getTime() <= now;
export async function publishedArticles() { return (await getCollection('articles')).filter(a => isPublished(a)).sort((a,b) => b.data.pubDate.getTime() - a.data.pubDate.getTime()); }
export const articlePath = (article: Article) => `/articles/${article.id}/`;
