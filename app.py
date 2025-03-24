from flask import Flask, request, jsonify
from flask_cors import CORS
from howlongtobeatpy import HowLongToBeat
from serpapi import GoogleSearch
import re
import asyncio
import os

app = Flask(__name__)
CORS(app)

# Load GSHEET_API_KEY from environment variables
GSHEET_API_KEY = os.getenv("GSHEET_API_KEY")


def clean_title(title):
    """Cleans up the title by removing unwanted prefixes, suffixes, and special terms."""
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
            title = title[len(prefix) :].strip()

    # Remove unwanted suffixes
    for suffix in unwanted_suffixes:
        if title.lower().endswith(suffix.lower()):
            title = title[: -len(suffix)].strip()

    # Remove any unwanted terms
    words = title.split()
    cleaned_words = [word for word in words if word.lower() not in unwanted_terms]
    return " ".join(cleaned_words).strip()


def extract_year(title):
    """Extract the year from the title, e.g., (2005), (Video 2005), etc."""
    match = re.search(r"\(.*?(\d{4})\).*?", title)
    return int(match.group(1)) if match else None


def normalize_query(query):
    """Normalize and remove special characters like '™', '®' etc., and unnecessary suffixes like (PS2)"""
    query = query.replace("™", "").replace("®", "").replace("©", "")
    query = re.sub(
        r"\(.*?\)", "", query
    )  # Remove everything inside parentheses (PS2, video game, etc.)
    query = re.sub(r"[^\x00-\x7F]+", "", query)  # Remove any non-ASCII characters
    return query.strip()


async def search_howlongtobeat(game_name, year=None):
    """Search the game on HowLongToBeat and filter by year if available."""
    results = await HowLongToBeat().async_search(game_name)

    # Ensure at least 5 results
    if len(results) < 5:
        print("Warning: Less than 5 results found.")

    if not results:
        return None

    # If year was extracted and multiple results exist, filter by year
    if year:
        # Attempt to find results with the matching year
        matching_results = [
            r for r in results if r.release_world and str(year) == str(r.release_world)
        ]

        if matching_results:
            result = matching_results[0]  # Pick the first matching result
        else:
            print(f"Year {year} not found in results, using closest match.")
            result = results[0]  # Fallback to the first result
    else:
        result = results[0]  # If no year is provided, pick the first result

    return result


def search_with_serpapi(query):
    """Search Google via SerpAPI, prioritizing Wikipedia results."""
    params = {
        "q": f"{query} site:wikipedia.org",  # Prioritize Wikipedia
        "api_key": "5e38dfb2ed9fa0fd486ab4906afa102e79e9b9de8abced676a66ae74c60ad87a",
    }
    search = GoogleSearch(params)
    results = search.get_dict().get("organic_results", [])
    return results


def remove_year_from_query(query, year):
    """Remove the year from the query string (e.g., 'God of War (2005 video game)' -> 'God of War')"""
    return re.sub(
        r"\(\d{4}(?:\s*video\s*game|\s*videogame|\s*series)?\)", "", query
    ).strip()


async def search_game(game_name):
    """Search the game name using multiple methods (HLTB and SerpAPI)."""
    year = extract_year(game_name)  # Extract year from original title for filtering
    cleaned_name = clean_title(game_name)  # Clean the original name for searching

    # First attempt: Search on HowLongToBeat
    hltb_result = await search_howlongtobeat(cleaned_name, year)

    if not hltb_result:
        # If no result, search using SerpAPI
        serpapi_results = search_with_serpapi(cleaned_name)
        best_result = serpapi_results[0] if serpapi_results else None
        if best_result:
            # Clean the SerpAPI result title and extract the cleaned name
            cleaned_best_match = clean_title(best_result["title"])
            # Normalize the query to remove special characters
            cleaned_best_match = normalize_query(cleaned_best_match)

            # Clean the title from SerpAPI results (remove special characters and year part)
            cleaned_best_match = remove_year_from_query(cleaned_best_match, year)
            print(f"Best Match: {cleaned_best_match}")
            # Use the cleaned best match to search HLTB
            hltb_result = await search_howlongtobeat(cleaned_best_match, year)

    return hltb_result


@app.route("/search-game", methods=["POST"])
async def search_game_route():
    """Endpoint to search for a game."""
    data = request.get_json()

    # Validate API key
    if "GSHEET_API_KEY" not in data or data["GSHEET_API_KEY"] != GSHEET_API_KEY:
        return jsonify({"error": "Invalid or missing GSHEET_API_KEY"}), 401

    game_name = data.get("game_name")
    if not game_name:
        return jsonify({"error": "game_name is required"}), 400

    # Perform the search
    result = await search_game(game_name)

    if not result:
        return jsonify({"error": "No results found"}), 404

    # Return the result
    return jsonify({"game_name": result.game_name, "main_story": result.main_story})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(debug=False, host="0.0.0.0", port=port)
