import asyncio
from typing import Dict, List

import pandas as pd
import pandas_ta as ta
import requests


class TradingService:
    """Service responsible for fetching market data and computing indicators."""

    def __init__(self) -> None:
        self.base_url = "https://api.bybit.com"

    async def get_market_data(self, symbol: str, interval: str, limit: int = 200) -> List[Dict]:
        """Fetch k-line (candlestick) data from Bybit's public API."""

        endpoint = f"{self.base_url}/v5/market/kline"
        params = {"category": "linear", "symbol": symbol, "interval": interval, "limit": limit}

        try:
            try:
                response = await asyncio.to_thread(
                    requests.get, endpoint, params=params, timeout=10
                )
            except AttributeError:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, lambda: requests.get(endpoint, params=params, timeout=10)
                )
        except Exception as exc:  # pragma: no cover - network errors not easily testable
            raise Exception(f"Failed to connect to Bybit API: {exc}") from exc

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch market data: {response.status_code} {response.text}"
            )

        payload = response.json()
        if payload.get("retCode") != 0:
            raise Exception(payload.get("retMsg", "Unknown error from Bybit API"))

        result = payload.get("result", {})
        candles_raw = result.get("list", []) or []

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
            except (ValueError, TypeError, IndexError) as exc:
                raise Exception(f"Unexpected data format received from Bybit: {entry}") from exc

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
