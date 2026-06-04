from app.clients.tdx_market import CnMarketError, TdxMarketClient


class CnMarketClient(TdxMarketClient):
    pass


__all__ = ["CnMarketClient", "CnMarketError"]
