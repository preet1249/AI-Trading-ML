export default function PredictionDisplay({ prediction }: { prediction: any }) {
  if (!prediction) return null;

  // Handle market closed case
  if (prediction.market_closed || prediction.error === 'MARKET_CLOSED') {
    return (
      <div className="bg-zinc-800/50 border border-amber-800 rounded-lg p-6 max-w-full font-mono text-sm">
        <pre className="text-amber-400 whitespace-pre-wrap">
{`⏰ MARKET CURRENTLY CLOSED
${'='.repeat(60)}

${prediction.message || prediction.reasoning || 'Market is currently closed'}

${prediction.symbol ? `Symbol: ${prediction.symbol}` : ''}
${prediction.exchange ? `Exchange: ${prediction.exchange}` : ''}

${'='.repeat(60)}`}
        </pre>
      </div>
    );
  }

  // Get direction color
  const getDirectionColor = (dir: string) => {
    if (dir === 'BULLISH') return 'text-emerald-400';
    if (dir === 'BEARISH') return 'text-red-400';
    return 'text-yellow-400';
  };

  // Format numbers with proper alignment
  const formatPrice = (price: any) => {
    if (!price) return 'N/A';
    const num = typeof price === 'number' ? price : parseFloat(price);
    return `$${num.toFixed(2)}`;
  };

  // Build the CLI-style output
  const separator = '='.repeat(60);
  const directionColor = getDirectionColor(prediction.direction);

  return (
    <div className="bg-zinc-900/80 border border-zinc-700 rounded-lg p-6 max-w-full overflow-x-auto">
      <pre className={`font-mono text-sm whitespace-pre-wrap ${directionColor}`}>
{`📊 PREDICTION FOR ${prediction.symbol || 'UNKNOWN'}
${separator}

🎯 DIRECTION: ${prediction.direction || 'N/A'}
💪 CONFIDENCE: ${prediction.confidence || 0}%
⚠️  RISK LEVEL: ${prediction.risk_level || 'N/A'}
⏰ TIMEFRAME: ${prediction.timeframe ? prediction.timeframe.toUpperCase() : 'N/A'}${prediction.current_price ? `
💰 CURRENT PRICE: ${formatPrice(prediction.current_price)}` : ''}${prediction.market_condition ? `
📈 MARKET: ${prediction.market_condition.toUpperCase()}` : ''}

📍 ENTRY & EXIT LEVELS:
  Entry:      ${formatPrice(prediction.entry_price)}
  Stop Loss:  ${formatPrice(prediction.stop_loss)}
  Target:     ${formatPrice(prediction.take_profits?.[0]?.price || prediction.target_price)}${prediction.entry_range_low || prediction.entry_range_high ? `
  Entry Low:  ${formatPrice(prediction.entry_range_low)}
  Entry High: ${formatPrice(prediction.entry_range_high)}` : ''}`}
        </pre>

        {/* Take Profit Levels */}
        {prediction.take_profits && prediction.take_profits.length > 0 && (
          <pre className="font-mono text-sm text-cyan-300 whitespace-pre-wrap mt-2">
{`
🎯 TAKE PROFIT LEVELS:${prediction.take_profits.map((tp: any, i: number) =>
  `\n  TP${i + 1}: ${formatPrice(tp.price)} (RR: ${tp.rr || '0.0'})`
).join('')}`}
          </pre>
        )}

        {/* Entry Reason */}
        {prediction.entry_reason && (
          <pre className="font-mono text-sm text-purple-300 whitespace-pre-wrap mt-2">
{`
💡 ENTRY REASON: ${prediction.entry_reason}`}
          </pre>
        )}

        {/* Analysis/Reasoning */}
        {prediction.reasoning && (
          <pre className="font-mono text-sm text-zinc-300 whitespace-pre-wrap mt-2">
{`
📝 ANALYSIS:
${prediction.reasoning}`}
          </pre>
        )}

        {/* KEY LEVELS - MOST IMPORTANT SECTION */}
        <pre className="font-mono text-sm text-amber-300 whitespace-pre-wrap mt-4 bg-amber-900/20 border border-amber-700/50 rounded p-4">
{`🔑 KEY LEVELS:${prediction.entry_price ? `
  • Entry Zone: ${formatPrice(prediction.entry_price)}` : ''}${prediction.entry_range_low ? `
  • Entry Low:  ${formatPrice(prediction.entry_range_low)}` : ''}${prediction.entry_range_high ? `
  • Entry High: ${formatPrice(prediction.entry_range_high)}` : ''}${prediction.resistance_levels && prediction.resistance_levels.length > 0 ? `
  • Resistance: ${formatPrice(prediction.resistance_levels[0])}` : ''}${prediction.support_levels && prediction.support_levels.length > 0 ? `
  • Support:    ${formatPrice(prediction.support_levels[0])}` : ''}${prediction.take_profits && prediction.take_profits.length > 0 ? `
  • Target:     ${formatPrice(prediction.take_profits[0].price)}` : prediction.target_price ? `
  • Target:     ${formatPrice(prediction.target_price)}` : ''}${prediction.stop_loss ? `
  • Stop Loss:  ${formatPrice(prediction.stop_loss)}` : ''}`}
        </pre>

        {/* Support Levels Detail */}
        {prediction.support_levels && prediction.support_levels.length > 1 && (
          <pre className="font-mono text-sm text-emerald-300 whitespace-pre-wrap mt-2">
{`
📉 SUPPORT LEVELS:${prediction.support_levels.map((level: any, i: number) =>
  `\n  S${i + 1}: ${formatPrice(typeof level === 'object' ? level.price : level)}`
).join('')}`}
          </pre>
        )}

        {/* Resistance Levels Detail */}
        {prediction.resistance_levels && prediction.resistance_levels.length > 1 && (
          <pre className="font-mono text-sm text-red-300 whitespace-pre-wrap mt-2">
{`
📈 RESISTANCE LEVELS:${prediction.resistance_levels.map((level: any, i: number) =>
  `\n  R${i + 1}: ${formatPrice(typeof level === 'object' ? level.price : level)}`
).join('')}`}
          </pre>
        )}

        {/* Technical Summary */}
        {(prediction.ta_summary || prediction.news_impact) && (
          <pre className="font-mono text-sm text-zinc-400 whitespace-pre-wrap mt-2">
{`${prediction.ta_summary ? `
📊 TECHNICAL: ${prediction.ta_summary}` : ''}${prediction.news_impact ? `
📰 NEWS IMPACT: ${prediction.news_impact}` : ''}`}
          </pre>
        )}

        {/* Footer */}
        <pre className="font-mono text-sm text-zinc-500 whitespace-pre-wrap mt-4">
{`
${separator}
⚠️  DISCLAIMER: This is AI-generated analysis. Always DYOR!
${separator}`}
        </pre>
      </div>
  );
}
