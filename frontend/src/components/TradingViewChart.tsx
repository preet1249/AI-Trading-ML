'use client';

import { useEffect, useRef } from 'react';

interface Props {
  symbol: string;
  onPriceUpdate?: (price: number) => void;
}

export default function TradingViewChart({ symbol }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Convert symbol for TradingView format
    let tvSymbol = symbol;
    if (symbol.endsWith('USDT')) {
      // Binance crypto: BTCUSDT -> BINANCE:BTCUSDT
      tvSymbol = `BINANCE:${symbol}`;
    } else if (symbol.endsWith('.NS')) {
      // NSE stocks: RELIANCE.NS -> NSE:RELIANCE
      tvSymbol = `NSE:${symbol.replace('.NS', '')}`;
    } else {
      // NASDAQ stocks: AAPL -> NASDAQ:AAPL
      tvSymbol = `NASDAQ:${symbol}`;
    }

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      if (typeof (window as any).TradingView !== 'undefined') {
        new (window as any).TradingView.widget({
          container_id: containerRef.current?.id,
          width: '100%',
          height: '100%',
          symbol: tvSymbol,
          interval: '15',
          timezone: 'America/New_York',
          theme: 'dark',
          style: '1',
          locale: 'en',
          toolbar_bg: '#000000',
          enable_publishing: false,
          hide_side_toolbar: false,
          allow_symbol_change: false,
          save_image: false,
          backgroundColor: '#000000',
          gridColor: '#1f1f1f',
          hide_top_toolbar: false,
          hide_legend: false,
          studies: [
            'MASimple@tv-basicstudies',
            'RSI@tv-basicstudies',
            'MACD@tv-basicstudies'
          ]
        });
      }
    };

    document.head.appendChild(script);

    return () => {
      if (document.head.contains(script)) {
        document.head.removeChild(script);
      }
    };
  }, [symbol]);

  return (
    <div className="h-full bg-black">
      <div
        id={`tradingview_${symbol}`}
        ref={containerRef}
        className="h-full"
      />
    </div>
  );
}
