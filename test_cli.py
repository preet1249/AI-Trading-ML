import requests
import json

# Test the prediction endpoint with your exact query
query = "Give me pred for SOLANA for scalping in 1m TF with perfect Entry Point"

print(f"\nTesting query: {query}\n")
print("Sending request to backend...\n")

try:
    response = requests.post(
        "http://localhost:8000/api/v1/cli/predict",
        json={"query": query},
        timeout=120
    )

    print(f"Status Code: {response.status_code}\n")

    if response.status_code == 200:
        data = response.json()
        print("="*60)
        print("Response:")
        print("="*60)
        print(json.dumps(data, indent=2))
        print("="*60)
    else:
        print(f"Error: {response.text}")

except Exception as e:
    print(f"Error: {str(e)}")
