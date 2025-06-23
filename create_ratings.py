import json

# Load data
with open("player_ratings.json", "r") as f:
    data = json.load(f)

# Collect stat categories for normalization
goals, assists, points, plus_minus = [], [], [], []
shots, shooting_pctg, toi, faceoff_pctg = [], [], [], []

# Gather all values for normalization
for team_players in data.values():
    for player in team_players:
        goals.append(player.get("goals", 0))
        assists.append(player.get("assists", 0))
        points.append(player.get("points", 0))
        plus_minus.append(player.get("plusMinus", 0))
        shots.append(player.get("shots", 0))
        shooting_pctg.append(player.get("shootingPctg", 0))
        toi.append(player.get("avgTimeOnIcePerGame", 0))
        faceoff_pctg.append(player.get("faceoffWinPctg", 0))

def normalize(value, values):
    min_v, max_v = min(values), max(values)
    return 0 if max_v == min_v else (value - min_v) / (max_v - min_v)

def scale_rating(value):
    return round(75 + value * 25)

# Define stat weights
weights = {
    "goals": 0.25,
    "assists": 0.15,
    "points": 0.25,
    "plusMinus": 0.1,
    "shots": 0.1,
    "shootingPctg": 0.05,
    "avgTimeOnIcePerGame": 0.1,
    "faceoffWinPctg": 0.05
}

# Generate ratings with team and jersey number
ratings = {}

for team, team_players in data.items():
    ratings[team] = []
    for player in team_players:
        score = 0
        score += weights["goals"] * normalize(player.get("goals", 0), goals)
        score += weights["assists"] * normalize(player.get("assists", 0), assists)
        score += weights["points"] * normalize(player.get("points", 0), points)
        score += weights["plusMinus"] * normalize(player.get("plusMinus", 0), plus_minus)
        score += weights["shots"] * normalize(player.get("shots", 0), shots)
        score += weights["shootingPctg"] * normalize(player.get("shootingPctg", 0), shooting_pctg)
        score += weights["avgTimeOnIcePerGame"] * normalize(player.get("avgTimeOnIcePerGame", 0), toi)
        score += weights["faceoffWinPctg"] * normalize(player.get("faceoffWinPctg", 0), faceoff_pctg)

        overall = scale_rating(score)

        ratings[team].append({
            "id": player["id"],
            "name": player["name"],
            "team": team,
            "position": player["position"],
            "rating": overall
        })

        

# Save to file
with open("normalized_player_ratings.json", "w") as f:
    json.dump(ratings, f, indent=2)

print("✅ Player ratings (with team + jersey number) saved to normalized_player_ratings.json")
