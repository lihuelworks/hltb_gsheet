"""
Test the public C# HowLongToBeat API service
https://hltbapi.codepotatoes.de
"""

import requests
import json

BASE_URL = "https://hltbapi.codepotatoes.de"

print("Testing HowLongToBeat C# API Service")
print("=" * 60)

# Test 1: Search endpoint
print("\n1. Testing search endpoint...")
print(f"POST {BASE_URL}/hltb/search")

payload = {
    "searchTerm": "Celeste",
    "matchType": "fuzzy"
}

response = requests.post(f"{BASE_URL}/hltb/search", json=payload, timeout=30)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"✅ SUCCESS! Got {len(data)} results")
    if data:
        first = data[0]
        print(f"\nFirst result:")
        print(json.dumps(first, indent=2))
else:
    print(f"❌ Failed: {response.text}")

# Test 2: Try direct game lookup by HLTB ID
print("\n\n2. Testing direct lookup by HLTB ID...")
print(f"GET {BASE_URL}/hltb/55633")  # Celeste's HLTB ID

response = requests.get(f"{BASE_URL}/hltb/55633", timeout=30)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"✅ SUCCESS!")
    print(json.dumps(data, indent=2))
else:
    print(f"❌ Failed: {response.text}")

# Test 3: Another game
print("\n\n3. Testing with 'Halo Combat Evolved'...")
payload = {"searchTerm": "Halo Combat Evolved"}

response = requests.post(f"{BASE_URL}/hltb/search", json=payload, timeout=30)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"✅ SUCCESS! Got {len(data)} results")
    if data:
        first = data[0]
        print(f"\nFirst result:")
        print(f"  Title: {first.get('title')}")
        print(f"  Main Story: {first.get('mainStory')} hours")
        print(f"  Main + Extra: {first.get('mainStoryWithExtras')} hours")
        print(f"  Completionist: {first.get('completionist')} hours")
else:
    print(f"❌ Failed: {response.text}")

print("\n" + "=" * 60)
print("Testing complete!")
