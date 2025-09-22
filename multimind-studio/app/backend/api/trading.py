from fastapi import APIRouter, Depends, Request

from ..core.trading_service import TradingService

router = APIRouter(prefix="/api/trading", tags=["Trading"])


def get_trading_service(request: Request) -> TradingService:
    service = getattr(request.app.state, "trading_service", None)
    if service is None:
        raise RuntimeError("Trading service is not configured")
    return service


@router.get("/market-data/{symbol}")
async def get_market_data(
    symbol: str,
    interval: str,
    limit: int = 200,
    service: TradingService = Depends(get_trading_service),
):
    candles = await service.get_market_data(symbol=symbol, interval=interval, limit=limit)
    return service.calculate_indicators(candles)
