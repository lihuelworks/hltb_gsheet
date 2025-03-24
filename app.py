from flask import Flask, request, jsonify
from flask_cors import CORS
from howlongtobeatpy import HowLongToBeat
from duckduckgo_search import DDGS
from fuzzywuzzy import fuzz
import re
import asyncio
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the GSHEET_API_KEY from environment variables
GSHEET_API_KEY = os.getenv("GSHEET_API_KEY")


def clean_title(title):
    # Remove common prefixes and suffixes
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

    # Remove unwanted prefixes
    for prefix in unwanted_prefixes:
        if title.lower().startswith(prefix.lower()):
            title = title[len(prefix) :].strip()

    # Remove unwanted suffixes
    for suffix in unwanted_suffixes:
        if title.lower().endswith(suffix.lower()):
            title = title[: -len(suffix)].strip()

    # Remove any trailing " - ", " | ", " : ", etc.
    title = re.sub(r"[-:|]\s*$", "", title).strip()

    # Remove Wikipedia-specific suffixes like " - Wikipedi"
    title = re.sub(r"\s*- Wikipedi.*$", "", title).strip()

    # Remove any remaining unwanted terms (but preserve meaningful phrases)
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
    # Split the title into words and filter out unwanted terms
    words = title.split()
    cleaned_words = []
    skip_next = False
    for i, word in enumerate(words):
        if skip_next:
            skip_next = False
            continue
        # Check if the current word and the next word form a meaningful phrase
        if i < len(words) - 1:
            phrase = f"{word} {words[i + 1]}".lower()
            if phrase in ["save the"]:  # Add more meaningful phrases here if needed
                cleaned_words.append(word)
                cleaned_words.append(words[i + 1])
                skip_next = True
                continue
        # If not part of a meaningful phrase, filter out unwanted terms
        if word.lower() not in unwanted_terms:
            cleaned_words.append(word)
    title = " ".join(cleaned_words)

    # Remove any trailing " - ", " | ", " : ", etc. again
    title = re.sub(r"[-:|]\s*$", "", title).strip()

    return title.strip()


def extract_year(title):
    # Extract the year from the title, e.g., (2005), (Video 2005), etc.
    match = re.search(r"\(.*?(\d{4})\).*?", title)
    if match:
        return int(match.group(1))  # Return the year as an integer
    return None  # Return None if no year is found


def remove_year_and_extra_text(title):
    # Remove the year and extra text like "Video", "IMDb", etc.
    title = re.sub(r"\(.*?\d{4}.*?\)", "", title)  # Remove (Video 2005), (2005), etc.
    title = re.sub(
        r"\b(video|imdb)\b", "", title, flags=re.IGNORECASE
    )  # Remove "Video", "IMDb"
    return title.strip()


async def search_howlongtobeat(game_name, year=None):
    # Perform the search using the HowLongToBeat package
    results = await HowLongToBeat().async_search(game_name)

    if results is None or len(results) == 0:
        return None

    # If a year is provided and there are multiple results, filter to only include results with that year
    if year and len(results) > 1:
        filtered_results = []
        for result in results:
            # Ensure release_world is treated as a string
            release_year = str(result.release_world) if result.release_world else None
            if release_year and str(year) == release_year:
                filtered_results.append(result)
        # If filtering by year yields results, use only those results
        if filtered_results:
            results = filtered_results

    # If there's still more than one result, return only the first one
    if len(results) > 1:
        results = [results[0]]

    return results[0]


async def search_with_duckduckgo(game_name):
    # Perform the search using DuckDuckGo
    results = DDGS().text(game_name, max_results=5)  # Fetch 5 results

    if results:
        # Clean up and store all the titles
        cleaned_titles = [clean_title(result.get("title", "")) for result in results]

        if not cleaned_titles:
            return None

        # Use the first result from the filtered list
        best_result = results[0]

        # Clean the title
        best_match = clean_title(best_result.get("title", ""))

        # Extract the year from the query (if available)
        year = extract_year(game_name)

        # Remove the year and extra text from the best match for the HLTB search
        best_match_cleaned = remove_year_and_extra_text(best_match)

        # Log the cleaned title for debugging
        print(f"Cleaned Title: {best_match_cleaned}")

        # Perform a fuzzy search with HowLongToBeat
        hltb_results = await HowLongToBeat().async_search(best_match_cleaned)

        if hltb_results is None or len(hltb_results) == 0:
            print("No results found after cleaning and searching.")
            return None

        # Use fuzzy matching to find the best match
        best_hltb_match = None
        best_score = 0
        for result in hltb_results:
            score = fuzz.ratio(best_match_cleaned.lower(), result.game_name.lower())
            if score > best_score:
                best_score = score
                best_hltb_match = result

        if best_hltb_match:
            print(
                f"Best Match Found: {best_hltb_match.game_name} (Score: {best_score})"
            )
            return best_hltb_match
        else:
            print("No matching results found in HowLongToBeat.")
            return None
    else:
        return None


@app.route("/search-game", methods=["POST"])
async def search_game():
    # Log the incoming request
    print("Incoming request data:", request.get_json())

    # Get the request body
    data = request.get_json()

    # Check if GSHEET_API_KEY is provided and matches the environment variable
    if "GSHEET_API_KEY" not in data or data["GSHEET_API_KEY"] != GSHEET_API_KEY:
        print("Invalid or missing GSHEET_API_KEY")
        return jsonify({"error": "Invalid or missing GSHEET_API_KEY"}), 401

    # Get the game name from the request body
    game_name = data.get("game_name")

    if not game_name:
        print("game_name is required")
        return jsonify({"error": "game_name is required"}), 400

    # First attempt: Search directly using HowLongToBeat
    result = await search_howlongtobeat(game_name)

    if result is None:
        print("No results found in first attempt. Trying DuckDuckGo search...")
        # Second attempt: Use DuckDuckGo to find a better match
        result = await search_with_duckduckgo(game_name)

    if result is None:
        print("No results found after DuckDuckGo search")
        return jsonify({"error": "No results found"}), 404

    # Extract the `main_story` value
    main_story = result.main_story

    # Return the result
    return jsonify({"game_name": result.game_name, "main_story": main_story})


if __name__ == "__main__":
    # Use the PORT environment variable provided by Render
    port = int(os.getenv("PORT", 10000))  # Render uses 10000 by default
    print(f"Running on port {port}")
    app.run(debug=False, host="0.0.0.0", port=port)  # Disable debug mode for production
