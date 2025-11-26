"""
Test if SerpAPI can extract HowLongToBeat data from search results
by using "howlongtobeat GAMENAME" query
"""

import os
from serpapi import GoogleSearch
import json

SERP_API_KEY = os.getenv("SERP_API_KEY", "your_key_here")

def test_hltb_via_serpapi(game_name):
    """Test searching 'howlongtobeat GAMENAME' to get HLTB data"""
    
    query = f"howlongtobeat {game_name}"
    print(f"\nTesting: {query}")
    print("-" * 60)
    
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "num": 10
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    
    # Save full results for inspection
    filename = f"serp_hltb_{game_name.replace(' ', '_')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Full results saved to: {filename}")
    
    # Check for answer_box (featured snippet)
    if "answer_box" in results:
        print("\n✅ Found answer_box!")
        answer = results["answer_box"]
        print(json.dumps(answer, indent=2))
    
    # Check for knowledge_graph
    if "knowledge_graph" in results:
        print("\n✅ Found knowledge_graph!")
        kg = results["knowledge_graph"]
        print(json.dumps(kg, indent=2))
    
    # Check organic results
    print("\n📄 Organic Results:")
    for i, result in enumerate(results.get("organic_results", [])[:3], 1):
        print(f"\n{i}. {result.get('title')}")
        print(f"   Link: {result.get('link')}")
        print(f"   Snippet: {result.get('snippet', '')[:150]}")
        
        # Check for rich_snippet or other data
        if "rich_snippet" in result:
            print(f"   Rich Snippet: {result['rich_snippet']}")
    
    return results

# Test with various games
test_games = [
    "Celeste",
    "Seven Samurai 20XX",
    "Halo Combat Evolved",
    "The Witcher 3",
    "Undertale",
    "Hollow Knight",
    # More obscure
    "Caves of Qud",
    "Dishonored",
]

print("=" * 60)
print("Testing HowLongToBeat data via SerpAPI")
print("=" * 60)

for game in test_games:
    try:
        results = test_hltb_via_serpapi(game)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("=" * 60)

print("\n✅ Testing complete! Check the saved JSON files for details.")
