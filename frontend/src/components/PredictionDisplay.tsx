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
    return 'text-yellow-400';
  };

  const getRiskColor = (risk: string) => {
    if (risk === 'HIGH') return 'bg-red-900/50 text-red-300';
    if (risk === 'MEDIUM') return 'bg-yellow-900/50 text-yellow-300';
    return 'bg-emerald-900/50 text-emerald-300';
  };

  const formatPrice = (price: any) => {
    if (!price) return null;
    const num = typeof price === 'number' ? price : parseFloat(price);
    return num.toFixed(2);
  };

  return (
    <div className="bg-zinc-800/50 border border-zinc-700 rounded-lg p-4 space-y-4 max-w-full">

      {/* Header: Prediction for Symbol */}
      <div>
        <h1 className="text-xl font-bold text-white mb-3">
          📊 Prediction for {prediction.symbol || 'UNKNOWN'}
        </h1>

        {/* Direction, Confidence, Risk, Timeframe */}
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div className="bg-zinc-900/50 rounded-lg p-3">
            <div className="text-xs text-zinc-500 mb-1">🎯 DIRECTION</div>
            <div className={`text-lg font-bold ${getDirectionColor(prediction.direction)}`}>
              {prediction.direction === 'BULLISH' && '📈 '}
              {prediction.direction === 'BEARISH' && '📉 '}
              {prediction.direction || 'N/A'}
            </div>
          </div>

          <div className="bg-zinc-900/50 rounded-lg p-3">
            <div className="text-xs text-zinc-500 mb-1">💪 CONFIDENCE</div>
            <div className="text-lg font-bold text-white">{prediction.confidence || 0}%</div>
          </div>

          <div className="bg-zinc-900/50 rounded-lg p-3">
            <div className="text-xs text-zinc-500 mb-1">⚠️ RISK LEVEL</div>
            <div className={`text-sm font-semibold px-2 py-1 rounded inline-block ${getRiskColor(prediction.risk_level)}`}>
              {prediction.risk_level || 'N/A'}
            </div>
          </div>

          <div className="bg-zinc-900/50 rounded-lg p-3">
            <div className="text-xs text-zinc-500 mb-1">⏰ TIMEFRAME</div>
            <div className="text-lg font-bold text-white">{prediction.timeframe ? prediction.timeframe.toUpperCase() : 'N/A'}</div>
          </div>
        </div>

        {/* Current Price & Market Condition */}
        <div className="grid grid-cols-2 gap-3">
          {prediction.current_price && (
            <div className="bg-zinc-900/50 rounded-lg p-3">
              <div className="text-xs text-zinc-500 mb-1">💰 CURRENT PRICE</div>
              <div className="text-lg font-bold text-white">${formatPrice(prediction.current_price)}</div>
            </div>
          )}

          {prediction.market_condition && (
            <div className="bg-zinc-900/50 rounded-lg p-3">
              <div className="text-xs text-zinc-500 mb-1">📈 MARKET</div>
              <div className="text-lg font-bold text-white">{prediction.market_condition.toUpperCase()}</div>
            </div>
          )}
        </div>
      </div>

      {/* Entry & Exit Levels */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">📍 Entry & Exit Levels</h2>
        <div className="grid grid-cols-3 gap-3">
          {prediction.entry_price && (
            <div className="bg-emerald-900/30 border border-emerald-700 rounded-lg p-3">
              <div className="text-xs text-emerald-400 mb-1">Entry</div>
              <div className="text-xl font-bold text-emerald-300">${formatPrice(prediction.entry_price)}</div>
            </div>
          )}

          {prediction.stop_loss && (
            <div className="bg-red-900/30 border border-red-700 rounded-lg p-3">
              <div className="text-xs text-red-400 mb-1">Stop Loss</div>
              <div className="text-xl font-bold text-red-300">${formatPrice(prediction.stop_loss)}</div>
            </div>
          )}

          {(prediction.take_profits?.[0]?.price || prediction.target_price) && (
            <div className="bg-cyan-900/30 border border-cyan-700 rounded-lg p-3">
              <div className="text-xs text-cyan-400 mb-1">Target</div>
              <div className="text-xl font-bold text-cyan-300">${formatPrice(prediction.take_profits?.[0]?.price || prediction.target_price)}</div>
            </div>
          )}
        </div>

        {/* Entry Range */}
        {(prediction.entry_range_low || prediction.entry_range_high) && (
          <div className="grid grid-cols-2 gap-3 mt-3">
            {prediction.entry_range_low && (
              <div className="bg-emerald-900/20 border border-emerald-700 rounded-lg p-2">
                <div className="text-xs text-emerald-400">Entry Low: <span className="font-bold">${formatPrice(prediction.entry_range_low)}</span></div>
              </div>
            )}
            {prediction.entry_range_high && (
              <div className="bg-emerald-900/20 border border-emerald-700 rounded-lg p-2">
                <div className="text-xs text-emerald-400">Entry High: <span className="font-bold">${formatPrice(prediction.entry_range_high)}</span></div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Take Profit Levels */}
      {prediction.take_profits && prediction.take_profits.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-3">🎯 Take Profit Levels</h2>
          <div className="space-y-2">
            {prediction.take_profits.map((tp: any, i: number) => (
              <div key={i} className="bg-cyan-900/20 border border-cyan-700 rounded-lg p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-cyan-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                    {i + 1}
                  </div>
                  <div>
                    <div className="text-sm text-cyan-400">TP{i + 1}: <span className="text-xl font-bold text-cyan-300">${formatPrice(tp.price)}</span></div>
                    {tp.reason && <div className="text-xs text-cyan-300/70">{tp.reason}</div>}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-cyan-400">RR: {tp.rr || '0.0'}</div>
                  {tp.percentage && <div className="text-xs text-zinc-400">{tp.percentage > 0 ? '+' : ''}{tp.percentage}%</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Entry Reason */}
      {prediction.entry_reason && (
        <div className="bg-purple-900/20 border border-purple-700 rounded-lg p-3">
          <div className="text-sm text-purple-300">
            <span className="font-semibold">💡 Entry Reason:</span> {prediction.entry_reason}
          </div>
        </div>
      )}

      {/* Analysis */}
      {prediction.reasoning && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-2">📝 Analysis</h2>
          <div className="bg-zinc-900/50 border border-zinc-700 rounded-lg p-3">
            <p className="text-sm text-zinc-300 leading-relaxed">{prediction.reasoning}</p>
          </div>
        </div>
      )}

      {/* KEY LEVELS - MOST IMPORTANT */}
      <div className="bg-gradient-to-r from-amber-900/40 to-orange-900/40 border-2 border-amber-600/60 rounded-lg p-4">
        <h2 className="text-lg font-bold text-amber-300 mb-3 flex items-center gap-2">
          🔑 KEY LEVELS
          <span className="text-xs bg-amber-600 text-white px-2 py-1 rounded">IMPORTANT</span>
        </h2>
        <div className="grid grid-cols-2 gap-3">
          {prediction.entry_price && (
            <div className="bg-black/30 rounded p-2">
              <div className="text-xs text-amber-400">• Entry Zone</div>
              <div className="text-lg font-bold text-amber-200">${formatPrice(prediction.entry_price)}</div>
            </div>
          )}

          {prediction.entry_range_low && (
            <div className="bg-black/30 rounded p-2">
              <div className="text-xs text-amber-400">• Entry Low</div>
              <div className="text-lg font-bold text-amber-200">${formatPrice(prediction.entry_range_low)}</div>
            </div>
          )}

          {prediction.entry_range_high && (
            <div className="bg-black/30 rounded p-2">
              <div className="text-xs text-amber-400">• Entry High</div>
              <div className="text-lg font-bold text-amber-200">${formatPrice(prediction.entry_range_high)}</div>
            </div>
          )}

          {prediction.resistance_levels && prediction.resistance_levels.length > 0 && (
            <div className="bg-black/30 rounded p-2">
              <div className="text-xs text-amber-400">• Resistance</div>
              <div className="text-lg font-bold text-amber-200">${formatPrice(prediction.resistance_levels[0])}</div>
            </div>
          )}

          {prediction.support_levels && prediction.support_levels.length > 0 && (
            <div className="bg-black/30 rounded p-2">
              <div className="text-xs text-amber-400">• Support</div>
              <div className="text-lg font-bold text-amber-200">${formatPrice(prediction.support_levels[0])}</div>
            </div>
          )}

          {(prediction.take_profits?.[0]?.price || prediction.target_price) && (
            <div className="bg-black/30 rounded p-2">
              <div className="text-xs text-amber-400">• Target</div>
              <div className="text-lg font-bold text-amber-200">${formatPrice(prediction.take_profits?.[0]?.price || prediction.target_price)}</div>
            </div>
          )}

          {prediction.stop_loss && (
            <div className="bg-black/30 rounded p-2">
              <div className="text-xs text-amber-400">• Stop Loss</div>
              <div className="text-lg font-bold text-amber-200">${formatPrice(prediction.stop_loss)}</div>
            </div>
          )}
        </div>
      </div>

      {/* Support Levels Detail */}
      {prediction.support_levels && prediction.support_levels.length > 1 && (
        <div>
          <h3 className="text-base font-semibold text-white mb-2">📉 Support Levels</h3>
          <div className="grid grid-cols-3 gap-2">
            {prediction.support_levels.map((level: any, i: number) => (
              <div key={i} className="bg-emerald-900/20 border border-emerald-700 rounded p-2">
                <div className="text-xs text-emerald-400">S{i + 1}</div>
                <div className="text-sm font-bold text-emerald-300">${formatPrice(typeof level === 'object' ? level.price : level)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Resistance Levels Detail */}
      {prediction.resistance_levels && prediction.resistance_levels.length > 1 && (
        <div>
          <h3 className="text-base font-semibold text-white mb-2">📈 Resistance Levels</h3>
          <div className="grid grid-cols-3 gap-2">
            {prediction.resistance_levels.map((level: any, i: number) => (
              <div key={i} className="bg-red-900/20 border border-red-700 rounded p-2">
                <div className="text-xs text-red-400">R{i + 1}</div>
                <div className="text-sm font-bold text-red-300">${formatPrice(typeof level === 'object' ? level.price : level)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Technical & News Summary */}
      {(prediction.ta_summary || prediction.news_impact) && (
        <div className="grid grid-cols-2 gap-3">
          {prediction.ta_summary && (
            <div className="bg-zinc-900/50 rounded p-3">
              <div className="text-xs text-zinc-500 mb-1">📊 Technical</div>
              <div className="text-sm text-zinc-300">{prediction.ta_summary}</div>
            </div>
          )}
          {prediction.news_impact && (
            <div className="bg-zinc-900/50 rounded p-3">
              <div className="text-xs text-zinc-500 mb-1">📰 News Impact</div>
              <div className="text-sm text-zinc-300">{prediction.news_impact}</div>
            </div>
          )}
        </div>
      )}

      {/* Disclaimer */}
      <div className="border-t border-zinc-700 pt-3">
        <div className="text-xs text-zinc-500 text-center">
          ⚠️ DISCLAIMER: This is AI-generated analysis. Always do your own research!
        </div>
      </div>
    </div>
  );
}
