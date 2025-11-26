[BUG] All searches return None - Library non-functional due to HLTB API changes and bot protection

## Summary
The HowLongToBeat Python API library is completely non-functional as of November 2024. All search operations return `None` regardless of game name, similarity settings, or search parameters. The issue affects both synchronous and asynchronous search methods.

## Environment
- **Library version**: 1.0.18 (latest from PyPI and master branch)
- **Python version**: 3.13.0 (also tested on 3.11)
- **Operating System**: Windows 10/11 (likely affects all platforms)
- **Installation method**: Both `pip install howlongtobeatpy` and from source
- **fake_useragent version**: 2.2.0

## Problem Description

### Observed Behavior
```python
from howlongtobeatpy import HowLongToBeat

# ALL of these return None
results = HowLongToBeat().search("Celeste")  # None
results = HowLongToBeat(0.0).search("Celeste")  # None (no similarity filter)
results = HowLongToBeat().search("The Witcher 3")  # None
results = HowLongToBeat().search("Halo Combat Evolved")  # None
```

### Expected Behavior
Should return a list of `HowLongToBeatEntry` objects with game data.

## Root Cause Analysis

After extensive debugging, we've identified **two critical issues**:

### Issue 1: Empty API Key Extraction
The library attempts to extract an API key from HLTB's JavaScript files, but the extraction now returns an **empty string** instead of `None` or a valid key.

**Evidence:**
```python
from howlongtobeatpy.HTMLRequests import HTMLRequests

search_info = HTMLRequests.send_website_request_getcode(False)
print(f"API Key: '{search_info.api_key}'")  # Prints: API Key: ''
print(f"Search URL: {search_info.search_url}")  # Prints: Search URL: None
```

The regex patterns in `__extract_api_from_script()` no longer match HLTB's current JavaScript structure.

### Issue 2: Bot Protection / Firewall Blocking
HLTB has implemented anti-bot measures (likely Cloudflare or similar) that block programmatic API requests with **403 Forbidden** errors.

**Direct API Test:**
```python
import requests
from fake_useragent import UserAgent

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

resp = requests.post('https://howlongtobeat.com/api/search', 
                     headers=headers, 
                     json=payload, 
                     timeout=10)
print(resp.status_code)  # 403
print(resp.text)  # {"error":"Session expired"}
```

**Different header combinations all result in 403:**
- Minimal headers: `403` with HTML firewall page
- With Referer/Origin: `403` with HTML firewall page  
- Full browser-like headers: `403` with JSON `{"error":"Session expired"}`

## Investigation Details

### JavaScript Analysis
We analyzed HLTB's current JavaScript bundles and found:
- The search endpoint is now simply `/api/search` (previously `/api/s/`)
- No API key suffix is required in the URL path
- The API key extraction patterns no longer match the JavaScript structure

**Current JavaScript patterns found:**
```
/api/search
/api/user
/api/logout
/api/search/init
/api/user/game_detail/
/api/game/
/api/error
```

### Comparison with Other Libraries
We checked the Swift implementation (https://github.com/holgerkrupp/HowLongToBeat-PythonAPI) which was updated November 1, 2025:
- Uses the **same API key extraction approach**
- Likely has the **same issues**
- Their `.httprequest` test file shows outdated endpoint patterns

### Test Results
All official library tests fail:
```bash
$ pytest howlongtobeatpy/tests/test_normal_request.py::TestNormalRequest::test_simple_game_name -v
FAILED - AssertionError: None == None : Search Results are None
```

## Attempted Fixes

We attempted several fixes:

1. ✅ **Updated SEARCH_URL** from `/api/s/` to `/api/search`
2. ✅ **Removed API key dependency** - made requests without API key suffix
3. ❌ **Comprehensive browser headers** - still blocked by firewall
4. ❌ **Static user agents** - still blocked
5. ❌ **Session management** - cookies not helping
6. ❌ **Authorization headers** - still blocked

**Modified code (still fails due to bot protection):**
```python
# In HTMLRequests.py
SEARCH_URL = BASE_URL + "api/search"  # Changed from "api/s/"

@staticmethod
def send_web_request(game_name: str, search_modifiers: SearchModifiers = SearchModifiers.NONE,
                     page: int = 1):
    headers = HTMLRequests.get_search_request_headers()
    search_url = HTMLRequests.SEARCH_URL  # No API key suffix needed
    payload = HTMLRequests.get_search_request_data(game_name, search_modifiers, page, None)
    resp = requests.post(search_url, headers=headers, data=payload, timeout=60)
    if resp.status_code == 200:
        return resp.text
    return None
```

## Additional Context

### Network/IP Considerations
The bot protection may be:
- IP-based (certain regions/IPs blocked)
- Rate-limit based
- Fingerprint-based (detecting automation)

### Timeline
- Library worked fine until approximately **October/November 2024**
- HLTB website structure changed (new JavaScript bundles)
- Bot protection appears to have been added/strengthened

## Reproduction Steps

1. Install the library: `pip install howlongtobeatpy`
2. Run any search:
   ```python
   from howlongtobeatpy import HowLongToBeat
   results = HowLongToBeat().search("Celeste")
   print(results)  # None
   ```
3. Observe that `None` is returned instead of game results

## System Information
```
Python: 3.13.0
howlongtobeatpy: 1.0.18
fake-useragent: 2.2.0
requests: 2.32.3
aiohttp: 3.13.2
beautifulsoup4: 4.14.2
```

## Working Solution Found

After extensive research, we found a **C# library that successfully works**:

**Repository**: https://codeberg.org/Crashdummy/HowLongToBeatScraper  
**Last Updated**: October 13, 2025 (commit: "Adapt to new endpoint")  
**NuGet Package**: `Codepotatoes.Scraper.HowLongToBeat` v1.3.1

### Current Status (November 2025)

**Important Update**: After further investigation, the `/api/locate/{seekMagic}` endpoint mentioned in the C# library **no longer exists** in HLTB's current JavaScript (November 26, 2025).

Current findings:
- HLTB's JavaScript only contains `/api/search` endpoint (no `/api/locate/`)
- Direct POST to `/ api/search` returns **403 "Session expired"** 
- Bot protection blocks ALL direct programmatic access
- No cookies are set when visiting the main page
- Session establishment doesn't bypass the protection
- Different user agents don't help

### How the C# Library Works

The C# library (Codepotatoes.Scraper.HowLongToBeat) successfully bypasses bot protection, but the exact mechanism is unclear. It may be:
1. Running in a .NET environment that isn't flagged as a bot
2. Using specific TLS fingerprinting that passes verification
3. The demo API (hltbapi.codepotatoes.de) runs as a caching proxy

### Available Endpoints in Current HLTB JavaScript

Found via analysis of `/_next/static/chunks/pages/_app-*.js`:
```
/api/error
/api/game/
/api/logout
/api/search
/api/search/init
/api/user
/api/user/game_detail/
```

### Recommended Solutions

1. **Use the C# proxy API** at https://hltbapi.codepotatoes.de (if the maintainer accepts this)
2. **Deploy the C# scraper** as a proxy service alongside your app
3. **Browser automation** (Selenium/Playwright) - slower but reliable
4. **Alternative data sources** - though none match HLTB's coverage

## Questions for Maintainer

1. How can we replicate what the C# library does to bypass bot protection?
2. Is the Python library actively maintained, or should users migrate to alternatives?
3. Would you consider a partnership with the C# library maintainer?

## Related Issues
- This likely affects all users globally
- Both sync and async methods affected
- All similarity thresholds affected
- Search by ID also likely affected (uses same underlying request mechanism)
