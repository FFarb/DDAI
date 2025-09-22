import asyncio
import logging
from typing import Dict, List

import pandas as pd
import pandas_ta as ta
import requests
from fastapi import HTTPException
from requests.exceptions import RequestException


logger = logging.getLogger(__name__)


class TradingService:
    """Service responsible for fetching market data and computing indicators."""

    def __init__(self) -> None:
        self.base_url = "https://api.bybit.com"

    async def get_market_data(self, symbol: str, interval: str, limit: int = 200) -> List[Dict]:
        """Fetch k-line (candlestick) data from Bybit's public API."""

        endpoint = f"{self.base_url}/v5/market/kline"
        params = {"category": "linear", "symbol": symbol, "interval": interval, "limit": limit}

        response = None

        try:
            try:
                response = await asyncio.to_thread(
                    requests.get, endpoint, params=params, timeout=10
                )
            except AttributeError:  # pragma: no cover - fallback for Python < 3.9
                loop = asyncio.get_event_loop()

                def _perform_request() -> requests.Response:
                    return requests.get(endpoint, params=params, timeout=10)

                response = await loop.run_in_executor(None, _perform_request)
        except RequestException as exc:
            logger.error(
                "Request to Bybit API failed for symbol %s with interval %s: %s",
                symbol,
                interval,
                exc,
                exc_info=True,
            )
            raise HTTPException(
                status_code=502,
                detail="Failed to communicate with the external Bybit API.",
            ) from exc
        except Exception as exc:  # pragma: no cover - safety net for unexpected errors
            logger.exception(
                "Unexpected error when requesting Bybit market data for %s (interval %s)",
                symbol,
                interval,
            )
            raise HTTPException(
                status_code=502,
                detail="Failed to communicate with the external Bybit API.",
            ) from exc

        if response is None:  # pragma: no cover - defensive
            logger.error("No response object returned when requesting Bybit data")
            raise HTTPException(
                status_code=502,
                detail="Failed to communicate with the external Bybit API.",
            )

        if response.status_code != 200:
            logger.error(
                "Bybit API returned non-200 status %s for symbol %s: %s",
                response.status_code,
                symbol,
                response.text,
            )
            raise HTTPException(
                status_code=502,
                detail="Failed to communicate with the external Bybit API.",
            )

        try:
            payload = response.json()
        except ValueError as exc:
            logger.error(
                "Failed to decode JSON from Bybit response for symbol %s: %s",
                symbol,
                response.text,
                exc_info=True,
            )
            raise HTTPException(
                status_code=502,
                detail="Failed to communicate with the external Bybit API.",
            ) from exc

        if not isinstance(payload, dict):
            logger.error("Unexpected payload type from Bybit: %r", payload)
            raise HTTPException(
                status_code=500,
                detail="Unexpected response format from Bybit API.",
            )

        missing_keys = {"retCode", "retMsg", "result"} - payload.keys()
        if missing_keys:
            logger.error(
                "Missing keys %s in Bybit response for %s: %s",
                ", ".join(sorted(missing_keys)),
                symbol,
                payload,
            )
            raise HTTPException(
                status_code=500,
                detail="Unexpected response format from Bybit API.",
            )

        if payload.get("retCode") != 0:
            logger.error(
                "Bybit API returned error for %s: retCode=%s retMsg=%s payload=%s",
                symbol,
                payload.get("retCode"),
                payload.get("retMsg"),
                payload,
            )
            raise HTTPException(
                status_code=500,
                detail=payload.get("retMsg", "Unknown error from Bybit API"),
            )

        result = payload.get("result")
        if not isinstance(result, dict):
            logger.error("Unexpected 'result' structure in Bybit response: %s", result)
            raise HTTPException(
                status_code=500,
                detail="Unexpected response format from Bybit API.",
            )

        candles_raw = result.get("list") or []
        if not isinstance(candles_raw, list):
            logger.error("Bybit 'list' payload is not a list: %r", candles_raw)
            raise HTTPException(
                status_code=500,
                detail="Unexpected response format from Bybit API.",
            )

        candles: List[Dict] = []
        for entry in candles_raw:
            if not entry:
                continue
            try:
                timestamp_ms = int(entry[0])
                open_price = float(entry[1])
                high_price = float(entry[2])
                low_price = float(entry[3])
                close_price = float(entry[4])
                volume = float(entry[5]) if len(entry) > 5 else 0.0
            except (ValueError, TypeError, IndexError, KeyError) as exc:
                logger.error("Failed to parse candle entry from Bybit: %s", entry, exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="Failed to parse candlestick data from Bybit.",
                ) from exc

            candles.append(
                {
                    "timestamp": timestamp_ms // 1000,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume,
                }
            )

        return candles

    def calculate_indicators(self, candles: List[Dict]) -> List[Dict]:
        """Calculate RSI and MACD indicators for the provided candle data."""

        if not candles:
            return []

        df = pd.DataFrame(candles)
        if df.empty:
            return []

        for column in ["open", "high", "low", "close", "volume"]:
            df[column] = pd.to_numeric(df[column], errors="coerce")
        df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")

        df["rsi"] = ta.rsi(df["close"], length=14)
        macd = ta.macd(df["close"])
        if macd is not None and not macd.empty:
            macd = macd.rename(
                columns={
                    "MACD_12_26_9": "macd",
                    "MACDs_12_26_9": "macd_signal",
                    "MACDh_12_26_9": "macd_hist",
                }
            )
            df = pd.concat([df, macd], axis=1)
        else:
            df["macd"] = pd.NA
            df["macd_signal"] = pd.NA
            df["macd_hist"] = pd.NA

        df = df.where(pd.notna(df), None)

        records = df.to_dict(orient="records")
        numeric_fields = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "rsi",
            "macd",
            "macd_signal",
            "macd_hist",
        ]
        for record in records:
            if record.get("timestamp") is not None:
                record["timestamp"] = int(record["timestamp"])
            for field in numeric_fields:
                value = record.get(field)
                if value is None:
                    continue
                try:
                    record[field] = float(value)
                except (TypeError, ValueError):
                    continue

        return records
