"""
Test using Steam AppID endpoint which should work
"""

import requests
import json

BASE_URL = "https://hltbapi.codepotatoes.de"

print("Testing C# HLTB API with Steam AppIDs")
print("=" * 60)

# Celeste Steam AppID: 504230
# Halo: The Master Chief Collection: 976730

games = [
    ("Celeste", 504230),
    ("Halo MCC", 976730),
]

for name, appid in games:
    print(f"\n{name} (Steam AppID: {appid})")
    print("-" * 40)
    
    response = requests.get(f"{BASE_URL}/steam/{appid}", timeout=30)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS!")
        print(f"  Title: {data.get('title')}")
        print(f"  Main Story: {data.get('mainStory')} hours")
        print(f"  Main + Extra: {data.get('mainStoryWithExtras')} hours")
        print(f"  Completionist: {data.get('completionist')} hours")
        print(f"  HLTB ID: {data.get('hltbId')}")
    else:
        print(f"❌ Failed: {response.text[:200]}")

print("\n" + "=" * 60)
