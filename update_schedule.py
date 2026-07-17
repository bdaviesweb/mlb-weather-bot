# update_schedule.py
# Updated: April 2026
# Changes:
#   - Added game_pk to each game entry (required for prediction accuracy tracking)
#   - Added missing/updated Regular Season venues (Athletics → Sacramento, etc.)
#   - Added Sutter Health Park (Athletics)
#   - Removed stale Oakland Coliseum entry
#   - Added timeout to requests call
#   - Added unknown venue warning with full list for easier debugging
#   - Added Rate Field (White Sox new stadium name) → Chicago,US
#   - Added UNIQLO Field at Dodger Stadium (renamed) → Los Angeles,US
#   - Added Daikin Park (Astros — possible Minute Maid rename) → Houston,US
#   - Added alternate capitalizations for loanDepot park → Miami,US
#   - Added Coors Field alternate name safety net
#   - Added Wrigley Field alternate name safety net

import json
import requests
from datetime import datetime, timedelta
import pytz
from venues import get_venue_location

def get_mlb_schedule(days_ahead=2, now=None):
    """Fetch MLB games starting in the next 24 hours."""
    games = []
    pacific_tz = pytz.timezone('America/Los_Angeles')
    now_pacific = now or datetime.now(pacific_tz)
    if now_pacific.tzinfo is None:
        now_pacific = pacific_tz.localize(now_pacific)
    window_end = now_pacific + timedelta(hours=24)

    for day_offset in range(days_ahead):
        date = now_pacific + timedelta(days=day_offset)
        date_str = date.strftime('%Y-%m-%d')

        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}"

        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            if 'dates' in data and len(data['dates']) > 0:
                for date_info in data['dates']:
                    for game in date_info.get('games', []):
                        away_team         = game['teams']['away']['team']['name']
                        home_team         = game['teams']['home']['team']['name']
                        game_datetime_utc = game['gameDate']
                        venue_name        = game['venue']['name']
                        game_pk           = game.get('gamePk', '')

                        venue_location = get_venue_location(venue_name)

                        # Parse UTC time and convert to Pacific
                        game_dt_utc     = datetime.strptime(game_datetime_utc, '%Y-%m-%dT%H:%M:%SZ')
                        game_dt_utc     = pytz.utc.localize(game_dt_utc)
                        game_dt_pacific = game_dt_utc.astimezone(pacific_tz)

                        if not (now_pacific <= game_dt_pacific <= window_end):
                            continue

                        games.append({
                            'date':     game_dt_pacific.strftime('%Y-%m-%d'),
                            'time':     game_dt_pacific.strftime('%H:%M'),
                            'opponent': f"{away_team} vs {home_team}",
                            'location': venue_location,
                            'venue':    venue_name,
                            'game_pk':  game_pk
                        })

        except Exception as e:
            print(f"Error fetching schedule for {date_str}: {e}")
            continue

    return games


def update_config_file(games):
    """Update config.json with fresh schedule"""
    config = {"games": games}
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✅ Updated config.json with {len(games)} games")


def main():
    print("🔄 Fetching MLB schedule...")
    games = get_mlb_schedule(days_ahead=2)

    if games:
        print(f"📅 Found {len(games)} games in next 24 hours")

        # Print venue summary for easy verification
        print(f"\n📍 Venues in today's schedule:")
        seen_venues = set()
        for game in games:
            venue = game.get('venue', 'Unknown')
            if venue not in seen_venues:
                print(f"   • {venue} → {game['location']}")
                seen_venues.add(venue)

        update_config_file(games)
    else:
        print("⚠️  No games found - keeping existing config.json")


if __name__ == "__main__":
    main()
