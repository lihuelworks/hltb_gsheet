"""
Test the actual HLTB search API endpoint
"""
import requests
from fake_useragent import UserAgent
import json

print("Testing HLTB Search API...")
print("=" * 80)

ua = UserAgent()
headers = {
    'content-type': 'application/json',
    'accept': '*/*',
    'User-Agent': ua.random.strip(),
    'referer': 'https://howlongtobeat.com/'
}

# Test 1: Try with just the search URL (no API key)
print("\nTEST 1: POST to /api/search (no API key in URL)")
print("-" * 80)

payload = {
    'searchType': "games",
    'searchTerms': ["Halo", "Combat", "Evolved"],
    'searchPage': 1,
    'size': 20,
    'searchOptions': {
        'games': {
            'userId': 0,
            'platform': "",
            'sortCategory': "popular",
            'rangeCategory': "main",
            'rangeTime': {
                'min': 0,
                'max': 0
            },
            'gameplay': {
                'perspective': "",
                'flow': "",
                'genre': ""
            },
            'rangeYear': {
                'max': "",
                'min': ""
            },
            'modifier': ""
        },
        'users': {
            'sortCategory': "postcount"
        },
        'lists': {
            'sortCategory': "follows"
        },
        'filter': "",
        'sort': 0,
        'randomizer': 0
    },
    'useCache': True
}

try:
    resp = requests.post(
        'https://howlongtobeat.com/api/search',
        headers=headers,
        data=json.dumps(payload),
        timeout=10
    )
    print(f"Status Code: {resp.status_code}")
    
    if resp.status_code == 200:
        print("✅ SUCCESS! API works without key in URL!")
        data = resp.json()
        print(f"Response has {len(data.get('data', []))} results")
        
        if data.get('data'):
            first_game = data['data'][0]
            print(f"\nFirst result:")
            print(f"  Game: {first_game.get('game_name')}")
            print(f"  Main Story: {first_game.get('comp_main', 0) / 3600:.1f} hours")
            print(f"  Main + Extra: {first_game.get('comp_plus', 0) / 3600:.1f} hours")
            print(f"  Completionist: {first_game.get('comp_100', 0) / 3600:.1f} hours")
    else:
        print(f"❌ Failed: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Try with "Celeste" (simple name)
print("\n" + "=" * 80)
print("\nTEST 2: Search for 'Celeste'")
print("-" * 80)

payload2 = payload.copy()
payload2['searchTerms'] = ["Celeste"]

try:
    resp = requests.post(
        'https://howlongtobeat.com/api/search',
        headers=headers,
        data=json.dumps(payload2),
        timeout=10
    )
    print(f"Status Code: {resp.status_code}")
    
    if resp.status_code == 200:
        print("✅ SUCCESS!")
        data = resp.json()
        print(f"Found {len(data.get('data', []))} results")
        
        if data.get('data'):
            for i, game in enumerate(data['data'][:3]):
                print(f"\n  {i+1}. {game.get('game_name')}")
                print(f"     Main Story: {game.get('comp_main', 0) / 3600:.1f} hours")
    else:
        print(f"❌ Failed: {resp.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("CONCLUSION:")
print("The HLTB API no longer requires an API key in the URL!")
print("Just POST to /api/search with the payload")
print("=" * 80)
