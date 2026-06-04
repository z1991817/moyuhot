from __future__ import annotations

from dataclasses import dataclass

from app.config import settings


@dataclass(frozen=True)
class PlatformMeta:
    platform: str
    platform_name: str


PLATFORMS: dict[str, PlatformMeta] = {
    # 社交娱乐
    "weibo": PlatformMeta(platform="weibo", platform_name="微博热搜"),
    "douyin": PlatformMeta(platform="douyin", platform_name="抖音热点"),
    "kuaishou": PlatformMeta(platform="kuaishou", platform_name="快手热榜"),
    "bilibili-hot-search": PlatformMeta(platform="bilibili-hot-search", platform_name="B站热搜"),
    "douban": PlatformMeta(platform="douban", platform_name="豆瓣热门"),
    "hupu": PlatformMeta(platform="hupu", platform_name="虎扑步行街"),
    # 资讯新闻
    "toutiao": PlatformMeta(platform="toutiao", platform_name="今日头条"),
    "baidu": PlatformMeta(platform="baidu", platform_name="百度热搜"),
    "thepaper": PlatformMeta(platform="thepaper", platform_name="澎湃新闻"),
    "ifeng": PlatformMeta(platform="ifeng", platform_name="凤凰网"),
    "tencent-hot": PlatformMeta(platform="tencent-hot", platform_name="腾讯新闻"),
    "cankaoxiaoxi": PlatformMeta(platform="cankaoxiaoxi", platform_name="参考消息"),
    "zaobao": PlatformMeta(platform="zaobao", platform_name="联合早报"),
    "sputniknewscn": PlatformMeta(platform="sputniknewscn", platform_name="卫星通讯社"),
    # 财经
    "wallstreetcn-hot": PlatformMeta(platform="wallstreetcn-hot", platform_name="华尔街见闻"),
    "cls-hot": PlatformMeta(platform="cls-hot", platform_name="财联社"),
    "jin10": PlatformMeta(platform="jin10", platform_name="金十数据"),
    "gelonghui": PlatformMeta(platform="gelonghui", platform_name="格隆汇"),
    "jintou": PlatformMeta(platform="jintou", platform_name="金投网"),
    "fastbull-express": PlatformMeta(platform="fastbull-express", platform_name="法布财经"),
    "xueqiu-hotstock": PlatformMeta(platform="xueqiu-hotstock", platform_name="雪球热股"),
    # 科技开发
    "github-trending-today": PlatformMeta(
        platform="github-trending-today", platform_name="GitHub Trending"
    ),
    "hackernews": PlatformMeta(platform="hackernews", platform_name="Hacker News"),
    "producthunt": PlatformMeta(platform="producthunt", platform_name="Product Hunt"),
    "juejin": PlatformMeta(platform="juejin", platform_name="稀土掘金"),
    "sspai": PlatformMeta(platform="sspai", platform_name="少数派"),
    "ithome": PlatformMeta(platform="ithome", platform_name="IT之家"),
    "solidot": PlatformMeta(platform="solidot", platform_name="Solidot"),
    "coolapk": PlatformMeta(platform="coolapk", platform_name="酷安"),
    "nowcoder": PlatformMeta(platform="nowcoder", platform_name="牛客"),
    "freebuf": PlatformMeta(platform="freebuf", platform_name="FreeBuf"),
    "steam": PlatformMeta(platform="steam", platform_name="Steam热门"),
    "chongbuluo-hot": PlatformMeta(platform="chongbuluo-hot", platform_name="虫部落"),
    "pcbeta-windows11": PlatformMeta(platform="pcbeta-windows11", platform_name="远景论坛"),
    # 问答社区
    "zhihu": PlatformMeta(platform="zhihu", platform_name="知乎热榜"),
    "tieba": PlatformMeta(platform="tieba", platform_name="百度贴吧"),
    "36kr-renqi": PlatformMeta(platform="36kr-renqi", platform_name="36氪人气"),
    "v2ex": PlatformMeta(platform="v2ex", platform_name="V2EX"),
    "v2ex-share": PlatformMeta(platform="v2ex-share", platform_name="V2EX分享"),
    "linux-do": PlatformMeta(platform="linux-do", platform_name="Linux.do"),
}


def normalize_platforms(raw: str | None) -> list[str]:
    if not raw:
        return settings.seesea_default_platforms
    parts = [item.strip() for item in raw.split(",") if item.strip()]
    return parts or settings.seesea_default_platforms


def get_platform_name(platform: str) -> str:
    return PLATFORMS.get(
        platform, PlatformMeta(platform=platform, platform_name=platform)
    ).platform_name
