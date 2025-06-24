import json

# Load simplified players list
with open('simplified_players.json') as f:
    simplified = json.load(f)

# Load team rosters (organized by team)
with open('team_rosters.json') as f:
    team_rosters = json.load(f)

# Flatten all rosters into a lookup by player ID (string)
roster_by_id = {}
for team, players in team_rosters.items():
    for player in players:
        roster_by_id[str(player['id'])] = player

# Merge data
merged = []
for player in simplified:
    pid = str(player['id'])
    is_goalie = player.get('position') == 'G'

    if pid in roster_by_id:
        # Merge existing data
        merged_player = {**player, **roster_by_id[pid]}
    else:
        # Not in rosters — likely a goalie
        merged_player = player.copy()
        if is_goalie:
            merged_player['rating'] = 82  # default rating for goalies
        else:
            merged_player['rating'] = 80  # fallback for skaters not in roster
            merged_player['status'] = 'missing_roster_data'
            print(f"⚠️ Skater not found in roster: {player['name']} ({player['team']})")

    merged.append(merged_player)

# Save result
with open('merged_players.json', 'w') as f:
    json.dump(merged, f, indent=2)

print(f"✅ Merged {len(merged)} players into merged_players.json")
