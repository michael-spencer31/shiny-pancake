import json
import os
import time
import random
import itertools
import numpy as np
from collections import defaultdict
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)

CACHE_FILE = "team_strengths.json"
TEAM_RATINGS_FILE = "team_ratings.json"
PLAYER_RATINGS_FILE = "team_rosters.json"
CACHE_TTL_SECONDS = 86400  # 24 hours

# --- Helpers ---

def normalize_rating(rating, min_rating=75, max_rating=100):
    return round(0.5 + ((rating - min_rating) / (max_rating - min_rating)) * 0.5, 3)

def load_or_generate_strengths(force_refresh=False):
    current_time = time.time()

    if not force_refresh and os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cached = json.load(f)
            if current_time - cached.get("_timestamp", 0) < CACHE_TTL_SECONDS:
                return cached["data"]

    with open(TEAM_RATINGS_FILE, 'r') as f:
        raw_ratings = json.load(f)

    strengths = {
        team: normalize_rating(rating)
        for team, rating in raw_ratings.items()
    }

    with open(CACHE_FILE, 'w') as f:
        json.dump({"_timestamp": current_time, "data": strengths}, f, indent=2)

    return strengths

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
    base_rate = 4.8
    expected1 = base_rate * str1
    expected2 = base_rate * str2

    score1 = np.random.poisson(expected1)
    score2 = np.random.poisson(expected2)

    blowout_chance = min(0.05 + (str1 - str2) * 0.1, 0.3)
    if np.random.rand() < blowout_chance:
        if str1 > str2:
            return 8, random.randint(0, 2), 1, False
        else:
            return random.randint(0, 2), 8, 2, False

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

def pick_weighted_player(players):
    total = sum(p['rating'] for p in players)
    r = random.uniform(0, total)
    upto = 0
    for p in players:
        upto += p['rating']
        if upto >= r:
            return p
    return random.choice(players)

def pick_assist_players(goal_scorer, team_players, max_assists=2):
    eligible = [p for p in team_players if p["name"] != goal_scorer["name"]]

    # Bias toward 1 or 2 assists: weighted random choice
    assist_options = [0, 1, 2]
    weights = [0.1, 0.45, 0.45]  # Adjust to your liking
    num_assists = random.choices(assist_options, weights=weights, k=1)[0]

    assists = []
    for _ in range(num_assists):
        if eligible:
            assist = pick_weighted_player(eligible)
            assists.append(assist)
            eligible = [p for p in eligible if p["name"] != assist["name"]]

    return assists

def generate_goal_time_and_period():
    period = random.choices([1, 2, 3, 4], weights=[30, 30, 30, 10])[0]
    minute = random.randint(0, 19)
    second = random.randint(0, 59)
    return period, f"{minute:02d}:{second:02d}"

def simulate_game_with_scorers(str1, str2, players1, players2):
    base_rate = 2.9
    expected1 = base_rate * str1
    expected2 = base_rate * str2

    goals1 = min(np.random.poisson(expected1), 8)
    goals2 = min(np.random.poisson(expected2), 8)

    detailed_goals1 = []
    detailed_goals2 = []

    all_goals = []

    # First generate all regulation goals
    for team_id, team_players, goal_count in [(1, players1, goals1), (2, players2, goals2)]:
        for _ in range(goal_count):
            scorer = pick_weighted_player(team_players)
            assists = pick_assist_players(scorer, team_players)
            period = random.choices([1, 2, 3], weights=[33, 33, 34])[0]  # Only periods 1-3
            minute = random.randint(0, 19)
            second = random.randint(0, 59)
            time_str = f"{minute:02d}:{second:02d}"
            all_goals.append({
                "team": team_id,
                "scorer": scorer["name"],
                "assists": [a["name"] for a in assists],
                "period": period,
                "time": time_str
            })

    # Determine winner and optionally simulate OT goal
    if goals1 > goals2:
        winner = 1
        tie = False
    elif goals2 > goals1:
        winner = 2
        tie = False
    else:
        tie = True
        winner = random.choice([1, 2])  # OT winner

        # Add 1 OT goal for the winning team
        ot_players = players1 if winner == 1 else players2
        scorer = pick_weighted_player(ot_players)
        assists = pick_assist_players(scorer, ot_players)
        minute = random.randint(0, 4)
        second = random.randint(0, 59)
        time_str = f"{minute:02d}:{second:02d}"
        all_goals.append({
            "team": winner,
            "scorer": scorer["name"],
            "assists": [a["name"] for a in assists],
            "period": 4,
            "time": time_str
        })

    # Sort and categorize
    all_goals.sort(key=lambda g: (g["period"], g["time"]))

    for goal in all_goals:
        if goal["team"] == 1:
            detailed_goals1.append(goal)
        else:
            detailed_goals2.append(goal)

    return {
        "score1": goals1,
        "score2": goals2,
        "winner": winner,
        "tie": tie,
        "goals_team1": detailed_goals1,
        "goals_team2": detailed_goals2
    }

# --- Routes ---

@app.route("/api/team-strengths", methods=["GET"])
def get_team_strengths():
    # force = request.args.get("force") == "1"
    strengths = load_or_generate_strengths()
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

@app.route("/api/simulate-game", methods=["GET"])
def simulate_game_endpoint():
    strengths = load_or_generate_strengths()
    teams = list(strengths.keys())

    if len(teams) < 2:
        return jsonify({"error": "Not enough teams to simulate a game."}), 400

    team1, team2 = random.sample(teams, 2)
    str1, str2 = strengths[team1], strengths[team2]

    score1, score2, winner, is_tie = simulate_game(str1, str2)

    return jsonify({
        "team1": team1,
        "team2": team2,
        "score1": score1,
        "score2": score2,
        "winner": team1 if winner == 1 else team2,
        "tie": is_tie
    })

@app.route("/api/simulate-specific-game", methods=["POST"])
def simulate_specific_game():
    data = request.get_json()
    team1 = data.get("team1")
    team2 = data.get("team2")

    strengths = load_or_generate_strengths()

    if team1 not in strengths or team2 not in strengths:
        return jsonify({"error": "One or both teams are invalid."}), 400
    if team1 == team2:
        return jsonify({"error": "Please select two different teams."}), 400

    str1 = strengths[team1]
    str2 = strengths[team2]

    score1, score2, winner, is_tie = simulate_game(str1, str2)

    return jsonify({
        "team1": team1,
        "team2": team2,
        "score1": score1,
        "score2": score2,
        "winner": team1 if winner == 1 else team2,
        "tie": is_tie
    })
@app.route("/api/simulate-specific-game-with-goals", methods=["POST"])
def simulate_with_goal_details():
    data = request.get_json()
    team1 = data.get("team1")
    team2 = data.get("team2")

    strengths = load_or_generate_strengths()

    if team1 not in strengths or team2 not in strengths:
        return jsonify({"error": "One or both teams are invalid."}), 400

    with open(PLAYER_RATINGS_FILE, "r") as f:
        player_data = json.load(f)

    players1 = player_data.get(team1, [])
    players2 = player_data.get(team2, [])

    result = simulate_game_with_scorers(strengths[team1], strengths[team2], players1, players2)

    return jsonify({
        "team1": team1,
        "team2": team2,
        "score1": result["score1"],
        "score2": result["score2"],
        "winner": team1 if result["winner"] == 1 else team2,
        "tie": result["tie"],
        "goals_team1": result["goals_team1"],
        "goals_team2": result["goals_team2"]
    })

# default landing page
@app.route("/")
def index():
    return send_file("index.html")

@app.route("/teams")
def teams():
    return send_file("teams.html")

@app.route("/rosters")
def roster():
    return send_file("roster.html")

if __name__ == "__main__":
    app.run(debug=True)
