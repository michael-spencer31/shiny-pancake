import requests
import json
import time

def get_valid_teams():
    res = requests.get("https://statsapi.web.nhl.com/api/v1/teams")
    res.raise_for_status()
    teams = res.json()["teams"]
    return {team["id"]: team["name"] for team in teams}

def fetch_roster(team_id):
    url = f"https://statsapi.web.nhl.com/api/v1/teams/{team_id}?expand=team.roster"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data["teams"][0]["roster"]["roster"]

def save_all_rosters():
    all_rosters = {}
    valid_teams = get_valid_teams()

    for team_id, team_name in valid_teams.items():
        try:
            print(f"Fetching roster for {team_name}...")
            roster = fetch_roster(team_id)
            all_rosters[team_name] = roster
            time.sleep(0.5)  # Avoid rate limits
        except Exception as e:
            print(f"❌ Failed for {team_name} ({team_id}): {e}")

    with open("roster_data.json", "w") as f:
        json.dump(all_rosters, f, indent=2)

if __name__ == "__main__":
    save_all_rosters()
