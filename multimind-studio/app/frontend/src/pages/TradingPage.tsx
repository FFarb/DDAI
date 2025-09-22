import { useCallback, useEffect, useState } from 'react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';

type Candle = {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  rsi?: number | null;
  macd?: number | null;
  macd_signal?: number | null;
  macd_hist?: number | null;
};

const DEFAULT_SYMBOL = 'BTCUSDT';

const TradingPage = () => {
  const [data, setData] = useState<Candle[]>([]);
  const [loading, setLoading] = useState(false);
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async (targetSymbol: string) => {
    const normalizedSymbol = targetSymbol.trim().toUpperCase();
    if (!normalizedSymbol) {
      setSymbol('');
      setError('Please provide a trading symbol.');
      setData([]);
      return;
    }
    setSymbol(normalizedSymbol);
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `http://localhost:8000/api/trading/market-data/${normalizedSymbol}?interval=60&limit=200`,
      );
      if (!response.ok) {
        throw new Error(`Failed to fetch data: ${response.status} ${response.statusText}`);
      }
      const payload = await response.json();
      if (Array.isArray(payload)) {
        setData(
          payload.map((entry) => ({
            ...entry,
            timestamp: Number(entry.timestamp),
            open: Number(entry.open),
            high: Number(entry.high),
            low: Number(entry.low),
            close: Number(entry.close),
            volume: Number(entry.volume),
            rsi: entry.rsi !== undefined && entry.rsi !== null ? Number(entry.rsi) : null,
            macd: entry.macd !== undefined && entry.macd !== null ? Number(entry.macd) : null,
            macd_signal:
              entry.macd_signal !== undefined && entry.macd_signal !== null
                ? Number(entry.macd_signal)
                : null,
            macd_hist:
              entry.macd_hist !== undefined && entry.macd_hist !== null
                ? Number(entry.macd_hist)
                : null,
          })) as Candle[],
        );
      } else {
        setData([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected error fetching data');
      setData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchData(DEFAULT_SYMBOL);
  }, [fetchData]);

  const formatNumber = (value: number | null | undefined, fractionDigits = 2) => {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return '—';
    }
    return value.toFixed(fractionDigits);
  };

  return (
    <div className="flex-column">
      <h1>Crypto Market Data</h1>
      <div className="card">
        <div className="flex">
          <Input
            value={symbol}
            onChange={(event) => setSymbol(event.target.value.toUpperCase())}
            placeholder="Symbol (e.g. BTCUSDT)"
            aria-label="Trading symbol"
          />
          <Button onClick={() => void fetchData(symbol)} disabled={loading || !symbol}>
            {loading ? 'Loading…' : 'Fetch Data'}
          </Button>
        </div>
        {error && <p style={{ color: '#ff6b6b' }}>{error}</p>}
      </div>
      {loading && <p>Loading market data…</p>}
      {!loading && data.length === 0 && !error && <p>No market data available.</p>}
      {!loading && data.length > 0 && (
        <div className="card" style={{ overflowX: 'auto' }}>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Open</TableHead>
                <TableHead>High</TableHead>
                <TableHead>Low</TableHead>
                <TableHead>Close</TableHead>
                <TableHead>Volume</TableHead>
                <TableHead>RSI</TableHead>
                <TableHead>MACD</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((candle) => (
                <TableRow key={candle.timestamp}>
                  <TableCell>
                    {new Date(candle.timestamp * 1000).toLocaleString()}
                  </TableCell>
                  <TableCell>{formatNumber(candle.open)}</TableCell>
                  <TableCell>{formatNumber(candle.high)}</TableCell>
                  <TableCell>{formatNumber(candle.low)}</TableCell>
                  <TableCell>{formatNumber(candle.close)}</TableCell>
                  <TableCell>{formatNumber(candle.volume, 2)}</TableCell>
                  <TableCell>{formatNumber(candle.rsi)}</TableCell>
                  <TableCell>{formatNumber(candle.macd)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
};

export default TradingPage;
