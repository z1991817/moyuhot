import { SITE_DESCRIPTION, SITE_URL } from "../lib/seo";

export function GET(): Response {
  return new Response(
    `# 摸鱼热榜

${SITE_DESCRIPTION}

## 重要页面

- 首页：${SITE_URL}/
- 关于与版权声明：${SITE_URL}/about

## 数据边界

本站只索引公开榜单的标题、平台、排名、热度、更新时间与原站链接，不抓取正文、不缓存图片、不做 AI 摘要。
`,
    {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
      },
    },
  );
}
