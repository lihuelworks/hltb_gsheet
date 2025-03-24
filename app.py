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


async def search_howlongtobeat(game_name, year=None):
    """Search the game on HowLongToBeat and filter by year if available."""
    results = await HowLongToBeat().async_search(game_name)

    if not results:
        return None

    if year and len(results) > 1:
        results = [
            result for result in results if str(result.release_world) == str(year)
        ]

    return results[0] if results else None


def search_with_serpapi(query):
    """Search Google via SerpAPI, prioritizing Wikipedia results."""
    params = {
        "q": f"{query} site:wikipedia.org",  # Prioritize Wikipedia
        "api_key": "5e38dfb2ed9fa0fd486ab4906afa102e79e9b9de8abced676a66ae74c60ad87a",
    }
    search = GoogleSearch(params)
    results = search.get_dict().get("organic_results", [])
    return results


async def search_game(game_name):
    """Search the game name using multiple methods (HLTB and SerpAPI)."""
    year = extract_year(game_name)
    cleaned_name = clean_title(game_name)

    # First attempt: Search on HowLongToBeat
    hltb_result = await search_howlongtobeat(cleaned_name, year)

    if not hltb_result:
        # If no result, search using SerpAPI
        serpapi_results = search_with_serpapi(cleaned_name)
        best_result = serpapi_results[0] if serpapi_results else None
        if best_result:
            hltb_result = await search_howlongtobeat(best_result["title"], year)

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
