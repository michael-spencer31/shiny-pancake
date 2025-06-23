import json

INPUT_FILE = "team_stats.json"
OUTPUT_FILE = "player_ratings.json"

FIELDS_TO_KEEP = [
    "playerId", "firstName", "lastName", "positionCode", "gamesPlayed",
    "goals", "assists", "points", "plusMinus", "shots", "shootingPctg",
    "avgTimeOnIcePerGame", "faceoffWinPctg"
]

def extract_relevant_stats():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    cleaned_data = {}

    for team_abbr, team_data in raw_data.items():
        skaters = team_data.get("skaters", [])
        cleaned_data[team_abbr] = []

        for player in skaters:
            simplified_player = {
                "id": player["playerId"],
                "name": f"{player['firstName']['default']} {player['lastName']['default']}",
                "position": player.get("positionCode", "")
            }

            for field in FIELDS_TO_KEEP:
                if field not in simplified_player:
                    simplified_player[field] = player.get(field)

            cleaned_data[team_abbr].append(simplified_player)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=2)

    print(f"✅ Extracted player ratings saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_relevant_stats()
