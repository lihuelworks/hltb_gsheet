"""
Test HLTB API with proper session initialization
"""
import requests
from fake_useragent import UserAgent
import json

print("Testing HLTB with Session Management...")
print("=" * 80)

# Create a session to persist cookies
session = requests.Session()

ua = UserAgent()
headers = {
    'User-Agent': ua.random.strip(),
    'referer': 'https://howlongtobeat.com/'
}

# Step 1: Visit the homepage to get cookies/session
print("\nSTEP 1: Getting session by visiting homepage...")
resp = session.get('https://howlongtobeat.com/', headers=headers, timeout=10)
print(f"Homepage status: {resp.status_code}")
print(f"Cookies received: {len(session.cookies)} cookies")
for cookie in session.cookies:
    print(f"  - {cookie.name}: {cookie.value[:50]}...")

# Step 2: Try the search with session cookies
print("\nSTEP 2: Searching with session cookies...")
search_headers = {
    'content-type': 'application/json',
    'accept': '*/*',
    'User-Agent': ua.random.strip(),
    'referer': 'https://howlongtobeat.com/',
    'origin': 'https://howlongtobeat.com'
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

try:
    resp = session.post(
        'https://howlongtobeat.com/api/search',
        headers=search_headers,
        data=json.dumps(payload),
        timeout=10
    )
    print(f"Search status: {resp.status_code}")
    
    if resp.status_code == 200:
        print("✅ SUCCESS!")
        data = resp.json()
        print(f"Found {len(data.get('data', []))} results\n")
        
        if data.get('data'):
            for i, game in enumerate(data['data'][:5]):
                print(f"{i+1}. {game.get('game_name')}")
                print(f"   Main: {game.get('comp_main', 0) / 3600:.1f}h | "
                      f"Extra: {game.get('comp_plus', 0) / 3600:.1f}h | "
                      f"100%: {game.get('comp_100', 0) / 3600:.1f}h")
    elif resp.status_code == 403:
        print(f"❌ Still 403 Forbidden")
        print(f"Response: {resp.text}")
    else:
        print(f"❌ Status {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
