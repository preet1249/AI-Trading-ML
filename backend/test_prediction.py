"""
Test the complete prediction workflow
"""
import asyncio
from app.agents.graph import prediction_workflow

async def test_prediction():
    """Test prediction with real query"""

    query = "What's the best entry point for BTC scalping with reversal price and breakout levels?"

    print("=" * 80)
    print(f"TESTING PREDICTION WORKFLOW")
    print("=" * 80)
    print(f"Query: {query}")
    print("-" * 80)

    # Initial state
    initial_state = {
        "query": query,
        "symbol": "",  # Will be extracted
        "user_id": "test_user",
        "timeframes": [],
        "analysis_type": "",
        "ta_data": {},
        "news_data": {},
        "prediction": {}
    }

    try:
        print("\nRunning multi-agent workflow...")
        print("-" * 80)

        # Run workflow
        final_state = await prediction_workflow.ainvoke(initial_state)

        print("\n" + "=" * 80)
        print("WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 80)

        # Display results
        print(f"\nSYMBOL: {final_state.get('symbol')}")
        print(f"ANALYSIS TYPE: {final_state.get('analysis_type')}")
        print(f"TIMEFRAMES: {final_state.get('timeframes')}")

        prediction = final_state.get('prediction', {})

        print(f"\nPREDICTION:")
        print(f"  Direction: {prediction.get('direction', 'N/A')}")
        print(f"  Trade Type: {prediction.get('trade_type', 'N/A')}")
        print(f"  Confidence: {prediction.get('confidence', 0)}%")
        print(f"  Risk Level: {prediction.get('risk_level', 'N/A')}")

        print(f"\nPRICE LEVELS:")
        print(f"  Entry Price: ${prediction.get('entry_price', 'N/A')}")
        if prediction.get('entry_reason'):
            print(f"  Entry Reason: {prediction.get('entry_reason')}")
        print(f"  Stop Loss: ${prediction.get('stop_loss', 'N/A')}")

        # Show multiple TP levels
        take_profits = prediction.get('take_profits', [])
        if take_profits:
            print(f"\n💎 MULTIPLE TAKE PROFIT LEVELS:")
            for tp in take_profits:
                print(f"  TP{tp['level']}: ${tp['price']} ({tp['rr']}) - {tp['reason']}")
        else:
            print(f"  Target Price: ${prediction.get('target_price', 'N/A')}")

        print(f"\nMARKET STRUCTURE:")
        print(f"  {prediction.get('market_structure', 'N/A')}")

        print(f"\nTRADE SETUP ANALYSIS:")
        if prediction.get('why_breakout_good'):
            print(f"  Breakout: {prediction.get('why_breakout_good')}")
        if prediction.get('why_reversal_good'):
            print(f"  Reversal: {prediction.get('why_reversal_good')}")

        print(f"\nCONFIRMATION SIGNALS:")
        for signal in prediction.get('confirmation_signals', []):
            print(f"  - {signal}")

        print(f"\nWHAT TO WATCH:")
        for item in prediction.get('what_to_watch', []):
            print(f"  - {item}")

        print(f"\nENTRY CONFIRMATION:")
        print(f"  {prediction.get('entry_confirmation', 'N/A')}")

        print(f"\nREASONING:")
        print(f"  {prediction.get('reasoning', 'N/A')}")

        print(f"\nTECHNICAL SUMMARY:")
        print(f"  {prediction.get('ta_summary', 'N/A')}")

        print(f"\nNEWS IMPACT:")
        print(f"  {prediction.get('news_impact', 'N/A')}")

        print(f"\nKEY FACTORS:")
        for factor in prediction.get('key_factors', []):
            print(f"  - {factor}")

        print("\n" + "=" * 80)
        print("TEST COMPLETED!")
        print("=" * 80)

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_prediction())
