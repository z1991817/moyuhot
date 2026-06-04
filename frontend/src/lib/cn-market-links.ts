const SINA_INDEX_SYMBOLS: Record<string, string> = {
  "000001": "sh000001",
  "000300": "sh000300",
  "000905": "sh000905",
  "000688": "sh000688",
};

const SINA_SECTOR_FALLBACK_URL = "https://finance.sina.com.cn/stock/sl/#sinaindustry_1";

const SINA_INDUSTRY_LABELS: Record<string, string> = {
  交通运输: "new_jtys",
  仪器仪表: "new_yqyb",
  传媒娱乐: "new_cmyl",
  供水供气: "new_gsgq",
  公路桥梁: "new_glql",
  其它行业: "new_qtxy",
  农林牧渔: "new_nlmy",
  农药化肥: "new_nyhf",
  化工行业: "new_hghy",
  化纤行业: "new_hqhy",
  医疗器械: "new_ylqx",
  印刷包装: "new_ysbz",
  发电设备: "new_fdsb",
  商业百货: "new_sybh",
  塑料制品: "new_slzp",
  家具行业: "new_jjhy",
  家电行业: "new_jdhy",
  建筑建材: "new_jzjc",
  开发区: "new_kfq",
  房地产: "new_fdc",
  摩托车: "new_mtc",
  有色金属: "new_ysjs",
  服装鞋类: "new_fzxl",
  机械行业: "new_jxhy",
  次新股: "new_stock",
  水泥行业: "new_snhy",
  汽车制造: "new_qczz",
  煤炭行业: "new_mthy",
  物资外贸: "new_wzwm",
  环保行业: "new_hbhy",
  玻璃行业: "new_blhy",
  生物制药: "new_swzz",
  电力行业: "new_dlhy",
  电器行业: "new_dqhy",
  电子信息: "new_dzxx",
  电子器件: "new_dzqj",
  石油行业: "new_syhy",
  纺织机械: "new_fzjx",
  纺织行业: "new_fzhy",
  综合行业: "new_zhhy",
  船舶制造: "new_cbzz",
  造纸行业: "new_zzhy",
  酒店旅游: "new_jdly",
  酿酒行业: "new_ljhy",
  金融行业: "new_jrhy",
  钢铁行业: "new_gthy",
  陶瓷行业: "new_tchy",
  飞机制造: "new_fjzz",
  食品行业: "new_sphy",
};

const TDX_TO_SINA_INDUSTRY_NAME: Record<string, string> = {
  酿酒: "酿酒行业",
  电力: "电力行业",
  白色家电: "家电行业",
  一般零售: "商业百货",
};

type CnMarketLinkedItem = {
  symbol: string;
  url?: string;
};

type CnSectorLinkedItem = {
  name: string;
  url?: string;
};

function normalizeSymbol(symbol: string): string {
  return symbol.trim();
}

function normalizeIndustryName(name: string): string {
  const value = name.trim();
  return TDX_TO_SINA_INDUSTRY_NAME[value] ?? value;
}

export function sinaMarketPrefix(symbol: string): "sh" | "sz" | "bj" {
  const normalized = normalizeSymbol(symbol);
  if (/^(8|4|9)/.test(normalized)) return "bj";
  if (/^(6|5)/.test(normalized)) return "sh";
  return "sz";
}

export function sinaStockUrl(symbol: string): string {
  const normalized = normalizeSymbol(symbol);
  if (!/^\d{6}$/.test(normalized)) return "https://finance.sina.com.cn/";
  return `https://finance.sina.com.cn/realstock/company/${sinaMarketPrefix(normalized)}${normalized}/nc.shtml`;
}

export function sinaIndexUrl(symbol: string): string {
  const normalized = normalizeSymbol(symbol);
  const sinaSymbol = SINA_INDEX_SYMBOLS[normalized];
  if (!sinaSymbol) return "https://finance.sina.com.cn/stock/";
  return `https://finance.sina.com.cn/realstock/company/${sinaSymbol}/nc.shtml`;
}

export function cnStockUrl(item: CnMarketLinkedItem): string {
  return item.url || sinaStockUrl(item.symbol);
}

export function cnSectorUrl(item: CnSectorLinkedItem): string {
  if (item.url && !item.url.includes("/realstock/company/") && !item.url.includes("#tdx_")) {
    return item.url;
  }
  const label = SINA_INDUSTRY_LABELS[normalizeIndustryName(item.name)];
  return label ? `https://vip.stock.finance.sina.com.cn/mkt/#${label}` : SINA_SECTOR_FALLBACK_URL;
}
