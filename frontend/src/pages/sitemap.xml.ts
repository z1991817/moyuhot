import { SITE_URL } from "../lib/seo";

const staticRoutes = [
  { path: "/", changefreq: "daily", priority: "1.0" },
  { path: "/about", changefreq: "monthly", priority: "0.5" },
  { path: "/ui-new/a-share", changefreq: "daily", priority: "0.8" },
  { path: "/ui-new/finance", changefreq: "daily", priority: "0.8" },
  { path: "/ui-new/about", changefreq: "monthly", priority: "0.5" },
];

function xmlEscape(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function GET(): Response {
  const lastmod = new Date().toISOString().slice(0, 10);
  const urls = staticRoutes
    .map(
      (route) => `  <url>
    <loc>${xmlEscape(`${SITE_URL}${route.path}`)}</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>${route.changefreq}</changefreq>
    <priority>${route.priority}</priority>
  </url>`,
    )
    .join("\n");

  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`,
    {
      headers: {
        "Content-Type": "application/xml; charset=utf-8",
      },
    },
  );
}
