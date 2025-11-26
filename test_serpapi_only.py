"""
Test that the Flask app works with SerpAPI only (HLTB disabled)
"""

import requests
import json

API_URL = "http://127.0.0.1:5000/search-game"
API_KEY = "tuviejovich"  # Your test API key

def test_search():
    print("Testing Flask API with SerpAPI only (HLTB disabled)...")
    print("=" * 60)
    
    test_games = [
        "Halo Combat Evolved",
        "Celeste",
        "The Witcher 3"
    ]
    
    for game in test_games:
        print(f"\nTesting: {game}")
        print("-" * 40)
        
        payload = {
            "GSHEET_API_KEY": API_KEY,
            "game_name": game
        }
        
        try:
            response = requests.post(API_URL, json=payload, timeout=30)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS!")
                print(f"   Main Story: {data.get('main_story')} hours")
                print(f"   Main + Extra: {data.get('main_extra')} hours")
                print(f"   Completionist: {data.get('completionist')} hours")
                print(f"   Source: {data.get('source', 'unknown')}")
            else:
                print(f"❌ FAILED: {response.text}")
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Test complete!")

if __name__ == "__main__":
    print("\n⚠️  Make sure Flask app is running on port 5000!")
    print("   Run: python app.py")
    print("   Or: flask run\n")
    input("Press Enter when ready...")
    test_search()
