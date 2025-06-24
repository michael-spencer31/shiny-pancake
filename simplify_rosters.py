import json

def simplify_rosters(input_file="roster_data.json", output_file="simplified_players.json"):
    with open(input_file, "r") as f:
        data = json.load(f)

    simplified = []

    for team_abbr, players in data.items():
        for player in players:
            full_name = f"{player['firstName']['default']} {player['lastName']['default']}"
            birth_year = int(player["birthDate"].split("-")[0])
            sweaterNumber = player.get("sweaterNumber")

            simplified.append({
                "id": player["id"],
                "name": full_name,
                "team": team_abbr,
                "number": sweaterNumber,
                "position": player.get("positionCode"),
                "number": sweaterNumber,
                "shoots": player.get("shootsCatches"),
                "birthYear": birth_year
            })

    with open(output_file, "w") as f:
        json.dump(simplified, f, indent=2)

    print(f"✅ Simplified {len(simplified)} players to {output_file}")

if __name__ == "__main__":
    simplify_rosters()
