# HowLongToBeat API Status - November 2025

## Current Situation

As of November 26, 2025, the HowLongToBeat Python library (`howlongtobeatpy`) is **completely non-functional** due to aggressive bot protection implemented by howlongtobeat.com.

### What Happened

- HLTB implemented Cloudflare-like bot protection that blocks all programmatic API requests
- All direct POST requests to `/api/search` return **403 "Session expired"**
- The Python library cannot bypass this protection with:
  - Different user agents (including fake_useragent)
  - Session cookies
  - Various header combinations
  - Static or dynamic user agents
  - API key extraction methods

### Investigation Summary

We attempted multiple approaches to fix the library:
1. ✅ Updated endpoint from `/api/s/` to `/api/search` 
2. ✅ Removed API key dependency (no longer needed)
3. ❌ Attempted `/api/locate/{seekMagic}` endpoint (doesn't exist as of Nov 2025)
4. ❌ Comprehensive browser-like headers (still blocked)
5. ❌ Session management with cookies (still blocked)
6. ❌ Authorization header variations (still blocked)

**Root Cause**: Bot protection is IP-based or uses TLS/HTTP2 fingerprinting that identifies Python requests library as a bot.

### Current Endpoints (Nov 2025)

Found in HLTB's JavaScript (`/_next/static/chunks/pages/_app-*.js`):
```
/api/error
/api/game/
/api/logout
/api/search          ← Returns 403 for programmatic access
/api/search/init
/api/user
/api/user/game_detail/
```

**Note**: The `/api/locate/{seekMagic}` endpoint mentioned in some documentation **does not exist** in current HLTB JavaScript.

### Working Alternative

A C# library successfully works: https://codeberg.org/Crashdummy/HowLongToBeatScraper

The C# implementation somehow bypasses bot protection (possibly due to .NET's HTTP client fingerprint or TLS handling). However, replicating this in Python requests has not been successful.

## Our Solution

This Flask API now **relies exclusively on SerpAPI** for game playtime data, which:
- ✅ Works reliably
- ✅ No bot protection issues
- ✅ Returns accurate data from Google search results
- ✅ Includes Wikipedia and gaming database sources

### Code Changes

1. **app.py**: 
   - Commented out `howlongtobeatpy` import
   - Disabled `search_howlongtobeat()` function with explanation
   - Forces fallback to SerpAPI exclusively

2. **requirements.txt**:
   - Commented out `howlongtobeatpy==1.0.18`
   - Documented reason for removal

## GitHub Issue

A comprehensive issue has been filed with the HowLongToBeat-PythonAPI project:
- Document: `GITHUB_ISSUE.md`
- Includes: Full investigation, test results, attempted fixes, and current status
- Purpose: Alert maintainer and community to the problem

## Future Options

1. **Wait for library fix**: If maintainer implements browser automation (Selenium/Playwright)
2. **Use C# proxy**: Deploy the working C# API as a sidecar service
3. **Browser automation**: Implement Selenium/Playwright in Python (slower but works)
4. **Contact HLTB**: Request official API access or IP whitelisting
5. **Keep SerpAPI**: Continue using the current working solution

## Testing

SerpAPI has been tested and confirmed working:
- Test file: `test_serpapi_only.py`
- Example data: `serp_halo1_example.json`
- All game searches return accurate playtime data

## Recommendation

**Continue using SerpAPI exclusively** until a viable HLTB solution emerges. The SerpAPI approach:
- Is more reliable (no bot protection)
- Has better uptime
- Returns consistent data
- Doesn't require maintenance when HLTB changes their website

---

*Last Updated*: November 26, 2025  
*Status*: HLTB Python library non-functional, SerpAPI fully operational
