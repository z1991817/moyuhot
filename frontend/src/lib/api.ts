import type {
  CnMarketResponse,
  HomeResponse,
  MarketResponse,
  SourcesResponse,
  StocksResponse,
  TrendsResponse,
} from "./types";

const API_BASE =
  import.meta.env.PUBLIC_API_BASE ??
  import.meta.env.API_BASE ??
  (import.meta.env.DEV ? "http://127.0.0.1:8000/api" : "/api");

async function requestJSON<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function fetchHome(): Promise<HomeResponse> {
  return requestJSON<HomeResponse>("/home");
}

export async function fetchTrends(platforms?: string[]): Promise<TrendsResponse> {
  const query = platforms && platforms.length > 0 ? `?platform=${platforms.join(",")}` : "";
  return requestJSON<TrendsResponse>(`/trends${query}`);
}

export async function fetchMarketUs(): Promise<MarketResponse> {
  return requestJSON<MarketResponse>("/market/us");
}

export async function fetchSources(): Promise<SourcesResponse> {
  return requestJSON<SourcesResponse>("/sources");
}

export async function fetchUsStocks(): Promise<StocksResponse> {
  return requestJSON<StocksResponse>("/market/us/stocks");
}

export async function fetchCnMarket(): Promise<CnMarketResponse> {
  return requestJSON<CnMarketResponse>("/market/cn");
}

