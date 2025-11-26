"""
Debug the API key extraction process
"""
from howlongtobeatpy.HTMLRequests import HTMLRequests

print("Testing HLTB API key extraction...")
print("="*60)

# Test 1: Try to get search info
print("\n1. Attempting to extract search info (parse_all=False):")
try:
    search_info = HTMLRequests.send_website_request_getcode(False)
    if search_info:
        print(f"   ✅ Success!")
        print(f"   API Key: {search_info.api_key}")
        print(f"   Search URL: {search_info.search_url}")
    else:
        print(f"   ❌ Returned None")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Try with parse_all=True
print("\n2. Attempting to extract search info (parse_all=True):")
try:
    search_info = HTMLRequests.send_website_request_getcode(True)
    if search_info:
        print(f"   ✅ Success!")
        print(f"   API Key: {search_info.api_key}")
        print(f"   Search URL: {search_info.search_url}")
    else:
        print(f"   ❌ Returned None - Cannot extract API key from HLTB website!")
        print(f"   This means HLTB changed their website structure.")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Diagnosis complete!")
