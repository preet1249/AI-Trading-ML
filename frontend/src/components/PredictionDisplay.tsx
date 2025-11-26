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
          {prediction.direction === 'BULLISH' && '=� '}
          {prediction.direction === 'BEARISH' && '=� '}
          {prediction.direction === 'NEUTRAL' && '� '}
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

      {/* H2: Price Levels Table */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-2">=� Price Levels</h2>
        <table className="w-full border border-zinc-700 rounded overflow-hidden">
          <tbody>
            {prediction.entry_price && (
              <tr className="border-b border-zinc-700">
                <td className="px-3 py-2 text-zinc-400 text-sm">Entry</td>
                <td className="px-3 py-2 text-emerald-400 font-semibold">${prediction.entry_price}</td>
              </tr>
            )}
            {prediction.target_price && (
              <tr className="border-b border-zinc-700">
                <td className="px-3 py-2 text-zinc-400 text-sm">Target</td>
                <td className="px-3 py-2 text-cyan-400 font-semibold">${prediction.target_price}</td>
              </tr>
            )}
            {prediction.stop_loss && (
              <tr>
                <td className="px-3 py-2 text-zinc-400 text-sm">Stop Loss</td>
                <td className="px-3 py-2 text-red-400 font-semibold">${prediction.stop_loss}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* H3: Market Structure */}
      {prediction.market_structure && (
        <div>
          <h3 className="text-base font-semibold text-white mb-2"><� Market Structure</h3>
          <p className="text-sm text-zinc-300">{prediction.market_structure}</p>
        </div>
      )}

      {/* H4: Confirmation Signals */}
      {prediction.confirmation_signals && prediction.confirmation_signals.length > 0 && (
        <div>
          <h4 className="text-base font-semibold text-white mb-2"> Confirmation Signals</h4>
          <ul className="space-y-1">
            {prediction.confirmation_signals.map((signal: string, i: number) => (
              <li key={i} className="text-sm text-zinc-300 flex gap-2">
                <span className="text-emerald-400">"</span>
                <span>{signal}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* H5: What to Watch */}
      {prediction.what_to_watch && prediction.what_to_watch.length > 0 && (
        <div>
          <h5 className="text-sm font-semibold text-white mb-2">=@ What to Watch</h5>
          <ul className="space-y-1">
            {prediction.what_to_watch.map((item: string, i: number) => (
              <li key={i} className="text-sm text-zinc-400">{item}</li>
            ))}
          </ul>
        </div>
      )}

      {/* H6: Entry Confirmation */}
      {prediction.entry_confirmation && (
        <div>
          <h6 className="text-sm font-semibold text-white mb-1"><� Entry Confirmation</h6>
          <p className="text-sm text-zinc-400">{prediction.entry_confirmation}</p>
        </div>
      )}

      {/* Reasoning */}
      {prediction.reasoning && (
        <div className="pt-3 border-t border-zinc-700">
          <p className="text-sm text-zinc-300 leading-relaxed">
            <strong className="text-white">Reasoning:</strong> {prediction.reasoning}
          </p>
        </div>
      )}

      {/* Technical Summary */}
      {prediction.ta_summary && (
        <div className="text-xs text-zinc-500 pt-2 border-t border-zinc-800">
          =� {prediction.ta_summary}
        </div>
      )}
    </div>
  );
}
