"""
Test with static user agent (like a real browser)
"""
import requests
import json

# Use a real, current Chrome user agent (not random)
headers = {
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Referer': 'https://howlongtobeat.com/',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

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

print("Testing with realistic Chrome headers...")
print("=" * 80)

try:
    resp = requests.post(
        'https://howlongtobeat.com/api/search',
        headers=headers,
        json=payload,
        timeout=10
    )
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        print("✅ SUCCESS!")
        data = resp.json()
        print(f"Found {len(data.get('data', []))} results")
        if data.get('data'):
            for i, game in enumerate(data['data'][:3]):
                print(f"\n{i+1}. {game.get('game_name')}")
                print(f"   Main: {game.get('comp_main', 0) / 3600:.1f}h")
    else:
        print(f"❌ Failed")
        print(f"Response: {resp.text[:500]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
