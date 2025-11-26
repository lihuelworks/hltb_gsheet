"""
Test with browser-like headers
"""
import requests
import json

print("Testing with various header combinations...")
print("=" * 80)

# Test different header combinations
test_cases = [
    {
        "name": "Minimal headers",
        "headers": {
            'content-type': 'application/json',
        }
    },
    {
        "name": "With referer and origin",
        "headers": {
            'content-type': 'application/json',
            'referer': 'https://howlongtobeat.com/',
            'origin': 'https://howlongtobeat.com'
        }
    },
    {
        "name": "Full browser headers",
        "headers": {
            'content-type': 'application/json',
            'accept': 'application/json',
            'referer': 'https://howlongtobeat.com/',
            'origin': 'https://howlongtobeat.com',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin'
        }
    }
]

payload = {
    'searchType': "games",
    'searchTerms': ["Celeste"],
    'searchPage': 1,
    'size': 20,
    'searchOptions': {
        'games': {
            'userId': 0,
            'platform': "",
            'sortCategory': "popular",
            'rangeCategory': "main",
            'rangeTime': {'min': 0, 'max': 0},
            'gameplay': {'perspective': "", 'flow': "", 'genre': ""},
            'rangeYear': {'max': "", 'min': ""},
            'modifier': ""
        },
        'users': {'sortCategory': "postcount"},
        'lists': {'sortCategory': "follows"},
        'filter': "",
        'sort': 0,
        'randomizer': 0
    },
    'useCache': True
}

for test in test_cases:
    print(f"\n{test['name']}:")
    print("-" * 80)
    try:
        resp = requests.post(
            'https://howlongtobeat.com/api/search',
            headers=test['headers'],
            json=payload,  # Use json= instead of data=json.dumps() for proper encoding
            timeout=10
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ SUCCESS! Found {len(data.get('data', []))} results")
            if data.get('data'):
                print(f"   First: {data['data'][0].get('game_name')}")
        else:
            print(f"Response: {resp.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")
