'use client';

import { useState } from 'react';
import ChatPanel from '@/components/ChatPanel';
import TradingViewChart from '@/components/TradingViewChart';
import SymbolSelector from '@/components/SymbolSelector';

export default function TradePage() {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);

  return (
    <div className="h-screen bg-black flex flex-col">
      {/* Header with Symbol Selector */}
      <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm">
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-white">AI Trading Predictor</h1>
            <div className="w-px h-6 bg-zinc-700" />
            <SymbolSelector
              selectedSymbol={selectedSymbol}
              onSymbolChange={setSelectedSymbol}
            />
          </div>

          {currentPrice && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-zinc-500">Price:</span>
              <span className="text-lg font-semibold text-emerald-400">
                ${currentPrice.toLocaleString()}
              </span>
            </div>
          )}
        </div>
      </header>

      {/* Main Content: Chat (30%) + Chart (70%) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Panel - 30% */}
        <div className="w-[30%] border-r border-zinc-800">
          <ChatPanel
            selectedSymbol={selectedSymbol}
            onPriceUpdate={setCurrentPrice}
          />
        </div>

        {/* Chart Panel - 70% */}
        <div className="w-[70%]">
          <TradingViewChart
            symbol={selectedSymbol}
            onPriceUpdate={setCurrentPrice}
          />
        </div>
      </div>
    </div>
  );
}
