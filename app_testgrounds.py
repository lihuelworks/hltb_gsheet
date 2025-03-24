import sys
import re
import asyncio
from howlongtobeatpy import HowLongToBeat
from serpapi import GoogleSearch


def extract_year(title):
    """Extracts year from input if present, e.g., 'God of War (2005 video game)' -> 2005"""
    # Match a four-digit number inside parentheses, including possible extra text like "video game"
    match = re.search(r"\((\d{4})\s*(video\s*game|ps2|series|edition)?\)", title)
    print("gotten year", match)
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
    """Searches HowLongToBeat with the full title; if multiple results, filters by year"""
    results = await HowLongToBeat().async_search(game_name)

    if not results:
        print("No results found or an error occurred")
        return

    # Ensure we have at least 5 results
    if len(results) < 5:
        print("Warning: Less than 5 results found.")

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

    if result:
        print(f"\nGame Name: {result.game_name}")
        print(f"Main Story: {result.main_story} hours")
        print(f"Main + Extra: {result.main_extra} hours")
        print(f"Completionist: {result.completionist} hours")
        print(f"All Styles: {result.all_styles} hours")
        print(f"Release Year: {result.release_world}")


def google_search(query):
    """Searches Google via SerpAPI, prioritizing Wikipedia results"""
    params = {
        "q": f"{query} site:wikipedia.org",  # Forces Wikipedia priority
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


def main():
    if len(sys.argv) < 2:
        print("Usage: python search.py <search_query>")
        sys.exit(1)

    query = sys.argv[1]  # Full user input

    results = google_search(query)

    # Prioritize Wikipedia results, fall back to general if none exist
    wiki_results = [r for r in results if "wikipedia.org" in r.get("link", "").lower()]
    best_result = wiki_results[0] if wiki_results else (results[0] if results else None)

    if not best_result:
        print("No results found.")
        return

    best_match = best_result.get(
        "title", ""
    ).strip()  # Extract the title from the dictionary
    print(f"Best Match: {best_match}")

    # Extract year after selecting the best match
    year = extract_year(best_match)  # Extract year from the title string
    if year:
        print(f"Extracted Year: {year}")

    # Normalize the query to remove special characters
    query = normalize_query(best_match)

    # Clean the title from SerpAPI results (remove special characters and year part)
    cleaned_query = remove_year_from_query(query, year)
    print(f"Searching HLTB for: {cleaned_query}")
    asyncio.run(search_howlongtobeat(cleaned_query, year))


if __name__ == "__main__":
    main()
