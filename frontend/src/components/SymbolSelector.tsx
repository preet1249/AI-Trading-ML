'use client';

import { useState } from 'react';

const SYMBOLS = {
  'Crypto (Binance USDT)': [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT',
    'MATICUSDT', 'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 'UNIUSDT', 'ATOMUSDT', 'LTCUSDT'
  ],
  'US Stocks (NASDAQ)': [
    'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'AMD', 'NFLX', 'INTC'
  ],
  'Indian Stocks (NSE)': [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS'
  ]
};

interface Props {
  selectedSymbol: string;
  onSymbolChange: (symbol: string) => void;
}

export default function SymbolSelector({ selectedSymbol, onSymbolChange }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');

  const filteredSymbols = Object.entries(SYMBOLS).reduce((acc, [category, symbols]) => {
    const filtered = symbols.filter(s =>
      s.toLowerCase().includes(search.toLowerCase())
    );
    if (filtered.length > 0) acc[category] = filtered;
    return acc;
  }, {} as Record<string, string[]>);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-white font-medium flex items-center gap-2 transition-colors"
      >
        <span>{selectedSymbol}</span>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full mt-2 left-0 w-80 bg-zinc-900 border border-zinc-800 rounded-lg shadow-2xl z-20 max-h-96 overflow-hidden flex flex-col">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search symbols..."
              className="px-4 py-3 bg-zinc-800 text-white placeholder-zinc-500 border-b border-zinc-700 focus:outline-none"
            />
            <div className="overflow-y-auto">
              {Object.entries(filteredSymbols).map(([category, symbols]) => (
                <div key={category}>
                  <div className="px-4 py-2 text-xs font-semibold text-zinc-500 uppercase">
                    {category}
                  </div>
                  {symbols.map(symbol => (
                    <button
                      key={symbol}
                      onClick={() => {
                        onSymbolChange(symbol);
                        setIsOpen(false);
                        setSearch('');
                      }}
                      className={`w-full px-4 py-2 text-left hover:bg-zinc-800 transition-colors ${
                        symbol === selectedSymbol ? 'bg-zinc-800 text-emerald-400' : 'text-white'
                      }`}
                    >
                      {symbol}
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
