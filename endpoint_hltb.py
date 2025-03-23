from flask import Flask, request, jsonify
from howlongtobeatpy import HowLongToBeat

app = Flask(__name__)


@app.route("/search-game", methods=["POST"])
async def search_game():
    # Get the game name from the request body
    data = request.get_json()
    game_name = data.get("game_name")

    if not game_name:
        return jsonify({"error": "game_name is required"}), 400

    # Perform the search using the HowLongToBeat package
    results = await HowLongToBeat().async_search(game_name)

    if results is None or len(results) == 0:
        return jsonify({"error": "No results found or an error occurred"}), 404

    # Get the first result
    first_result = results[0]

    # Extract the `main_story` value
    main_story = first_result.main_story

    # Return only the `main_story` value
    return jsonify({"game_name": first_result.game_name, "main_story": main_story})


if __name__ == "__main__":
    # Use a consistent port (e.g., 5000)
    port = 5000
    print(f"Running on port {port}")
    app.run(debug=True, use_reloader=False, port=port)
