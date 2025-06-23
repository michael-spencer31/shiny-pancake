import requests
import json
import time

TEAM_ABBRS = [
    "ANA", "UTA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL", "DAL", "DET",
    "EDM", "FLA", "LAK", "MIN", "MTL", "NJD", "NSH", "NYI", "NYR", "OTT", "PHI",
    "PIT", "SEA", "SJS", "STL", "TBL", "TOR", "VAN", "VGK", "WPG", "WSH"
]

SEASON = "20242025"
GAME_TYPE = "2"  # Regular season
OUTPUT_FILE = "team_stats.json"

def fetch_team_stats(team_abbr):
    url = f"https://api-web.nhle.com/v1/club-stats/{team_abbr}/{SEASON}/{GAME_TYPE}"
    print(f"Fetching {team_abbr} stats from: {url}")
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"❌ Failed to fetch data for {team_abbr}: {e}")
        return None

def main():
    all_stats = {}
    for team in TEAM_ABBRS:
        data = fetch_team_stats(team)
        if data:
            all_stats[team] = data
        time.sleep(1)  # Light rate limiting

    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_stats, f, indent=2)
    print(f"\n✅ Saved team stats to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
