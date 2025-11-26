"""
Deep diagnostics for HowLongToBeat library
"""
import asyncio
from howlongtobeatpy import HowLongToBeat

async def test_with_debug():
    """Test with verbose output"""
    print("Testing HLTB with debug info...")
    
    # Test 1: Simple search
    print("\n1. Simple search for 'Celeste':")
    try:
        hltb = HowLongToBeat()
        print(f"   HowLongToBeat object: {hltb}")
        
        results = await hltb.async_search("Celeste")
        print(f"   Results type: {type(results)}")
        print(f"   Results value: {results}")
        
        if results:
            print(f"   Length: {len(results)}")
            if len(results) > 0:
                print(f"   First result: {results[0]}")
    except Exception as e:
        print(f"   Exception: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Check library version
    print("\n2. Library information:")
    try:
        import howlongtobeatpy
        print(f"   Module path: {howlongtobeatpy.__file__}")
        if hasattr(howlongtobeatpy, '__version__'):
            print(f"   Version: {howlongtobeatpy.__version__}")
    except Exception as e:
        print(f"   Error getting version: {e}")
    
    # Test 3: Try synchronous search if available
    print("\n3. Checking available methods:")
    hltb = HowLongToBeat()
    methods = [m for m in dir(hltb) if not m.startswith('_')]
    print(f"   Available methods: {methods}")

asyncio.run(test_with_debug())

print("\n" + "="*60)
print("Checking internet connectivity to HLTB...")
print("="*60)

import urllib.request
import ssl

# Try to connect to HowLongToBeat website
try:
    context = ssl.create_default_context()
    response = urllib.request.urlopen('https://howlongtobeat.com', context=context, timeout=5)
    print(f"✅ Can reach howlongtobeat.com (status: {response.status})")
except Exception as e:
    print(f"❌ Cannot reach howlongtobeat.com: {e}")
