"""
Debug script to examine HLTB website structure and find the API key pattern
"""
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re

print("Fetching HLTB homepage...")
ua = UserAgent()
headers = {
    'User-Agent': ua.random.strip(),
    'referer': 'https://howlongtobeat.com/'
}

resp = requests.get('https://howlongtobeat.com/', headers=headers, timeout=60)
print(f"Response status: {resp.status_code}\n")

if resp.status_code == 200:
    soup = BeautifulSoup(resp.text, 'html.parser')
    scripts = soup.find_all('script', src=True)
    
    print(f"Found {len(scripts)} script tags\n")
    print("=" * 80)
    
    # Look for _app- scripts (the ones that usually have the API key)
    app_scripts = [s for s in scripts if '_app-' in s['src']]
    print(f"\nFound {len(app_scripts)} _app- scripts:")
    for s in app_scripts:
        print(f"  - {s['src']}")
    
    # Get the first _app- script
    if app_scripts:
        script_url = 'https://howlongtobeat.com' + app_scripts[0]['src']
        print(f"\nFetching: {script_url}")
        script_resp = requests.get(script_url, headers=headers, timeout=60)
        
        if script_resp.status_code == 200:
            script_content = script_resp.text
            print(f"Script size: {len(script_content)} characters\n")
            
            # Test Pattern 1: users:{id:"..."
            print("=" * 80)
            print("TEST 1: Looking for users:{id:\"...\"")
            print("=" * 80)
            pattern1 = r'users\s*:\s*{\s*id\s*:\s*"([^"]+)"'
            matches1 = re.findall(pattern1, script_content)
            if matches1:
                print(f"✅ FOUND {len(matches1)} matches:")
                for i, m in enumerate(matches1[:5]):
                    print(f"  {i+1}. '{m}'")
            else:
                print("❌ No matches found")
            
            # Test Pattern 2: fetch("/api/...".concat
            print("\n" + "=" * 80)
            print("TEST 2: Looking for fetch(\"/api/...\".concat pattern")
            print("=" * 80)
            pattern2 = r'\/api\/\w+\/"(?:\.concat\("[^"]*"\))*'
            matches2 = re.findall(pattern2, script_content)
            if matches2:
                print(f"✅ FOUND {len(matches2)} matches:")
                for i, m in enumerate(matches2[:5]):
                    print(f"  {i+1}. '{m}'")
            else:
                print("❌ No matches found")
            
            # Look for any /api/ references
            print("\n" + "=" * 80)
            print("TEST 3: Looking for ANY /api/ references")
            print("=" * 80)
            api_refs = re.findall(r'["\']\/api\/[^"\']{0,100}["\']', script_content)
            if api_refs:
                print(f"✅ FOUND {len(api_refs)} API references:")
                unique_refs = list(set(api_refs))[:10]
                for i, ref in enumerate(unique_refs):
                    print(f"  {i+1}. {ref}")
            else:
                print("❌ No /api/ references found")
            
            # Look for fetch() calls
            print("\n" + "=" * 80)
            print("TEST 4: Looking for fetch() calls with /api/")
            print("=" * 80)
            fetch_pattern = r'fetch\([^)]{0,200}\/api\/[^)]{0,200}\)'
            fetch_calls = re.findall(fetch_pattern, script_content)
            if fetch_calls:
                print(f"✅ FOUND {len(fetch_calls)} fetch calls:")
                for i, call in enumerate(fetch_calls[:5]):
                    # Clean it up for display
                    clean_call = call.replace('\n', ' ').replace('  ', ' ')[:150]
                    print(f"  {i+1}. {clean_call}...")
            else:
                print("❌ No fetch calls found")
            
            # Look for common API key formats
            print("\n" + "=" * 80)
            print("TEST 5: Looking for UUID/hash-like strings (potential API keys)")
            print("=" * 80)
            # Look for strings like: "a1b2c3d4e5f6..." (hex), UUIDs, etc.
            hash_pattern = r'"([a-f0-9]{16,64})"'
            hashes = re.findall(hash_pattern, script_content)
            if hashes:
                unique_hashes = list(set(hashes))[:10]
                print(f"✅ FOUND {len(unique_hashes)} unique hash-like strings:")
                for i, h in enumerate(unique_hashes):
                    print(f"  {i+1}. '{h}'")
            else:
                print("❌ No hash-like strings found")
            
            # Look for concat chains
            print("\n" + "=" * 80)
            print("TEST 6: Looking for .concat() chains")
            print("=" * 80)
            concat_pattern = r'\.concat\([^)]+\)(?:\.concat\([^)]+\))*'
            concats = re.findall(concat_pattern, script_content)
            if concats:
                print(f"✅ FOUND {len(concats)} concat chains:")
                for i, c in enumerate(concats[:5]):
                    clean_c = c[:100]
                    print(f"  {i+1}. {clean_c}...")
            else:
                print("❌ No concat chains found")
                
            # Save a sample of the script for manual inspection
            print("\n" + "=" * 80)
            print("Saving first 5000 chars to debug_script_sample.txt")
            print("=" * 80)
            with open('debug_script_sample.txt', 'w', encoding='utf-8') as f:
                f.write(script_content[:5000])
            print("✅ Saved!")
            
        else:
            print(f"❌ Failed to fetch script: {script_resp.status_code}")
    else:
        print("❌ No _app- scripts found")
        
else:
    print(f"❌ Failed to fetch homepage: {resp.status_code}")
