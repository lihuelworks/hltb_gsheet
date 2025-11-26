"""
Analyze the existing serp_halo1_example.json to see if it has HLTB data
"""

import json

with open('serp_halo1_example.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Analyzing serp_halo1_example.json for HLTB data")
print("=" * 60)

# Check for answer_box
if "answer_box" in data:
    print("\n✅ Found answer_box:")
    print(json.dumps(data["answer_box"], indent=2))

# Check for knowledge_graph  
if "knowledge_graph" in data:
    print("\n✅ Found knowledge_graph:")
    print(json.dumps(data["knowledge_graph"], indent=2))

# Check organic results for HLTB links
print("\n📄 Checking organic results for HowLongToBeat:")
for i, result in enumerate(data.get("organic_results", []), 1):
    title = result.get('title', '')
    link = result.get('link', '')
    snippet = result.get('snippet', '')
    
    if 'howlongtobeat' in link.lower() or 'howlongtobeat' in title.lower():
        print(f"\n{i}. HLTB RESULT FOUND!")
        print(f"   Title: {title}")
        print(f"   Link: {link}")
        print(f"   Snippet: {snippet}")
        
        # Check for rich snippets or structured data
        if "rich_snippet" in result:
            print(f"   Rich Snippet: {json.dumps(result['rich_snippet'], indent=2)}")

print("\n" + "=" * 60)
print("\nNow let's see what query was used:")
print(f"Query: {data.get('search_parameters', {}).get('q')}")
