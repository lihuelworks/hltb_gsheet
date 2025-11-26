"""
Alternative HLTB implementation using the C# API service
Can be integrated into app.py if you deploy the C# service
"""

import requests
import logging

logger = logging.getLogger(__name__)

CSHARP_HLTB_API_URL = "https://your-csharp-api.onrender.com"  # Replace with your deployment URL

def search_game_csharp_hltb(game_name):
    """
    Search for a game using the C# HowLongToBeat API service.
    
    The C# API bypasses bot protection and provides cached results.
    
    Note: This requires deploying the C# API separately:
    https://codeberg.org/Crashdummy/HowLongToBeatApi
    
    @param game_name: Name of the game to search
    @return: Dict with playtime data or None
    """
    try:
        # The C# API has multiple search methods:
        # 1. /hltb/search - direct search
        # 2. /steam/{appId} - via Steam AppID
        # 3. /gog/{appId} - via GOG AppID
        
        # For simplicity, we'll use direct search
        # You might need to adjust based on actual API docs
        
        url = f"{CSHARP_HLTB_API_URL}/hltb/search"
        payload = {
            "searchTerm": game_name,
            "matchType": "fuzzy"
        }
        
        logger.info(f"Searching C# HLTB API for: {game_name}")
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            results = response.json()
            
            if not results or len(results) == 0:
                logger.info(f"No results from C# API for: {game_name}")
                return None
            
            # Get first result
            game = results[0]
            
            return {
                "main_story": game.get("mainStory"),
                "main_extra": game.get("mainStoryWithExtras"),
                "completionist": game.get("completionist"),
                "game_name": game.get("title"),
                "hltb_id": game.get("hltbId"),
                "source": "csharp_hltb_api"
            }
        else:
            logger.error(f"C# API returned {response.status_code}: {response.text[:200]}")
            return None
            
    except Exception as e:
        logger.error(f"Error calling C# HLTB API: {str(e)}")
        return None


# Integration example for app.py:
"""
# In app.py, replace search_howlongtobeat() with:

async def search_howlongtobeat(game_name, year=None, timeout=10):
    '''Search using C# HLTB API service (bypasses bot protection)'''
    
    # Try C# API first
    result = search_game_csharp_hltb(game_name)
    
    if result:
        logger.info(f"Found via C# API: {result['game_name']}")
        return result
    
    # Fallback to SerpAPI if C# API fails
    logger.info("C# API failed, falling back to SerpAPI")
    return None  # Will trigger SerpAPI fallback in main search
"""
