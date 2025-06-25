import json
from collections import defaultdict

# Load player data
with open('merged_players.json') as f:
    players = json.load(f)

# Group players by team
teams = defaultdict(list)
for player in players:
    teams[player['team']].append(player)

# Calculate raw scores
raw_scores = {}
for team, roster in teams.items():
    weighted_sum = 0
    franchise_count = 0

    for p in roster:
        r = p.get('rating', 0)
        if r >= 90:
            weighted_sum += r * 2
            franchise_count += 1
        elif r >= 80:
            weighted_sum += r
        else:
            weighted_sum += r * 0.6

    bonus = 50 if franchise_count >= 2 else 25 if franchise_count == 1 else 0
    total = round(weighted_sum + bonus)
    raw_scores[team] = total

# Normalize to range [0.1, 2.0]
min_score = min(raw_scores.values())
max_score = max(raw_scores.values())
score_range = max_score - min_score

def normalize(value):
    if score_range == 0:
        return 1.0
    return round(0.1 + ((value - min_score) / score_range) * (2.0 - 0.1), 2)

# Create formatted output
normalized_output = {
    "data": {team: normalize(score) for team, score in sorted(raw_scores.items())}
}

# Write to file
with open('normalized_ratings.json', 'w') as f:
    json.dump(normalized_output, f, indent=2)

print("✅ Normalized ratings saved to static/normalized_ratings.json")
