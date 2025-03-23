from flask import Flask, request, jsonify
from flask_cors import CORS
from howlongtobeatpy import HowLongToBeat
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the GSHEET_API_KEY from environment variables
GSHEET_API_KEY = os.getenv("GSHEET_API_KEY")


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

    # Perform the search using the HowLongToBeat package
    results = await HowLongToBeat().async_search(game_name)

    if results is None or len(results) == 0:
        print("No results found or an error occurred")
        return jsonify({"error": "No results found or an error occurred"}), 404

    # Get the first result
    first_result = results[0]

    # Extract the `main_story` value
    main_story = first_result.main_story

    # Return only the `main_story` value
    return jsonify({"game_name": first_result.game_name, "main_story": main_story})


if __name__ == "__main__":
    # Use the PORT environment variable provided by Render
    port = int(os.getenv("PORT", 10000))  # Render uses 10000 by default
    print(f"Running on port {port}")
    app.run(debug=True, host="0.0.0.0", port=port)  # Disable debug mode for production
