"""
Test script to verify HLTB and SerpAPI functionality
Run with: python test_apis.py
"""
import asyncio
import os
from howlongtobeatpy import HowLongToBeat
from serpapi import GoogleSearch

# Load from environment or use test values
SERP_API_KEY = os.getenv("SERP_API_KEY", "your_key_here")

print("=" * 60)
print("Testing HowLongToBeat API")
print("=" * 60)

async def test_hltb():
    """Test HLTB with various game names"""
    test_games = [
        "Halo 1",
        "Halo Combat Evolved",
        "Seven Samurai 20XX",
        "Celeste",
        "The Witcher 3"
    ]
    
    for game in test_games:
        print(f"\nSearching for: {game}")
        try:
            results = await HowLongToBeat().async_search(game)
            print(f"  Type: {type(results)}")
            print(f"  Value: {results}")
            
            if results is None:
                print(f"  ❌ Returned None")
            elif len(results) == 0:
                print(f"  ⚠️  Empty list")
            else:
                print(f"  ✅ Found {len(results)} results")
                best = max(results, key=lambda x: x.similarity)
                print(f"  Best match: {best.game_name}")
                print(f"  Main story: {best.main_story} hours")
                print(f"  Similarity: {best.similarity}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

print("\nRunning HLTB tests...")
asyncio.run(test_hltb())

print("\n" + "=" * 60)
print("Testing SerpAPI")
print("=" * 60)

def test_serpapi():
    """Test SerpAPI searches"""
    if not SERP_API_KEY or SERP_API_KEY == "your_key_here":
        print("\n⚠️  SERP_API_KEY not set - skipping SerpAPI tests")
        print("Set environment variable: SERP_API_KEY=your_key")
        return
    
    test_queries = [
        "Halo 1",
        "Seven Samurai 20XX"
    ]
    
    for query in test_queries:
        print(f"\nSearching for: {query}")
        try:
            params = {
                "q": f"{query} videogame site:wikipedia.org",
                "api_key": SERP_API_KEY,
            }
            search = GoogleSearch(params)
            results = search.get_dict().get("organic_results", [])
            
            if len(results) == 0:
                print(f"  ⚠️  No results")
            else:
                print(f"  ✅ Found {len(results)} results")
                if results:
                    print(f"  Best match: {results[0].get('title', 'N/A')}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

print("\nRunning SerpAPI tests...")
test_serpapi()

print("\n" + "=" * 60)
print("Testing with lower similarity threshold")
print("=" * 60)

async def test_hltb_low_similarity():
    """Test HLTB with 0 similarity (return all results)"""
    test_games = ["Halo 1", "Seven Samurai 20XX"]
    
    for game in test_games:
        print(f"\nSearching for: {game} (similarity=0)")
        try:
            results = await HowLongToBeat(0.0).async_search(game)
            
            if results is None:
                print(f"  ❌ Returned None")
            elif len(results) == 0:
                print(f"  ⚠️  Empty list")
            else:
                print(f"  ✅ Found {len(results)} results (unfiltered)")
                for i, r in enumerate(results[:5]):  # Show first 5
                    print(f"  {i+1}. {r.game_name} (similarity: {r.similarity})")
        except Exception as e:
            print(f"  ❌ Error: {e}")

print("\nRunning low similarity tests...")
asyncio.run(test_hltb_low_similarity())

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
