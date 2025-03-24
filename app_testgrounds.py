import sys
from duckduckgo_search import DDGS
from fuzzywuzzy import fuzz
import re
from howlongtobeatpy import HowLongToBeat
import asyncio


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


def title_contains_year(title):
    # Check if the title contains a year
    return bool(re.search(r"\(.*?\d{4}.*?\)", title))


async def search_howlongtobeat(game_name, year=None):
    # Perform the search using the HowLongToBeat package
    results = await HowLongToBeat().async_search(game_name)

    if results is None or len(results) == 0:
        print("No results found or an error occurred")
        return

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

    # Print the result
    for i, result in enumerate(results[:1], start=1):
        print(f"\nResult {i}:")
        print(f"Game Name: {result.game_name}")
        print(f"Main Story: {result.main_story} hours")
        print(f"Main + Extra: {result.main_extra} hours")
        print(f"Completionist: {result.completionist} hours")
        print(f"All Styles: {result.all_styles} hours")
        print(f"Release Year: {result.release_world}")
        print(f"Raw JSON Data: {result.__dict__}")  # Print all raw data


def main():
    if len(sys.argv) < 2:
        print("Usage: python duckduckgo_search.py <search_query>")
        sys.exit(1)

    query = sys.argv[1]
    # Add "site:wikipedia.org" to the query to search only Wikipedia
    query_with_site = f"{query} site:wikipedia.org"

    # Perform the search with the modified query
    results = DDGS().text(query_with_site, max_results=5)  # Fetch 5 results

    if results:
        # Clean up and store all the titles
        cleaned_titles = [clean_title(result.get("title", "")) for result in results]

        if not cleaned_titles:
            print("No clean results found.")
            return

        # Use the first result from the filtered list
        best_result = results[0]

        # Clean the title
        best_match = clean_title(best_result.get("title", ""))

        # Extract the year from the query (if available)
        year = extract_year(query)

        # Print the best match and the extracted year (if any)
        print(f"Best Match: {best_match}")
        if year:
            print(f"Extracted Year: {year}")

        # Remove the year and extra text from the best match for the HLTB search
        best_match_cleaned = remove_year_and_extra_text(best_match)
        print(f"Searching HLTB for: {best_match_cleaned}")

        # Search HowLongToBeat with the cleaned best match and filter by extracted year (if available)
        asyncio.run(search_howlongtobeat(best_match_cleaned, year))
    else:
        print("No results found.")


if __name__ == "__main__":
    main()
