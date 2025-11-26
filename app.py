from flask import Flask, request, jsonify
from flask_cors import CORS
# TEMPORARILY DISABLED: HLTB library is broken due to bot protection (see GitHub issue)
# from howlongtobeatpy import HowLongToBeat
from serpapi import GoogleSearch
import re
import asyncio
import os
import logging
from datetime import datetime, timedelta
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Load environment variables
GSHEET_API_KEY = os.getenv("GSHEET_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")

# Validate environment variables at startup
if not GSHEET_API_KEY:
    logger.error("GSHEET_API_KEY environment variable is not set!")
    raise ValueError("GSHEET_API_KEY must be set")

if not SERP_API_KEY:
    logger.warning("SERP_API_KEY not set - SerpAPI fallback will not work")

# In-memory cache with TTL (will reset on Render restart, but that's fine)
# Cache structure: {game_name: (result, timestamp)}
CACHE = {}
CACHE_TTL_HOURS = 24 * 7  # Cache for 1 week


def get_cached_result(game_name):
    """Get cached result if available and not expired."""
    if game_name in CACHE:
        result, timestamp = CACHE[game_name]
        age = datetime.now() - timestamp
        if age < timedelta(hours=CACHE_TTL_HOURS):
            logger.info(f"Cache hit for '{game_name}' (age: {age})")
            return result
        else:
            logger.info(f"Cache expired for '{game_name}'")
            del CACHE[game_name]
    return None


def set_cached_result(game_name, result):
    """Cache the result with current timestamp."""
    CACHE[game_name] = (result, datetime.now())
    logger.info(f"Cached result for '{game_name}' (cache size: {len(CACHE)})")


def clean_title(title):
    """Cleans up the title by removing unwanted prefixes, suffixes, and special terms."""
    logger.debug(f"clean_title - original title: {title}")
    unwanted_prefixes = [
        "Buy",
        "Download",
        "Amazon.com",
        "Steam",
        "PlayStation Store",
        "Xbox Store",
        "Wikipedia",
        "IMDb",
        "Fandom",
        "Video",
        "Game",
        "Games",
    ]
    unwanted_suffixes = [
        "on",
        "at",
        "for",
        "in",
        "the",
        "a",
        "an",
        "by",
        "with",
        "from",
        "to",
    ]
    unwanted_terms = [
        "wikipedia",
        "steam",
        "buy",
        "game",
        "video",
        "playstation",
        "xbox",
        "fandom",
        "amazon",
        "download",
        "old",
        "games",
        "imdb",
        "on",
    ]

    # Remove unwanted prefixes
    for prefix in unwanted_prefixes:
        if title.lower().startswith(prefix.lower()):
            logger.debug(f"clean_title - removing prefix: {prefix}")
            title = title[len(prefix) :].strip()

    # Remove unwanted suffixes
    for suffix in unwanted_suffixes:
        if title.lower().endswith(suffix.lower()):
            logger.debug(f"clean_title - removing suffix: {suffix}")
            title = title[: -len(suffix)].strip()

    # Remove any unwanted terms
    words = title.split()
    cleaned_words = [word for word in words if word.lower() not in unwanted_terms]
    cleaned_title = " ".join(cleaned_words).strip()
    logger.debug(f"clean_title - cleaned title: {cleaned_title}")
    return cleaned_title


def extract_year(title):
    """Extract the year from the title, e.g., (2005), (Video 2005), etc."""
    match = re.search(r"\(.*?(\d{4})\).*?", title)
    if match:
        year = int(match.group(1))
        logger.debug(f"extract_year - found year: {year}")
        return year
    logger.debug("extract_year - no year found")
    return None


def normalize_query(query):
    """Normalize and remove special characters like '™', '®' etc., and unnecessary suffixes like (PS2)"""
    logger.debug(f"normalize_query - original query: {query}")
    query = query.replace("™", "").replace("®", "").replace("©", "")
    query = re.sub(
        r"\(.*?\)", "", query
    )  # Remove everything inside parentheses (PS2, video game, etc.)
    query = re.sub(r"[^\x00-\x7F]+", "", query)  # Remove any non-ASCII characters
    cleaned_query = query.strip()
    logger.debug(f"normalize_query - cleaned query: {cleaned_query}")
    return cleaned_query


async def search_howlongtobeat(game_name, year=None, timeout=10):
    """
    TEMPORARILY DISABLED: HowLongToBeat library is non-functional due to aggressive bot protection.
    
    As of November 2025, HLTB has implemented bot protection that blocks all programmatic API access
    with 403 "Session expired" errors. The Python library (howlongtobeatpy) cannot bypass this.
    
    See GitHub issue: https://github.com/ScrappyCocco/HowLongToBeat-PythonAPI/issues/[TBD]
    
    This function now returns None to force fallback to SerpAPI which works reliably.
    """
    logger.info(f"search_howlongtobeat - DISABLED due to bot protection. Game: {game_name}")
    logger.info("Falling back to SerpAPI for game time data")
    return None
    
    # ORIGINAL CODE COMMENTED OUT - DO NOT USE UNTIL BOT PROTECTION IS RESOLVED
    # try:
    #     results = await asyncio.wait_for(
    #         HowLongToBeat().async_search(game_name), timeout=timeout
    #     )
    #     
    #     if results is None:
    #         logger.warning(f"search_howlongtobeat - HLTB returned None for: {game_name}")
    #         return None
    #     
    #     if not results or len(results) == 0:
    #         logger.info(f"search_howlongtobeat - No results found for: {game_name}")
    #         return None
    #         
    #     logger.info(f"search_howlongtobeat - found {len(results)} results")
    #     
    # except asyncio.TimeoutError:
    #     logger.error(f"HLTB search timed out after {timeout}s for: {game_name}")
    #     return None
    # except Exception as e:
    #     logger.error(f"HLTB search failed for '{game_name}': {str(e)}", exc_info=True)
    #     return None
    #
    # if year:
    #     logger.debug(f"Filtering results by year: {year}")
    #     matching_results = [
    #         r for r in results if r.release_world and str(year) in str(r.release_world)
    #     ]
    #
    #     if matching_results:
    #         logger.info(f"Found {len(matching_results)} matching year results")
    #         result = matching_results[0]
    #     else:
    #         logger.info(f"Year {year} not found, using first result")
    #         result = results[0]
    # else:
    #     logger.debug("No year provided, using first result")
    #     result = results[0]
    #
    # logger.info(
    #     f"search_howlongtobeat - selected: {result.game_name if result else 'None'}"
    # )
    # return result


def search_with_serpapi(query):
    """Search Google via SerpAPI, prioritizing Wikipedia results."""
    if not SERP_API_KEY:
        logger.warning("SERP_API_KEY not configured, skipping SerpAPI search")
        return []

    logger.info(f"search_with_serpapi - searching for: {query}")

    try:
        params = {
            "q": f"{query} videogame site:wikipedia.org",
            "api_key": SERP_API_KEY,
        }
        search = GoogleSearch(params)
        results = search.get_dict().get("organic_results", [])
        logger.info(f"search_with_serpapi - found {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"SerpAPI search failed for '{query}': {str(e)}")
        return []


def remove_year_from_query(query, year):
    """Remove the year from the query string (e.g., 'God of War (2005 video game)' -> 'God of War')"""
    logger.debug(f"remove_year_from_query - original query: {query}, year: {year}")
    cleaned_query = re.sub(
        r"\(\d{4}(?:\s*video\s*game|\s*videogame|\s*series)?\)", "", query
    ).strip()
    logger.debug(f"remove_year_from_query - cleaned query: {cleaned_query}")
    return cleaned_query


async def search_game(game_name):
    """Search the game name using multiple methods (HLTB and SerpAPI)."""
    logger.info(f"Starting search for: {game_name}")

    year = extract_year(game_name)
    cleaned_name = clean_title(game_name)

    # Attempt 1: Search HLTB with cleaned name
    logger.info("Attempt 1: Searching HLTB with cleaned name")
    hltb_result = await search_howlongtobeat(cleaned_name, year)

    # Attempt 2: If no result, try with SerpAPI fallback
    if not hltb_result and SERP_API_KEY:
        logger.info("Attempt 2: Trying SerpAPI search")
        serpapi_results = search_with_serpapi(cleaned_name)
        best_result = serpapi_results[0] if serpapi_results else None

        if best_result:
            cleaned_best_match = clean_title(best_result["title"])
            cleaned_best_match = normalize_query(cleaned_best_match)
            cleaned_best_match = remove_year_from_query(cleaned_best_match, year)
            logger.info(f"Best Match from SerpAPI: {cleaned_best_match}")

            if cleaned_best_match.lower() == game_name.lower():
                cleaned_best_match = game_name
            hltb_result = await search_howlongtobeat(cleaned_best_match, year)

    if hltb_result:
        logger.info(f"Final result found: {hltb_result.game_name}")
    else:
        logger.warning(f"No results found after all attempts for: {game_name}")

    return hltb_result


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring."""
    return (
        jsonify(
            {
                "status": "healthy",
                "cache_size": len(CACHE),
                "serp_api_configured": bool(SERP_API_KEY),
            }
        ),
        200,
    )


@app.route("/search-game", methods=["POST"])
def search_game_route():
    """Endpoint to search for a game."""
    try:
        data = request.get_json()
    except Exception as e:
        logger.error(f"Invalid JSON payload: {str(e)}")
        return jsonify({"error": "Invalid JSON"}), 400

    # Validate API key
    if "GSHEET_API_KEY" not in data or data["GSHEET_API_KEY"] != GSHEET_API_KEY:
        logger.warning("Invalid or missing API key in request")
        return jsonify({"error": "Invalid or missing GSHEET_API_KEY"}), 401

    game_name = data.get("game_name")
    if not game_name:
        logger.warning("Missing game_name in request")
        return jsonify({"error": "game_name is required"}), 400

    # Check cache first
    cached_result = get_cached_result(game_name)
    if cached_result:
        logger.info(f"Returning cached result for: {game_name}")
        return jsonify(cached_result), 200

    # Perform the search
    try:
        result = asyncio.run(search_game(game_name))
    except Exception as e:
        logger.error(f"Search failed for '{game_name}': {str(e)}")
        return jsonify({"error": "Internal server error during search"}), 500

    if not result:
        logger.info(f"No results found for: {game_name}")
        return jsonify({"error": "No results found"}), 404

    # Build response
    response_data = {
        "game_name": result.game_name,
        "main_story": result.main_story,
        "main_extra": result.main_extra,
        "completionist": result.completionist,
        "all_styles": result.all_styles,
    }

    # Cache the result
    set_cached_result(game_name, response_data)

    return jsonify(response_data), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Starting server on port {port}")
    logger.info(f"GSHEET_API_KEY configured: {bool(GSHEET_API_KEY)}")
    logger.info(f"SERP_API_KEY configured: {bool(SERP_API_KEY)}")
    app.run(debug=False, host="0.0.0.0", port=port)
