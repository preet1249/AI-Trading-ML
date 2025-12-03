"""
Test script for Indian stock prediction
"""
import requests
import json

# Test with Indian stock
query = "Reliance Industries day trading prediction"

print(f"Testing query: {query}\n")
print("Sending request to backend...")

try:
    response = requests.post(
        "http://localhost:8000/api/v1/cli/predict",
        json={"query": query},
        timeout=120
    )

    print(f"\nStatus Code: {response.status_code}\n")

    if response.status_code == 200:
        data = response.json()
        print("=" * 60)
        print("Response:")
        print("=" * 60)
        print(json.dumps(data, indent=2))
        print("=" * 60)

        if data.get("success"):
            print("\n✅ SUCCESS! Indian stock prediction working!")
        else:
            print("\n❌ FAILED:", data.get("message"))
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Error: {e}")
