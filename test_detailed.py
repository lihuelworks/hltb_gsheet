"""
Test with detailed logging
"""
from howlongtobeatpy import HowLongToBeat
from howlongtobeatpy.HTMLRequests import HTMLRequests
import requests
from fake_useragent import UserAgent
import json

print("Manual test of the actual POST request...")
print("=" * 80)

ua = UserAgent()
headers = {
    'content-type': 'application/json',
    'accept': '*/*',
    'User-Agent': ua.random.strip(),
    'referer': 'https://howlongtobeat.com/'
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

print(f"URL: {HTMLRequests.SEARCH_URL}")
print(f"Payload: {json.dumps(payload, indent=2)[:500]}...")
print()

resp = requests.post(HTMLRequests.SEARCH_URL, headers=headers, data=json.dumps(payload), timeout=60)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:1000]}")

print("\n" + "=" * 80)
print("Now testing through library...")
print("=" * 80)

results = HowLongToBeat().search("Celeste")
print(f"Results: {results}")
if results:
    print(f"Found {len(results)} results")
    for r in results[:3]:
        print(f"  - {r.game_name}")
