export default function PredictionDisplay({ prediction }: { prediction: any }) {
  if (!prediction) return null;

  // Handle market closed case
  if (prediction.market_closed || prediction.error === 'MARKET_CLOSED') {
    return (
      <div className="bg-zinc-800/50 border border-amber-800 rounded-lg p-4 space-y-3 max-w-full">
        <div className="flex items-center gap-2">
          <svg className="w-6 h-6 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h1 className="text-xl font-bold text-amber-400">Market Currently Closed</h1>
        </div>

        <div className="bg-amber-900/20 border border-amber-700 rounded p-3">
          <p className="text-amber-200 text-sm leading-relaxed">
            {prediction.message || prediction.reasoning || 'Market is currently closed'}
          </p>
        </div>

        {prediction.symbol && (
          <div className="text-sm text-zinc-400">
            <span className="font-semibold">{prediction.symbol}</span>
            {prediction.exchange && <span> on {prediction.exchange}</span>}
          </div>
        )}
      </div>
    );
  }

  const getDirectionColor = (dir: string) => {
    if (dir === 'BULLISH') return 'text-emerald-400';
    if (dir === 'BEARISH') return 'text-red-400';
    return 'text-zinc-400';
  };

  const getRiskColor = (risk: string) => {
    if (risk === 'HIGH') return 'bg-red-900/50 text-red-300';
    if (risk === 'MEDIUM') return 'bg-yellow-900/50 text-yellow-300';
    return 'bg-emerald-900/50 text-emerald-300';
  };

  return (
    <div className="bg-zinc-800/50 border border-zinc-700 rounded-lg p-4 space-y-4 max-w-full">
      {/* H1: Direction */}
      <div>
        <h1 className={`text-2xl font-bold ${getDirectionColor(prediction.direction)}`}>
          {prediction.direction === 'BULLISH' && '📈 '}
          {prediction.direction === 'BEARISH' && '📉 '}
          {prediction.direction === 'NEUTRAL' && '➡️ '}
          {prediction.direction} Prediction
        </h1>
        <div className="flex items-center gap-2 mt-1">
          <span className={`px-2 py-1 rounded text-xs font-semibold ${getRiskColor(prediction.risk_level)}`}>
            {prediction.risk_level} RISK
          </span>
          <span className="text-zinc-500 text-sm">
            Confidence: <span className="text-white font-semibold">{prediction.confidence}%</span>
          </span>
        </div>
      </div>

      {/* H2: Best Entry Point */}
      {prediction.entry_price && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-2">🎯 Best Entry Point</h2>
          <div className="bg-emerald-900/30 border border-emerald-700 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-emerald-400">${prediction.entry_price}</div>
                {prediction.entry_reason && (
                  <div className="text-xs text-emerald-300 mt-1">{prediction.entry_reason}</div>
                )}
              </div>
              {prediction.entry_confidence && (
                <div className="text-right">
                  <div className="text-sm text-zinc-400">Confidence</div>
                  <div className="text-lg font-semibold text-emerald-400">{prediction.entry_confidence}%</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* H2: Multiple Take Profit Levels */}
      {prediction.take_profits && prediction.take_profits.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-2">💎 Take Profit Levels (Multi-TP Strategy)</h2>
          <div className="space-y-2">
            {prediction.take_profits.map((tp: any, i: number) => (
              <div key={i} className="bg-cyan-900/20 border border-cyan-700 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-cyan-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                      {tp.level}
                    </div>
                    <div>
                      <div className="text-xl font-bold text-cyan-400">${tp.price}</div>
                      <div className="text-xs text-cyan-300">{tp.reason}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-cyan-400">{tp.rr}</div>
                    <div className="text-xs text-zinc-400">{tp.percentage > 0 ? '+' : ''}{tp.percentage}%</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* H2: Stop Loss */}
      {prediction.stop_loss && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-2">🛡️ Stop Loss</h2>
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-3">
            <div className="text-2xl font-bold text-red-400">${prediction.stop_loss}</div>
            <div className="text-xs text-red-300 mt-1">Protect your capital - Risk managed</div>
          </div>
        </div>
      )}

      {/* H3: Advanced Levels (Fibonacci & Pivots) */}
      {(prediction.fibonacci_levels || prediction.pivot_points) && (
        <div>
          <h3 className="text-base font-semibold text-white mb-2">📊 Key Technical Levels</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            {prediction.fibonacci_levels?.fib_618 && (
              <div className="bg-zinc-900/50 rounded p-2">
                <div className="text-zinc-500 text-xs">Fib 0.618</div>
                <div className="text-white font-semibold">${prediction.fibonacci_levels.fib_618.toFixed(2)}</div>
              </div>
            )}
            {prediction.pivot_points?.PP && (
              <div className="bg-zinc-900/50 rounded p-2">
                <div className="text-zinc-500 text-xs">Pivot Point</div>
                <div className="text-white font-semibold">${prediction.pivot_points.PP.toFixed(2)}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* H4: Order Blocks */}
      {prediction.order_blocks && prediction.order_blocks.length > 0 && (
        <div>
          <h4 className="text-base font-semibold text-white mb-2">🏛️ Order Blocks (Institutional Zones)</h4>
          <div className="space-y-2">
            {prediction.order_blocks.map((ob: any, i: number) => (
              <div key={i} className={`text-sm p-2 rounded ${ob.type === 'bullish' ? 'bg-emerald-900/20 text-emerald-300' : 'bg-red-900/20 text-red-300'}`}>
                <span className="font-semibold capitalize">{ob.type}:</span> ${ob.zone.toFixed(2)} (${ob.low.toFixed(2)} - ${ob.high.toFixed(2)})
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reasoning */}
      {prediction.reasoning && (
        <div className="pt-3 border-t border-zinc-700">
          <p className="text-sm text-zinc-300 leading-relaxed">
            <strong className="text-white">Analysis:</strong> {prediction.reasoning}
          </p>
        </div>
      )}

      {/* Technical & News Summary */}
      <div className="grid grid-cols-2 gap-2 text-xs text-zinc-500 pt-2 border-t border-zinc-700">
        {prediction.ta_summary && (
          <div>
            <span className="font-semibold text-zinc-400">TA:</span> {prediction.ta_summary}
          </div>
        )}
        {prediction.news_impact && (
          <div>
            <span className="font-semibold text-zinc-400">News:</span> {prediction.news_impact}
          </div>
        )}
      </div>
    </div>
  );
}
