'use client';

import { useEffect, useRef } from 'react';

export default function TradingViewChart() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      if (typeof (window as any).TradingView !== 'undefined') {
        new (window as any).TradingView.widget({
          container_id: 'tradingview_chart',
          width: '100%',
          height: '100%',
          symbol: 'BINANCE:BTCUSDT',  // Default symbol
          interval: '15',
          timezone: 'America/New_York',
          theme: 'dark',
          style: '1',
          locale: 'en',
          toolbar_bg: '#000000',
          enable_publishing: false,
          hide_side_toolbar: false,
          allow_symbol_change: true,  // Enable symbol search
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
  }, []);

  return (
    <div className="h-full bg-black">
      <div
        id="tradingview_chart"
        ref={containerRef}
        className="h-full"
      />
    </div>
  );
}
