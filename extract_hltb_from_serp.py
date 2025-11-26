"""
Create a function that extracts HLTB data from SerpAPI results
when searching "howlongtobeat GAMENAME"

Based on Google's featured snippets for HLTB queries
"""

import re

def extract_hltb_from_serpapi(results, game_name):
    """
    Extract HowLongToBeat playtime data from SerpAPI results.
    
    Looks for:
    1. Answer boxes with time information
    2. HLTB organic results with snippets containing playtime
    3. Knowledge graph data
    
    @param results: SerpAPI results dict
    @param game_name: Original game name searched
    @return: Dict with playtime data or None
    """
    
    # Pattern to match time formats like "10 Hours", "10.5 Hours", "10-12 Hours"
    time_pattern = r'(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*(?:Hours?|hrs?)'
    
    data = {
        'main_story': None,
        'main_extra': None, 
        'completionist': None,
        'game_name': game_name,
        'source': 'serpapi_hltb'
    }
    
    # Check answer_box (Google's featured snippet)
    if "answer_box" in results:
        answer = results["answer_box"]
        text = answer.get("answer", "") or answer.get("snippet", "")
        
        print(f"Found answer_box: {text[:200]}")
        
        # Try to extract hours
        matches = re.findall(time_pattern, text, re.IGNORECASE)
        if matches:
            # Usually first match is main story
            data['main_story'] = parse_time_to_hours(matches[0])
            print(f"Extracted main_story: {data['main_story']}")
            
            if len(matches) > 1:
                data['main_extra'] = parse_time_to_hours(matches[1])
            if len(matches) > 2:
                data['completionist'] = parse_time_to_hours(matches[2])
    
    # Check organic results for HLTB links
    for result in results.get("organic_results", []):
        link = result.get("link", "")
        snippet = result.get("snippet", "")
        title = result.get("title", "")
        
        # Look for howlongtobeat.com results
        if "howlongtobeat.com" in link:
            print(f"\nFound HLTB result:")
            print(f"  Title: {title}")
            print(f"  Snippet: {snippet[:150]}")
            
            # Extract times from snippet
            # Common patterns:
            # "8 Hours"  
            # "Main Story: 10 Hours"
            # "10-15 Hours to complete"
            
            matches = re.findall(time_pattern, snippet, re.IGNORECASE)
            if matches and not data['main_story']:
                data['main_story'] = parse_time_to_hours(matches[0])
                print(f"  Extracted: {data['main_story']} hours")
            
            # Try to extract specific playtime types
            if "main story" in snippet.lower():
                main_match = re.search(r'main story[:\s]+' + time_pattern, snippet, re.IGNORECASE)
                if main_match:
                    data['main_story'] = parse_time_to_hours(main_match.group(1))
            
            if "completionist" in snippet.lower() or "100%" in snippet:
                comp_match = re.search(r'(?:completionist|100%)[:\s]+' + time_pattern, snippet, re.IGNORECASE)
                if comp_match:
                    data['completionist'] = parse_time_to_hours(comp_match.group(1))
    
    # Return data if we found at least main_story
    if data['main_story']:
        return data
    
    return None


def parse_time_to_hours(time_str):
    """
    Convert time string to hours float.
    
    Handles:
    - "10" -> 10.0
    - "10.5" -> 10.5
    - "10-12" -> 11.0 (average)
    """
    time_str = time_str.strip()
    
    # Handle ranges like "10-12"
    if '-' in time_str:
        parts = time_str.split('-')
        try:
            low = float(parts[0])
            high = float(parts[1])
            return (low + high) / 2
        except:
            return float(parts[0])
    
    try:
        return float(time_str)
    except:
        return None


# Example test with mock data
if __name__ == "__main__":
    # Simulate what Google returns for "howlongtobeat celeste"
    mock_serpapi_result = {
        "organic_results": [
            {
                "title": "How long is Celeste?",
                "link": "https://howlongtobeat.com/game/42818",
                "snippet": "8 Hours. Inspired by classic platformers, Celeste is an intense platformer with over 700 screens of hardcore challenges. Main Story: 8 Hours. Completionist: 40 Hours."
            }
        ]
    }
    
    result = extract_hltb_from_serpapi(mock_serpapi_result, "Celeste")
    
    if result:
        print("\n✅ Successfully extracted HLTB data!")
        print(f"Main Story: {result['main_story']} hours")
        print(f"Completionist: {result['completionist']} hours")
    else:
        print("\n❌ Could not extract HLTB data")
