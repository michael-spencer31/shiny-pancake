import json

# Configuration
MIN_RATING = 78
MAX_RATING = 95
EXPONENT = 1.5

def scale_softened(avg_rating, min_input, max_input, exponent=EXPONENT):
    """Scale a value using softened exponential transformation."""
    transformed = avg_rating ** exponent
    min_trans = min_input ** exponent
    max_trans = max_input ** exponent
    if max_trans == min_trans:
        return MIN_RATING
    normalized = (transformed - min_trans) / (max_trans - min_trans)
    return round(MIN_RATING + normalized * (MAX_RATING - MIN_RATING))

def main():
    with open("team_rosters.json", "r") as f:
        rosters = json.load(f)

    team_averages = {}
    for team, players in rosters.items():
        if not players:
            team_averages[team] = 0
        else:
            total_rating = sum(player["rating"] for player in players)
            avg_rating = total_rating / len(players)
            team_averages[team] = avg_rating

    # Normalize with softened scaling
    min_avg = min(team_averages.values())
    max_avg = max(team_averages.values())

    team_ratings = {}
    for team, avg in team_averages.items():
        team_ratings[team] = scale_softened(avg, min_avg, max_avg)

    with open("team_ratings.json", "w") as f:
        json.dump(team_ratings, f, indent=2)

    print("✅ team_ratings.json created with softened scaling!")

if __name__ == "__main__":
    main()
