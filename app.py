from flask import Flask, request, jsonify
from flask_cors import CORS

from howlongtobeatpy import HowLongToBeat
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
# Cache structure: {normalized_game_name: (result, timestamp)}
CACHE = {}
CACHE_TTL_HOURS = 24 * 7  # Cache for 1 week


def normalize_cache_key(game_name):
    """Normalize game name for consistent cache keys."""
    # Lowercase, strip, remove extra spaces, remove special chars
    key = game_name.lower().strip()
    key = re.sub(r'\s+', ' ', key)  # collapse multiple spaces
    key = re.sub(r'[^\w\s]', '', key)  # remove special chars like : and -
    return key


def get_cached_result(game_name):
    """Get cached result if available and not expired."""
    cache_key = normalize_cache_key(game_name)
    if cache_key in CACHE:
        result, timestamp = CACHE[cache_key]
        age = datetime.now() - timestamp
        if age < timedelta(hours=CACHE_TTL_HOURS):
            logger.info(f"Cache hit for '{game_name}' (key: {cache_key}, age: {age})")
            return result
        else:
            logger.info(f"Cache expired for '{game_name}'")
            del CACHE[cache_key]
    return None


def set_cached_result(game_name, result):
    """Cache the result with current timestamp using normalized key."""
    cache_key = normalize_cache_key(game_name)
    CACHE[cache_key] = (result, datetime.now())
    logger.info(f"Cached result for '{game_name}' (key: {cache_key}, cache size: {len(CACHE)})")


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
    Search for game time data using the HowLongToBeat API (howlongtobeatpy).
    Returns the first result or filters by year if provided.
    """
    try:
        results = await asyncio.wait_for(
            HowLongToBeat().async_search(game_name), timeout=timeout
        )

        if results is None:
            logger.warning(
                f"search_howlongtobeat - HLTB returned None for: {game_name}"
            )
            return None

        if not results or len(results) == 0:
            logger.info(f"search_howlongtobeat - No results found for: {game_name}")
            return None

        logger.info(f"search_howlongtobeat - found {len(results)} results")

    except asyncio.TimeoutError:
        logger.error(f"HLTB search timed out after {timeout}s for: {game_name}")
        return None
    except Exception as e:
        logger.error(f"HLTB search failed for '{game_name}': {str(e)}", exc_info=True)
        return None

    if year:
        logger.debug(f"Filtering results by year: {year}")
        matching_results = [
            r
            for r in results
            if getattr(r, "release_world", None) and str(year) in str(r.release_world)
        ]

        if matching_results:
            logger.info(f"Found {len(matching_results)} matching year results")
            result = matching_results[0]
        else:
            logger.info(f"Year {year} not found, using first result")
            result = results[0]
    else:
        logger.debug("No year provided, using first result")
        result = results[0]

    logger.info(
        f"search_howlongtobeat - selected: {getattr(result, 'game_name', None) if result else 'None'}"
    )
    return result


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


def search_hltb_with_serpapi(game_name):
    """
    Search for HowLongToBeat data using SerpAPI with 'howlongtobeat GAMENAME' query.
    Extracts playtime from Google's featured snippets and HLTB organic results.
    """
    if not SERP_API_KEY:
        logger.warning("SERP_API_KEY not configured")
        return None

    query = f"howlongtobeat {game_name}"
    logger.info(f"search_hltb_with_serpapi - query: {query}")

    try:
        params = {
            "q": query,
            "api_key": SERP_API_KEY,
            "num": 5,  # Only need first few results
        }
        search = GoogleSearch(params)
        results = search.get_dict()

        # Pattern to match time formats - MUST have Hours/hrs suffix
        # Handles: "10 Hours", "10.5 hrs", "10-12 Hours", "6½ Hours"
        time_pattern = r"(\d+(?:[½¼¾]|\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*(?:Hours?|hrs?)"
        
        # Pattern to detect "X hours a day" or "X hours per day" which is a RATE, not total time
        # We must SKIP these matches! e.g. "6 Days to complete if you play for 1.5 hours a day"
        rate_pattern = r"\d+(?:\.\d+)?\s*(?:hours?|hrs?)\s*(?:a|per)\s*day"

        data = {
            "main_story": None,
            "main_extra": None,
            "completionist": None,
        }

        # Check answer_box first (Google's featured snippet)
        if "answer_box" in results:
            answer_text = results["answer_box"].get("answer", "") or results[
                "answer_box"
            ].get("snippet", "")
            logger.debug(f"Found answer_box: {answer_text[:150]}")
            
            # Skip if this contains "hours per day" format (rate, not total time)
            if re.search(rate_pattern, answer_text, re.IGNORECASE):
                logger.info("Skipping answer_box - contains 'hours per day' rate format")
            else:
                matches = re.findall(time_pattern, answer_text, re.IGNORECASE)
                if matches:
                    # Parse and validate times
                    parsed_times = [parse_time_to_hours(m) for m in matches]
                    valid_times = [t for t in parsed_times if t is not None and 0.25 <= t <= 500]
                    
                    if valid_times:
                        data["main_story"] = valid_times[0]
                        if len(valid_times) > 1:
                            data["main_extra"] = valid_times[1]
                        if len(valid_times) > 2:
                            data["completionist"] = valid_times[2]

        # Check organic results for HLTB links (only if no data yet)
        if not data["main_story"]:
            for result in results.get("organic_results", []):
                link = result.get("link", "")
                snippet = result.get("snippet", "")

                # Only process howlongtobeat.com/game links
                if "howlongtobeat.com/game" in link and snippet:
                    logger.info(f"Found HLTB result: {snippet[:150]}")
                    
                    # Skip if this contains "hours per day" format (rate, not total time)
                    if re.search(rate_pattern, snippet, re.IGNORECASE):
                        logger.info("Skipping snippet - contains 'hours per day' rate format")
                        continue

                    # Try to extract specific types first
                    main_match = re.search(
                        r"main\s*story[:\s]*" + time_pattern, snippet, re.IGNORECASE
                    )
                    if main_match:
                        parsed = parse_time_to_hours(main_match.group(1))
                        if parsed and 0.25 <= parsed <= 500:
                            data["main_story"] = parsed

                    comp_match = re.search(
                        r"(?:completionist|100%)[:\s]*" + time_pattern,
                        snippet,
                        re.IGNORECASE,
                    )
                    if comp_match:
                        parsed = parse_time_to_hours(comp_match.group(1))
                        if parsed and 0.25 <= parsed <= 500:
                            data["completionist"] = parsed

                    # Fallback: Extract all times from snippet
                    if not data["main_story"]:
                        matches = re.findall(time_pattern, snippet, re.IGNORECASE)
                        if matches:
                            parsed_times = [parse_time_to_hours(m) for m in matches]
                            valid_times = [t for t in parsed_times if t is not None and 0.25 <= t <= 500]
                            if valid_times:
                                data["main_story"] = valid_times[0]
                                logger.info(f"Fallback extraction: found {valid_times}, using {valid_times[0]}")

                    # If we found main_story data, stop searching
                    if data["main_story"]:
                        break

        if data["main_story"]:
            logger.info(
                f"Extracted HLTB data: main={data['main_story']}, comp={data['completionist']}"
            )
            return data
        else:
            logger.info("No HLTB data found in SerpAPI results")
            return None

    except Exception as e:
        logger.error(f"HLTB SerpAPI search failed: {str(e)}")
        return None


def parse_time_to_hours(time_str):
    """
    Convert time string to hours float.
    Handles: "10" -> 10.0, "10.5" -> 10.5, "10-12" -> 11.0 (average)
    Also handles unicode fractions: "6½" -> 6.5, "10¼" -> 10.25
    """
    if time_str is None:
        return None
        
    time_str = str(time_str).strip()
    
    # Handle unicode fractions first
    time_str = time_str.replace('½', '.5')
    time_str = time_str.replace('¼', '.25')
    time_str = time_str.replace('¾', '.75')

    if "-" in time_str:
        parts = time_str.split("-")
        try:
            low = float(parts[0])
            high = float(parts[1])
            return (low + high) / 2
        except:
            try:
                return float(parts[0])
            except:
                return None

    try:
        return float(time_str)
    except:
        return None


def remove_year_from_query(query, year):
    """Remove the year from the query string (e.g., 'God of War (2005 video game)' -> 'God of War')"""
    logger.debug(f"remove_year_from_query - original query: {query}, year: {year}")
    cleaned_query = re.sub(
        r"\(\d{4}(?:\s*video\s*game|\s*videogame|\s*series)?\)", "", query
    ).strip()
    logger.debug(f"remove_year_from_query - cleaned query: {cleaned_query}")
    return cleaned_query


async def search_game(game_name):
    """
    Search for game playtime using SerpAPI.

    Strategy:
    1. Try direct HLTB search via SerpAPI: "howlongtobeat GAMENAME"
    2. Fallback to Wikipedia search if no HLTB data found
    """
    logger.info(f"Starting search for: {game_name}")

    year = extract_year(game_name)
    cleaned_name = clean_title(game_name)

    # Attempt 1: Use howlongtobeatpy as main source
    hltb_result = await search_howlongtobeat(cleaned_name, year)
    if hltb_result:
        logger.info(f"✅ [HLTB_PY] Found HLTB data via howlongtobeatpy for: {cleaned_name} - main_story: {getattr(hltb_result, 'main_story', None)}")
        hltb_result._source = 'hltbpy'
        return hltb_result

    # Attempt 2: Fallback to SerpAPI if no result from howlongtobeatpy
    logger.info("[HLTB_SERPAPI] No HLTB data from package, trying SerpAPI fallback")
    hltb_data = search_hltb_with_serpapi(cleaned_name)
    if hltb_data:
        logger.info(f"✅ [HLTB_SERPAPI] Found HLTB data via SerpAPI for: {cleaned_name} - main_story: {hltb_data.get('main_story', None)}")
        class HLTBResult:
            def __init__(self, main, extra, comp, name):
                self.main_story = main
                self.main_extra = extra
                self.completionist = comp
                self.game_name = name
                self._source = 'serpapi'
        return HLTBResult(
            hltb_data["main_story"],
            hltb_data["main_extra"],
            hltb_data["completionist"],
            cleaned_name,
        )

    logger.warning(f"No HLTB data found after all attempts for: {game_name}")
    return None


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

    # Build response - handle both old HowLongToBeatEntry and new HLTBResult objects
    response_data = {
        "game_name": result.game_name if hasattr(result, "game_name") else game_name,
        "main_story": result.main_story if hasattr(result, "main_story") else None,
        "main_extra": result.main_extra if hasattr(result, "main_extra") else None,
        "completionist": (
            result.completionist if hasattr(result, "completionist") else None
        ),
        "all_styles": result.all_styles if hasattr(result, "all_styles") else None,
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
