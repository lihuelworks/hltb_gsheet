"""
Test synchronous search method
"""
from howlongtobeatpy import HowLongToBeat

print("Testing synchronous search...")

test_games = ["Celeste", "Halo Combat Evolved", "The Witcher 3"]

for game in test_games:
    print(f"\nSearching for: {game}")
    try:
        results = HowLongToBeat().search(game)
        print(f"  Type: {type(results)}")
        print(f"  Value: {results}")
        
        if results is None:
            print(f"  ❌ Returned None")
        elif len(results) == 0:
            print(f"  ⚠️  Empty list")
        else:
            print(f"  ✅ Found {len(results)} results")
            best = max(results, key=lambda x: x.similarity)
            print(f"  Best: {best.game_name} (similarity: {best.similarity})")
            print(f"  Main story: {best.main_story} hours")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
print("Testing with similarity=0.0")
print("="*60)

for game in ["Celeste", "Halo 1"]:
    print(f"\nSearching for: {game}")
    try:
        results = HowLongToBeat(0.0).search(game)
        print(f"  Results: {len(results) if results else 'None'}")
        if results and len(results) > 0:
            print(f"  ✅ First: {results[0].game_name}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
