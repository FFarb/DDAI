import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from ..core.trading_service import TradingService

router = APIRouter(prefix="/api/trading", tags=["Trading"])


logger = logging.getLogger(__name__)


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
    try:
        candles = await service.get_market_data(
            symbol=symbol, interval=interval, limit=limit
        )
        return service.calculate_indicators(candles)
    except HTTPException as exc:
        raise exc
    except Exception as exc:  # pragma: no cover - defensive logging for unexpected errors
        logger.exception(
            "Unhandled error while serving market data for %s with interval %s", symbol, interval
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected internal server error occurred.",
        ) from exc
