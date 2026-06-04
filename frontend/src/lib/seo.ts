export const SITE_NAME = "摸鱼热榜";
export const SITE_KEYWORD_LIST = [
  "热搜平台",
  "热搜聚合",
  "热搜榜",
  "新闻聚合阅读",
  "摸鱼平台",
  "摸鱼网站",
  "今日热搜",
  "实时热榜",
  "微博热搜",
  "知乎热榜",
  "B站热搜",
  "抖音热搜",
  "GitHub Trending",
  "V2EX 热门",
] as const;

export const SITE_KEYWORDS = SITE_KEYWORD_LIST.join(",");
export const SITE_DESCRIPTION =
  "摸鱼热榜是一个热搜平台，聚合微博、知乎、B站、抖音、贴吧、V2EX、GitHub 等热门榜单，提供一站式热搜聚合与新闻聚合阅读入口。";

const runtimeSiteUrl = (
  globalThis as typeof globalThis & {
    process?: { env?: Record<string, string | undefined> };
  }
).process?.env?.PUBLIC_SITE_URL;

export const SITE_URL = (runtimeSiteUrl ?? import.meta.env.PUBLIC_SITE_URL ?? "https://moyuhot.com")
  .replace(/\/+$/, "");

export const DEFAULT_OG_IMAGE = `${SITE_URL}/logo-orange-4-punch.svg`;

export function absoluteUrl(path = "/"): string {
  if (/^https?:\/\//.test(path)) {
    return path;
  }
  return `${SITE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export function jsonLd(data: unknown): string {
  return JSON.stringify(data).replace(/</g, "\\u003c");
}
