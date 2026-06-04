import type { HomeResponse, Trend } from "./types";

export type UiNewBoard = {
  platform: string;
  platformName: string;
  items: Trend[];
  updatedAt: string;
  iconUrl: string | null;
  desc: string;
  themeColor: string;
};

export type UiNewCategoryId =
  | "frequent"
  | "general"
  | "tech"
  | "community";

export type UiNewBoardGroup = {
  id: UiNewCategoryId;
  label: string;
  boards: UiNewBoard[];
};

type UiNewMeta = {
  iconUrl: string | null;
  desc: string;
  themeColor: string;
};

const PLATFORM_ORDER = [
  "weibo",
  "zhihu",
  "bilibili-hot-search",
  "douyin",
  "juejin",
  "github-trending-today",
  "hupu",
  "tieba",
  "douban",
  "baidu",
  "v2ex",
  "linux-do",
  "toutiao",
  "thepaper",
  "wallstreetcn-hot",
  "cls-hot",
  "jin10",
  "kuaishou",
  "tencent-hot",
  "ifeng",
  "36kr-renqi",
  "ithome",
  "sspai",
  "coolapk",
  "gelonghui",
  "xueqiu-hotstock",
  "nowcoder",
  "hackernews",
  "producthunt",
  "freebuf",
  "steam",
] as const;

const PLATFORM_META: Record<string, UiNewMeta> = {
  weibo: { iconUrl: "/ui-new/icons/weibo.svg", desc: "全网公共话题、娱乐和社会热点", themeColor: "#E6162D" },
  zhihu: { iconUrl: "/ui-new/icons/zhihu.svg", desc: "深度讨论、问答和观点趋势", themeColor: "#0084FF" },
  "bilibili-hot-search": { iconUrl: "/ui-new/icons/bilibili.svg", desc: "视频内容、知识区和年轻人关注", themeColor: "#00A1D6" },
  douyin: { iconUrl: "/ui-new/icons/douyin.svg", desc: "短视频热点、生活方式和实时流行", themeColor: "#000000" },
  juejin: { iconUrl: "/ui-new/icons/juejin.svg", desc: "开发者文章、前端后端与工程化", themeColor: "#007FFF" },
  "github-trending-today": { iconUrl: "/ui-new/icons/github.svg", desc: "开源项目、工具库和技术趋势", themeColor: "#181717" },
  v2ex: { iconUrl: "/ui-new/icons/v2ex.png", desc: "技术社区、分享和节点讨论", themeColor: "#1F1F1F" },
  "linux-do": { iconUrl: "/ui-new/icons/linux-do.png", desc: "开发者社区、AI 工具和热门讨论", themeColor: "#FFB000" },
  hupu: { iconUrl: "/ui-new/icons/hupu.ico", desc: "体育、社区和步行街话题", themeColor: "#C01E2E" },
  tieba: { iconUrl: "/ui-new/icons/tieba.ico", desc: "贴吧热议、兴趣圈层和老牌社区", themeColor: "#3385FF" },
  douban: { iconUrl: "/ui-new/icons/douban.svg", desc: "书影音、小组和生活讨论", themeColor: "#2D963D" },
  baidu: { iconUrl: "/ui-new/icons/baidu.svg", desc: "搜索趋势、公共事件和实时关注", themeColor: "#2932E1" },
  toutiao: { iconUrl: "/ui-new/icons/toutiao.ico", desc: "资讯推荐、社会热点和综合热榜", themeColor: "#D81E06" },
  kuaishou: { iconUrl: "/ui-new/icons/kuaishou.svg", desc: "短视频热点和社区流行内容", themeColor: "#FF4906" },
  thepaper: { iconUrl: "/ui-new/icons/thepaper.ico", desc: "新闻现场、深度报道和公共议题", themeColor: "#ED1C24" },
  "36kr-renqi": { iconUrl: "/ui-new/icons/36kr.ico", desc: "商业、创投和公司动态", themeColor: "#1E88E5" },
  ithome: { iconUrl: "/ui-new/icons/ithome.ico", desc: "科技资讯、数码产品和行业新闻", themeColor: "#D81E06" },
  "wallstreetcn-hot": { iconUrl: "/ui-new/icons/wallstreetcn.png", desc: "财经市场、宏观和公司热点", themeColor: "#0B3A75" },
  "cls-hot": { iconUrl: "/ui-new/icons/cls.ico", desc: "财经快讯、市场和公司事件", themeColor: "#C80000" },
  jin10: { iconUrl: "/ui-new/icons/jin10.ico", desc: "金融数据、市场消息和宏观日历", themeColor: "#D4A017" },
  sspai: { iconUrl: "/ui-new/icons/sspai.ico", desc: "效率工具、数字生活和应用推荐", themeColor: "#D71920" },
  coolapk: { iconUrl: "/ui-new/icons/coolapk.ico", desc: "数码应用、安卓生态和社区讨论", themeColor: "#11AA66" },
  gelonghui: { iconUrl: "/ui-new/icons/gelonghui.ico", desc: "港美股、研报和财经观察", themeColor: "#1D6FEA" },
  "xueqiu-hotstock": { iconUrl: "/ui-new/icons/xueqiu.ico", desc: "热门股票、投资社区和市场情绪", themeColor: "#1E88E5" },
  nowcoder: { iconUrl: "/ui-new/icons/nowcoder.ico", desc: "求职面试、刷题和技术讨论", themeColor: "#25BB9B" },
  ifeng: { iconUrl: "/ui-new/icons/ifeng.ico", desc: "资讯热点、社会话题和综合新闻", themeColor: "#E60012" },
  "tencent-hot": { iconUrl: "/ui-new/icons/tencent-news.ico", desc: "腾讯新闻、综合热点和公共议题", themeColor: "#0052D9" },
  hackernews: { iconUrl: "/ui-new/icons/hackernews.ico", desc: "创业、工程和海外科技讨论", themeColor: "#FF6600" },
  producthunt: { iconUrl: "/ui-new/icons/producthunt.svg", desc: "新产品、工具和创业项目", themeColor: "#DA552F" },
  freebuf: { iconUrl: "/ui-new/icons/freebuf.ico", desc: "网络安全、漏洞和攻防资讯", themeColor: "#E64340" },
  steam: { iconUrl: "/ui-new/icons/steam.svg", desc: "游戏热度、在线人数和玩家趋势", themeColor: "#000000" },
};

const DEFAULT_THEME_COLOR = "#10B981";

const CATEGORY_ORDER: UiNewCategoryId[] = [
  "frequent",
  "tech",
  "community",
  "general",
];

const CATEGORY_META: Record<UiNewCategoryId, Pick<UiNewBoardGroup, "label">> = {
  frequent: { label: "综合" },
  general: { label: "资讯财经" },
  tech: { label: "科技" },
  community: { label: "社区" },
};

const PLATFORM_CATEGORY: Record<string, UiNewCategoryId> = {
  weibo: "frequent",
  zhihu: "frequent",
  douyin: "frequent",
  "bilibili-hot-search": "frequent",
  baidu: "frequent",
  hupu: "frequent",
  v2ex: "frequent",
  "linux-do": "frequent",
  toutiao: "general",
  thepaper: "general",
  ifeng: "general",
  kuaishou: "community",
  "tencent-hot": "general",
  steam: "community",
  juejin: "tech",
  "github-trending-today": "tech",
  ithome: "tech",
  sspai: "tech",
  coolapk: "tech",
  nowcoder: "tech",
  hackernews: "tech",
  producthunt: "tech",
  freebuf: "tech",
  "36kr-renqi": "general",
  "wallstreetcn-hot": "general",
  "cls-hot": "general",
  jin10: "general",
  gelonghui: "general",
  "xueqiu-hotstock": "general",
  douban: "community",
  tieba: "community",
};

export function buildUiNewBoards(data: HomeResponse): UiNewBoard[] {
  const grouped = data.trends.reduce<Record<string, Trend[]>>((acc, item) => {
    const items = acc[item.platform] ?? [];
    items.push(item);
    acc[item.platform] = items;
    return acc;
  }, {});

  const known = PLATFORM_ORDER.flatMap((platform) => {
    const items = grouped[platform] ?? [];
    if (items.length === 0) return [];
    const meta = PLATFORM_META[platform] ?? { iconUrl: null, desc: "公开榜单数据", themeColor: DEFAULT_THEME_COLOR };
    return [{
      platform,
      platformName: items[0]?.platformName ?? platform,
      items,
      updatedAt: items[0]?.updatedAt ?? data.updatedAt,
      iconUrl: meta.iconUrl,
      desc: meta.desc,
      themeColor: meta.themeColor,
    }];
  });

  const rest = Object.entries(grouped)
    .filter(([platform]) => !PLATFORM_ORDER.includes(platform as (typeof PLATFORM_ORDER)[number]))
    .map(([platform, items]) => ({
      platform,
      platformName: items[0]?.platformName ?? platform,
      items,
      updatedAt: items[0]?.updatedAt ?? data.updatedAt,
      iconUrl: null,
      desc: "公开榜单数据",
      themeColor: DEFAULT_THEME_COLOR,
    }));

  return [...known, ...rest];
}

export function groupUiNewBoards(boards: UiNewBoard[]): UiNewBoardGroup[] {
  const grouped = boards.reduce<Record<UiNewCategoryId, UiNewBoard[]>>(
    (acc, board) => {
      const category = PLATFORM_CATEGORY[board.platform] ?? "general";
      acc[category].push(board);
      return acc;
    },
    {
      frequent: [],
      general: [],
      tech: [],
      community: [],
    }
  );

  return CATEGORY_ORDER.flatMap((id) => {
    const categoryBoards = grouped[id];
    if (categoryBoards.length === 0) return [];
    return [{ id, ...CATEGORY_META[id], boards: categoryBoards }];
  });
}

export function formatUiNewTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "--:--";
  return date.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export function formatUiNewHeat(heat: string | undefined, rank: number): string {
  return heat && heat.trim().length > 0 ? heat : `TOP ${rank}`;
}
