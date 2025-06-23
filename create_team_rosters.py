import json

def main():
    with open("normalized_player_ratings.json", "r") as f:
        team_data = json.load(f)

    rosters = {}

    for team, players in team_data.items():
        rosters[team] = []
        for player in players:
            rosters[team].append({
                "id": player["id"],
                "name": player["name"],
                "position": player["position"],
                "rating": player["rating"]
            })

    with open("team_rosters.json", "w") as f:
        json.dump(rosters, f, indent=2)

    print("✅ team_rosters.json created successfully!")

if __name__ == "__main__":
    main()
