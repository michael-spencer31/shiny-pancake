from flask import Flask, jsonify, request
import os
import json
import time
import random
import itertools
import numpy as np
from collections import defaultdict
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
CACHE_FILE = "team_strengths.json"
CACHE_TTL_SECONDS = 86400  # 24 hours

# --- Helpers ---

def generate_team_strengths():
    return {
        "Edmonton": 1.5,
        "San Jose": 0.2,
        "Toronto": 1.2,
        "Montreal": 0.9,
        "Vancouver": 1.0,
        "Calgary": 1.1,
        "Seattle": 0.6,
        "Minnesota": 1.2,
        "Colorado": 1.5
    }

def load_or_generate_strengths(force_refresh=False):
    current_time = time.time()

    if not force_refresh and os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cached = json.load(f)
            if current_time - cached.get("_timestamp", 0) < CACHE_TTL_SECONDS:
                return cached["data"]

    data = generate_team_strengths()
    with open(CACHE_FILE, 'w') as f:
        json.dump({"_timestamp": current_time, "data": data}, f, indent=2)
    return data

def generate_fair_schedule(teams, games_per_team):
    matchups = list(itertools.combinations(teams, 2))
    total_games_needed = (games_per_team * len(teams)) // 2

    for _ in range(1000):
        matchup_counts = defaultdict(int)
        team_games = defaultdict(int)
        random.shuffle(matchups)

        while sum(team_games.values()) // 2 < total_games_needed:
            progress = False
            for team1, team2 in matchups:
                if team_games[team1] < games_per_team and team_games[team2] < games_per_team:
                    matchup_counts[(team1, team2)] += 1
                    team_games[team1] += 1
                    team_games[team2] += 1
                    progress = True
                if sum(team_games.values()) // 2 >= total_games_needed:
                    break
            if not progress:
                break

        if all(g == games_per_team for g in team_games.values()):
            return matchup_counts
    raise RuntimeError("Could not generate a fair schedule")

def simulate_game(str1, str2):
    base_rate = 2.9
    expected1 = base_rate * str1
    expected2 = base_rate * str2

    score1 = np.random.poisson(expected1)
    score2 = np.random.poisson(expected2)

    # Blowout logic
    blowout_chance = min(0.05 + (str1 - str2) * 0.1, 0.3)
    if np.random.rand() < blowout_chance:
        if str1 > str2:
            return 8, random.randint(0, 2), 1, False
        else:
            return random.randint(0, 2), 8, 2, False

    # Occasional upset
    upset_chance = 0.05
    if str1 < str2 and np.random.rand() < upset_chance:
        return random.randint(4, 5), random.randint(0, 2), 1, False
    if str2 < str1 and np.random.rand() < upset_chance:
        return random.randint(0, 2), random.randint(4, 5), 2, False

    score1 = min(score1, 8)
    score2 = min(score2, 8)

    if score1 == score2:
        if str1 > str2:
            return score1, score2, 1, True
        elif str2 > str1:
            return score1, score2, 2, True
        else:
            return score1, score2, random.choice([1, 2]), True

    return score1, score2, 1 if score1 > score2 else 2, False

# --- Routes ---

@app.route("/api/team-strengths", methods=["GET"])
def get_team_strengths():
    force = request.args.get("force") == "1"
    strengths = load_or_generate_strengths(force)
    return jsonify(strengths)

@app.route("/api/simulate-season", methods=["GET"])
def simulate_season():
    strengths = load_or_generate_strengths()
    teams = list(strengths.keys())
    games_per_team = 82

    schedule = generate_fair_schedule(teams, games_per_team)

    results = {
        team: {
            "wins": 0,
            "points": 0,
            "games_played": 0,
            "biggest_win": (0, 0, ""),
            "goal_diff": 0
        } for team in teams
    }

    for (team1, team2), count in schedule.items():
        for _ in range(count):
            s1, s2, winner, is_tie = simulate_game(strengths[team1], strengths[team2])

            results[team1]["games_played"] += 1
            results[team2]["games_played"] += 1
            results[team1]["goal_diff"] += s1 - s2
            results[team2]["goal_diff"] += s2 - s1

            if is_tie:
                results[team1]["points"] += 1
                results[team2]["points"] += 1
                if winner == 1:
                    results[team1]["points"] += 1
                    results[team1]["wins"] += 1
                    if s1 - s2 > results[team1]["biggest_win"][0] - results[team1]["biggest_win"][1]:
                        results[team1]["biggest_win"] = (s1, s2, team2)
                else:
                    results[team2]["points"] += 1
                    results[team2]["wins"] += 1
                    if s2 - s1 > results[team2]["biggest_win"][0] - results[team2]["biggest_win"][1]:
                        results[team2]["biggest_win"] = (s2, s1, team1)
            else:
                if winner == 1:
                    results[team1]["points"] += 2
                    results[team1]["wins"] += 1
                    if s1 - s2 > results[team1]["biggest_win"][0] - results[team1]["biggest_win"][1]:
                        results[team1]["biggest_win"] = (s1, s2, team2)
                else:
                    results[team2]["points"] += 2
                    results[team2]["wins"] += 1
                    if s2 - s1 > results[team2]["biggest_win"][0] - results[team2]["biggest_win"][1]:
                        results[team2]["biggest_win"] = (s2, s1, team1)

    standings = sorted(results.items(), key=lambda x: (x[1]['points'], x[1]['wins']), reverse=True)

    return jsonify({
        "standings": [
            {
                "rank": i + 1,
                "team": team,
                "points": stats["points"],
                "wins": stats["wins"],
                "goal_diff": stats["goal_diff"],
                "games_played": stats["games_played"],
                "biggest_win": {
                    "score": f"{stats['biggest_win'][0]}-{stats['biggest_win'][1]}",
                    "opponent": stats["biggest_win"][2]
                }
            } for i, (team, stats) in enumerate(standings)
        ]
    })

if __name__ == "__main__":
    app.run(debug=True)
