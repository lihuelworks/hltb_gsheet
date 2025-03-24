import sys
import re
import asyncio
from howlongtobeatpy import HowLongToBeat
from serpapi import GoogleSearch


def extract_year(title):
    """Extracts year from input if present, e.g., 'God of War (2005 video game)' -> 2005"""
    match = re.search(r"\(.*?(\d{4}).*?\)", title)
    return int(match.group(1)) if match else None


def normalize_query(query):
    """Normalize and remove special characters like '™', '®' etc."""
    # Replace common special characters with their base versions
    query = query.replace("™", "").replace("®", "").replace("©", "")
    query = re.sub(r"[^\x00-\x7F]+", "", query)  # Remove any non-ASCII characters
    return query.strip()


async def search_howlongtobeat(game_name, year=None):
    """Searches HowLongToBeat with the full title; if multiple results, filters by year"""
    results = await HowLongToBeat().async_search(game_name)

    if not results:
        print("No results found or an error occurred")
        return

    # If year was extracted and multiple results exist, filter by year
    if year and len(results) > 1:
        results = [
            r for r in results if r.release_world and str(year) == str(r.release_world)
        ]

    result = results[0] if results else None
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
    return re.sub(r"\(\d{4}\s*video game\)", "", query).strip()


def main():
    if len(sys.argv) < 2:
        print("Usage: python search.py <search_query>")
        sys.exit(1)

    query = sys.argv[1]  # Full user input
    year = extract_year(query)  # Extract year if present

    query = normalize_query(query)  # Normalize the query to remove special characters

    results = google_search(query)

    # Prioritize Wikipedia results, fall back to general if none exist
    wiki_results = [r for r in results if "wikipedia.org" in r.get("link", "").lower()]
    best_result = wiki_results[0] if wiki_results else (results[0] if results else None)

    if not best_result:
        print("No results found.")
        return

    best_match = best_result.get("title", "").strip()  # Keep full title
    print(f"Best Match: {best_match}")
    if year:
        print(f"Extracted Year: {year}")

    # Remove the year from query for HLTB search
    cleaned_query = remove_year_from_query(query, year)
    print(f"Searching HLTB for: {cleaned_query}")
    asyncio.run(search_howlongtobeat(cleaned_query, year))


if __name__ == "__main__":
    main()
