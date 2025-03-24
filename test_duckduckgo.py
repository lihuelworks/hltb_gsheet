import sys
from duckduckgo_search import DDGS
from fuzzywuzzy import fuzz
import re


def clean_title(title):
    # Remove common terms like 'Wikipedia', 'Steam', 'Download', etc.
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
    ]
    title = " ".join(
        [word for word in title.split() if word.lower() not in unwanted_terms]
    )

    # Remove any trailing " - " and " | " and other unwanted trailing words
    title = title.rstrip(" -|")

    return title.strip()


def extract_year(title):
    # Extract the year from the title, e.g., (2022)
    match = re.search(r"\((\d{4})\)", title)
    if match:
        return int(match.group(1))  # Return the year as an integer
    return None  # Return None if no year is found


def main():
    if len(sys.argv) < 2:
        print("Usage: python duckduckgo_search.py <search_query>")
        sys.exit(1)

    query = sys.argv[1]
    results = DDGS().text(query, max_results=15)  # Fetch 15 results

    if results:
        # Clean up and store all the titles
        cleaned_titles = [clean_title(result.get("title", "")) for result in results]

        if not cleaned_titles:
            print("No clean results found.")
            return

        # Extract the year from the first title (if available)
        base_title = cleaned_titles[0]
        year = extract_year(base_title)

        # Perform fuzzy matching and average the results
        matched_titles = cleaned_titles[1:]

        # Average fuzzy match score and adjusted title
        scores = []
        for title in matched_titles:
            score = fuzz.partial_ratio(base_title, title)
            scores.append((title, score))

        # Sort results by match score (highest first)
        scores.sort(key=lambda x: x[1], reverse=True)

        # Get the highest matching title as the corrected result
        best_match = scores[0][0] if scores else base_title

        # Print the best match and the extracted year (if any)
        print(f"Best Match: {best_match}")
        if year:
            print(f"Extracted Year: {year}")
    else:
        print("No results found.")


if __name__ == "__main__":
    main()
