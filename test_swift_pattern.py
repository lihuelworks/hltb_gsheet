"""
Test using the pattern from Swift library's HTTP request file
They use: /api/ouch + apikey with Authorization header
"""
import requests
import json

# From the .httprequest file, the pattern seems to be:
# URL: /api/ouch + apikey
# Header: Authorization: apikey
# Body: users.if = apikey (this looks like a typo in their file though)

api_key = "a3ca5a62"  # From their example

headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.howlongtobeat.com',
    'Origin': 'https://www.howlongtobeat.com',
    'Authorization': api_key
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
        'users': {
            'sortCategory': "postcount",
            'id': api_key  # Maybe the key goes here too?
        },
        'lists': {'sortCategory': "follows"},
        'filter': "",
        'sort': 0,
        'randomizer': 0
    },
    'useCache': True
}

# Test 1: With /api/ouch prefix
print("TEST 1: Using /api/ouch + apikey pattern from Swift lib")
print("=" * 80)
try:
    url = f"https://www.howlongtobeat.com/api/ouch{api_key}"
    print(f"URL: {url}")
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Try /api/search with Authorization header
print("\n" + "=" * 80)
print("TEST 2: Using /api/search with Authorization header")
print("=" * 80)
try:
    url = "https://www.howlongtobeat.com/api/search"
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("✅ SUCCESS!")
        data = resp.json()
        print(f"Found {len(data.get('data', []))} results")
    else:
        print(f"Response: {resp.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
