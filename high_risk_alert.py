# high_risk_alert.py
# Updated: April 2026
# Weather API: National Weather Service (NWS) — replaces OpenWeatherMap
# Changes:
#   - Removed WEATHER_API_KEY / OpenWeatherMap entirely
#   - NWS API: no API key, hourly updates, ~92-95% accuracy (US only)
#   - Toronto (Rogers Centre) hardcoded as fixed dome — roof always closed
#   - get_weather_forecast() replaced with NWS implementation
#   - Rain threshold tightened: HIGH_RISK 70% → 75%
#   - Cold temp threshold tightened: 20°F → 35°F
#   - Forecast targets exact game start hour (not closest 3-hr bucket)
#   - Slack footer updated to reflect new NWS threshold
#   - Thunderstorm detection smarter: ignores "Slight Chance" thunderstorms
#     and requires rain_prob >= 40% to trigger thunderstorm HIGH RISK

import os
import json
import requests
import pytz
from datetime import datetime, timedelta
from analytics import log_alert, log_workflow_run, log_prediction_accuracy

SLACK_WEBHOOK = os.environ.get('HIGH_RISK_WEBHOOK_URL')

# ─────────────────────────────────────────────────────────────
# NWS CONFIG — No API key needed
# ─────────────────────────────────────────────────────────────
NWS_USER_AGENT = "MLBWeatherBot/2.0 (github.com/Sports-Weather2/mlb-weather-bot)"
NWS_POINTS_URL = "https://api.weather.gov/points/{lat},{lon}"

STADIUM_COORDINATES = {
    # Fixed Dome — always excluded
    'St Petersburg,US':  {'lat': 27.7683, 'lon': -82.6534, 'roof': 'fixed'},
    'Toronto,CA':        {'lat': 43.6414, 'lon': -79.3894, 'roof': 'fixed'},

    # Retractable Roof — check MLB API
    'Phoenix,US':        {'lat': 33.4453, 'lon': -112.0667, 'roof': 'retractable'},
    'Miami,US':          {'lat': 25.7781, 'lon': -80.2197,  'roof': 'retractable'},
    'Arlington,US':      {'lat': 32.7512, 'lon': -97.0832,  'roof': 'retractable'},
    'Houston,US':        {'lat': 29.7573, 'lon': -95.3555,  'roof': 'retractable'},
    'Seattle,US':        {'lat': 47.5914, 'lon': -122.3325, 'roof': 'retractable'},
    'Milwaukee,US':      {'lat': 43.0280, 'lon': -87.9712,  'roof': 'retractable'},

    # Open Air — always monitored
    'Anaheim,US':        {'lat': 33.8003, 'lon': -117.8827, 'roof': 'open'},
    'Los Angeles,US':    {'lat': 34.0739, 'lon': -118.2400, 'roof': 'open'},
    'San Francisco,US':  {'lat': 37.7786, 'lon': -122.3893, 'roof': 'open'},
    'San Diego,US':      {'lat': 32.7076, 'lon': -117.1570, 'roof': 'open'},
    'Denver,US':         {'lat': 39.7559, 'lon': -104.9942, 'roof': 'open'},
    'Kansas City,US':    {'lat': 39.0517, 'lon': -94.4803,  'roof': 'open'},
    'Minneapolis,US':    {'lat': 44.9817, 'lon': -93.2776,  'roof': 'open'},
    'Chicago,US':        {'lat': 41.8299, 'lon': -87.6338,  'roof': 'open'},
    'Cleveland,US':      {'lat': 41.4962, 'lon': -81.6852,  'roof': 'open'},
    'Detroit,US':        {'lat': 42.3390, 'lon': -83.0485,  'roof': 'open'},
    'Cincinnati,US':     {'lat': 39.0979, 'lon': -84.5082,  'roof': 'open'},
    'St Louis,US':       {'lat': 38.6226, 'lon': -90.1928,  'roof': 'open'},
    'Pittsburgh,US':     {'lat': 40.4469, 'lon': -80.0057,  'roof': 'open'},
    'New York,US':       {'lat': 40.8296, 'lon': -73.9262,  'roof': 'open'},
    'Philadelphia,US':   {'lat': 39.9061, 'lon': -75.1665,  'roof': 'open'},
    'Washington,US':     {'lat': 38.8730, 'lon': -77.0074,  'roof': 'open'},
    'Boston,US':         {'lat': 42.3467, 'lon': -71.0972,  'roof': 'open'},
    'Baltimore,US':      {'lat': 39.2838, 'lon': -76.6216,  'roof': 'open'},
    'Atlanta,US':        {'lat': 33.8907, 'lon': -84.4677,  'roof': 'open'},
    'Oakland,US':        {'lat': 37.7516, 'lon': -122.2005, 'roof': 'open'},

    # Spring Training — Cactus League (AZ)
    'Tempe,US':          {'lat': 33.4255, 'lon': -111.9400, 'roof': 'open'},
    'Mesa,US':           {'lat': 33.3978, 'lon': -111.8336, 'roof': 'open'},
    'Scottsdale,US':     {'lat': 33.4569, 'lon': -111.9456, 'roof': 'open'},
    'Peoria,US':         {'lat': 33.5806, 'lon': -112.2374, 'roof': 'open'},
    'Surprise,US':       {'lat': 33.6284, 'lon': -112.3681, 'roof': 'open'},
    'Goodyear,US':       {'lat': 33.4350, 'lon': -112.3750, 'roof': 'open'},

    # Spring Training — Grapefruit League (FL)
    'Fort Myers,US':      {'lat': 26.6417, 'lon': -81.8557, 'roof': 'open'},
    'Sarasota,US':        {'lat': 27.3364, 'lon': -82.4625, 'roof': 'open'},
    'Bradenton,US':       {'lat': 27.5001, 'lon': -82.5748, 'roof': 'open'},
    'Port Charlotte,US':  {'lat': 26.9787, 'lon': -82.1087, 'roof': 'open'},
    'Jupiter,US':         {'lat': 26.9134, 'lon': -80.1165, 'roof': 'open'},
    'West Palm Beach,US': {'lat': 26.7153, 'lon': -80.0534, 'roof': 'open'},
    'Clearwater,US':      {'lat': 27.9659, 'lon': -82.7291, 'roof': 'open'},
    'Tampa,US':           {'lat': 27.9711, 'lon': -82.5038, 'roof': 'open'},
    'Dunedin,US':         {'lat': 28.0194, 'lon': -82.7693, 'roof': 'open'},
}

# ─────────────────────────────────────────────────────────────
# TIGHTENED THRESHOLDS — NWS data is more precise
# ─────────────────────────────────────────────────────────────
IMPACT_RULES = {
    'high_risk': {
        'rain_prob':    75,
        'wind_gust':    30,
        'lightning':    True,
        'temp_extreme': [35, 100]
    }
}


# ─────────────────────────────────────────────────────────────
# EXISTING HELPERS — unchanged
# ─────────────────────────────────────────────────────────────
def load_games():
    with open('config.json', 'r') as f:
        return json.load(f)['games']


def save_high_risk_predictions(high_risk_games, game_date):
    predictions_file = 'high_risk_predictions.json'
    try:
        with open(predictions_file, 'r') as f:
            predictions = json.load(f)
    except FileNotFoundError:
        predictions = {}

    predictions[game_date] = {
        str(game['game'].get('game_pk', '')): True
        for game in high_risk_games
        if game['game'].get('game_pk')
    }

    with open(predictions_file, 'w') as f:
        json.dump(predictions, f, indent=2)

    print(f"📊 Saved {len(high_risk_games)} high-risk prediction(s) for {game_date}")


def get_venue_name_from_location(location):
    location_to_venue = {
        'Phoenix,US':         'Chase Field',
        'Miami,US':           'loanDepot park',
        'Arlington,US':       'Globe Life Field',
        'Houston,US':         'Minute Maid Park',
        'Seattle,US':         'T-Mobile Park',
        'Milwaukee,US':       'American Family Field',
        'St Petersburg,US':   'Tropicana Field',
        'Toronto,CA':         'Rogers Centre',
        'Anaheim,US':         'Angel Stadium',
        'Los Angeles,US':     'Dodger Stadium',
        'San Francisco,US':   'Oracle Park',
        'San Diego,US':       'Petco Park',
        'Denver,US':          'Coors Field',
        'Kansas City,US':     'Kauffman Stadium',
        'Minneapolis,US':     'Target Field',
        'Chicago,US':         'Guaranteed Rate Field',
        'Cleveland,US':       'Progressive Field',
        'Detroit,US':         'Comerica Park',
        'Cincinnati,US':      'Great American Ball Park',
        'St Louis,US':        'Busch Stadium',
        'Pittsburgh,US':      'PNC Park',
        'New York,US':        'Yankee Stadium',
        'Philadelphia,US':    'Citizens Bank Park',
        'Washington,US':      'Nationals Park',
        'Boston,US':          'Fenway Park',
        'Baltimore,US':       'Oriole Park at Camden Yards',
        'Atlanta,US':         'Truist Park',
        'Tempe,US':           'Tempe Diablo Stadium',
        'Mesa,US':            'Sloan Park',
        'Scottsdale,US':      'Salt River Fields',
        'Peoria,US':          'Peoria Sports Complex',
        'Surprise,US':        'Surprise Stadium',
        'Goodyear,US':        'Goodyear Ballpark',
        'Fort Myers,US':      'Hammond Stadium',
        'Sarasota,US':        'Ed Smith Stadium',
        'Bradenton,US':       'LECOM Park',
        'Port Charlotte,US':  'Charlotte Sports Park',
        'Jupiter,US':         'Roger Dean Chevrolet Stadium',
        'West Palm Beach,US': 'The Ballpark of the Palm Beaches',
        'Clearwater,US':      'Spectrum Field',
        'Tampa,US':           'George M. Steinbrenner Field',
        'Dunedin,US':         'TD Ballpark'
    }
    return location_to_venue.get(location, 'Unknown Venue')


def get_venue_roof_info(venue_name):
    fixed_domes = {
        'Tropicana Field': {'has_roof': True, 'type': 'fixed', 'should_alert': False},
        'Rogers Centre':   {'has_roof': True, 'type': 'fixed', 'should_alert': False}
    }
    retractable_roofs = {
        'Chase Field':           {'has_roof': True, 'type': 'retractable'},
        'loanDepot park':        {'has_roof': True, 'type': 'retractable'},
        'Globe Life Field':      {'has_roof': True, 'type': 'retractable'},
        'Minute Maid Park':      {'has_roof': True, 'type': 'retractable'},
        'T-Mobile Park':         {'has_roof': True, 'type': 'retractable'},
        'American Family Field': {'has_roof': True, 'type': 'retractable'}
    }
    if venue_name in fixed_domes:
        return fixed_domes[venue_name]
    if venue_name in retractable_roofs:
        return {**retractable_roofs[venue_name], 'should_alert': None}
    return {'has_roof': False, 'type': 'open', 'should_alert': True}


def get_roof_status_from_mlb(game_date, venue_name):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={game_date}&hydrate=venue"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if 'dates' in data and len(data['dates']) > 0:
            for date_info in data['dates']:
                for game in date_info.get('games', []):
                    if game['venue']['name'] == venue_name:
                        venue_data = game.get('venue', {})
                        if 'roofType' in venue_data:
                            roof_type = venue_data.get('roofType', '').lower()
                            if roof_type == 'open':
                                print(f"   🔓 {venue_name} roof confirmed OPEN - including in alert")
                                return True
                            elif roof_type == 'closed':
                                print(f"   🔒 {venue_name} roof confirmed CLOSED - skipping alert")
                                return False
                        print(f"   ❓ {venue_name} roof status unknown - assuming closed, skipping alert")
                        return False
        print(f"   ❓ {venue_name} game not found in API - assuming closed, skipping alert")
        return False
    except Exception as e:
        print(f"   ⚠️  Error checking roof status for {venue_name}: {e}")
        print(f"   ❓ API error - assuming {venue_name} roof closed, skipping alert")
        return False


# ─────────────────────────────────────────────────────────────
# NWS WEATHER FETCH
# ─────────────────────────────────────────────────────────────
def get_nws_hourly_forecast_url(lat, lon):
    url = NWS_POINTS_URL.format(lat=lat, lon=lon)
    headers = {
        'User-Agent': NWS_USER_AGENT,
        'Accept': 'application/geo+json'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        props = resp.json()['properties']
        return props['forecastHourly'], props['timeZone']
    except Exception as e:
        raise ValueError(f"NWS grid lookup failed for ({lat},{lon}): {e}")


def get_weather_forecast(location, game_datetime):
    if location not in STADIUM_COORDINATES:
        raise ValueError(f"No coordinates found for location: {location}")

    coords = STADIUM_COORDINATES[location]
    lat, lon = coords['lat'], coords['lon']

    hourly_url, tz_name = get_nws_hourly_forecast_url(lat, lon)

    headers = {
        'User-Agent': NWS_USER_AGENT,
        'Accept': 'application/geo+json'
    }
    resp = requests.get(hourly_url, headers=headers, timeout=10)
    resp.raise_for_status()
    periods = resp.json()['properties']['periods']

    stadium_tz = pytz.timezone(tz_name)
    if game_datetime.tzinfo is None:
        pt = pytz.timezone('America/Los_Angeles')
        game_local = pt.localize(game_datetime).astimezone(stadium_tz)
    else:
        game_local = game_datetime.astimezone(stadium_tz)

    best_period = None
    for period in periods:
        period_start = datetime.fromisoformat(period['startTime'])
        period_end   = datetime.fromisoformat(period['endTime'])
        if period_start <= game_local < period_end:
            best_period = period
            break

    if not best_period:
        closest      = None
        closest_diff = float('inf')
        for period in periods:
            period_start = datetime.fromisoformat(period['startTime'])
            diff = abs((period_start - game_local).total_seconds())
            if diff < closest_diff and diff <= 3600:
                closest_diff = diff
                closest      = period
        best_period = closest

    if not best_period:
        raise ValueError(f"No NWS forecast period found for {location} at {game_local}")

    wind_str = best_period.get('windSpeed', '0 mph')
    try:
        wind_parts = [int(p) for p in wind_str.replace('mph', '').split('to') if p.strip().isdigit()]
        wind_speed = max(wind_parts) if wind_parts else 0
    except Exception:
        wind_speed = 0

    pop_data  = best_period.get('probabilityOfPrecipitation', {})
    rain_prob = pop_data.get('value') if isinstance(pop_data, dict) else 0
    rain_prob = rain_prob or 0

    temp = best_period.get('temperature', 72)

    # Step 8: Thunderstorm detection — SMARTER ✅
    # Ignores "Slight Chance", "Isolated", "Chance" thunderstorms
    # Also requires rain_prob >= 40% so low-probability storms don't trigger HIGH RISK
    short_forecast    = best_period.get('shortForecast', '')
    detailed_forecast = best_period.get('detailedForecast', '')
    combined          = (short_forecast + ' ' + detailed_forecast).lower()

    # Check if it's only a slight/isolated/chance storm (not a real threat)
    is_slight_chance = any(w in combined for w in [
        'slight chance', 'isolated', 'chance thunderstorm',
        'chance of thunderstorm', 'few thunderstorm'
    ])

    # Only flag thunderstorm if it's a real threat — not just a slight chance
    # AND rain probability is meaningful (≥40%)
    has_thunderstorm = (
        any(w in combined for w in ['thunder', 'tstm', 'lightning'])
        and not is_slight_chance   # ✅ Ignore slight chance thunderstorms
        and rain_prob >= 40        # ✅ Require meaningful rain probability
    )

    print(f"   📡 NWS [{location}] @ {game_local.strftime('%I:%M %p %Z')}: "
          f"{temp}°F | {rain_prob}% rain | {wind_speed}mph wind | "
          f"{short_forecast} | ⚡thunderstorm={has_thunderstorm}")

    return {
        'temp':             temp,
        'feels_like':       temp,
        'rain_prob':        rain_prob,
        'conditions':       short_forecast,
        'wind_speed':       wind_speed,
        'wind_gust':        wind_speed,
        'humidity':         0,
        'has_thunderstorm': has_thunderstorm,
        'nws_period_start': best_period.get('startTime', '')
    }


# ─────────────────────────────────────────────────────────────
# RISK CHECK
# ─────────────────────────────────────────────────────────────
def is_high_risk(weather):
    return (
        weather['rain_prob']  >= IMPACT_RULES['high_risk']['rain_prob']  or
        weather['wind_gust']  >= IMPACT_RULES['high_risk']['wind_gust']  or
        weather['has_thunderstorm']                                        or
        weather['temp']       <= IMPACT_RULES['high_risk']['temp_extreme'][0] or
        weather['temp']       >= IMPACT_RULES['high_risk']['temp_extreme'][1]
    )


# ─────────────────────────────────────────────────────────────
# SLACK MESSAGE BUILDER
# ─────────────────────────────────────────────────────────────
def build_high_risk_message(high_risk_games):
    pacific_tz = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pacific_tz)

    if not high_risk_games:
        return {
            "text": "✅ No high-risk weather games",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ All Clear - No High-Risk Weather Games",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "No games currently at high risk due to weather."
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"Checked at {now.strftime('%I:%M %p')} PT  |  "
                                f"Source: 🌐 National Weather Service (NWS)"
                            )
                        }
                    ]
                }
            ]
        }

    message = {
        "text": f"🚨 {len(high_risk_games)} HIGH RISK weather game(s)",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 HIGH RISK WEATHER ALERT",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{len(high_risk_games)} game(s) at HIGH RISK* requiring attention "
                        f"for daypart/guide adjustments"
                    )
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"Updated: {now.strftime('%I:%M %p')} PT  |  "
                            f"Source: 🌐 National Weather Service (NWS)"
                        )
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
    }

    for game_data in high_risk_games:
        game    = game_data['game']
        weather = game_data['weather']

        game_datetime = datetime.strptime(
            f"{game['date']} {game['time']}", "%Y-%m-%d %H:%M"
        )
        date_str = game_datetime.strftime("%A, %B %d")
        time_str = game_datetime.strftime("%I:%M %p")

        weather_details  = f"🌡️ {weather['temp']:.0f}°F  |  "
        weather_details += f"💧 Rain: *{weather['rain_prob']:.0f}%*  |  "
        weather_details += f"💨 Wind: {weather['wind_speed']:.0f} mph"

        if weather['wind_gust'] > weather['wind_speed'] + 5:
            weather_details += f" (gusts {weather['wind_gust']:.0f} mph)"

        if weather['has_thunderstorm']:
            weather_details += "  |  ⚡ *Thunderstorms*"

        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*🔴 {game['opponent']}*\n"
                    f"{date_str} at {time_str} PT\n"
                    f"{weather_details}"
                )
            }
        })
        message["blocks"].append({"type": "divider"})

    message["blocks"].append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": (
                    "🔴 *HIGH RISK* = ≥75% rain OR thunderstorms (≥40% rain) OR "
                    "temps ≤35°F / ≥100°F OR wind gusts ≥30 mph"
                )
            }
        ]
    })

    return message


def post_to_slack(message):
    response = requests.post(
        SLACK_WEBHOOK,
        json=message,
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise ValueError(f"Slack request failed: {response.status_code}, {response.text}")
    return response.status_code == 200


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    try:
        games = load_games()

        if not games:
            print("ℹ️  No MLB games scheduled - skipping alert")
            log_workflow_run('skipped')
            return

        pacific_tz = pytz.timezone('America/Los_Angeles')
        now = datetime.now(pacific_tz)

        print(f"🏟️  Filtering games by roof status...")
        games_to_check = []

        for game in games:
            try:
                venue_name = get_venue_name_from_location(game['location'])
                roof_info  = get_venue_roof_info(venue_name)

                if roof_info['type'] == 'fixed':
                    print(f"   ⏭️  Skipping {game['opponent']} at {venue_name} (fixed dome / roof always closed)")
                    continue

                if roof_info['type'] == 'retractable':
                    should_alert = get_roof_status_from_mlb(game['date'], venue_name)
                    if should_alert:
                        games_to_check.append(game)
                    continue

                print(f"   ✅ Including {game['opponent']} at {venue_name} (open-air)")
                games_to_check.append(game)

            except Exception as filter_error:
                print(f"   ⚠️  Error filtering {game.get('opponent', 'Unknown')}: {filter_error}")
                games_to_check.append(game)
                continue

        print(f"\n📊 Roof filtering: {len(games_to_check)} of {len(games)} games need weather monitoring\n")

        if not games_to_check:
            print("ℹ️  No games need weather monitoring (all in domed/closed-roof stadiums)")
            log_workflow_run('skipped')
            return

        high_risk_games = []
        print(f"🔍 Checking NWS weather for high-risk games...")

        upcoming_count = 0
        for game in games_to_check:
            game_datetime = datetime.strptime(
                f"{game['date']} {game['time']}", "%Y-%m-%d %H:%M"
            )

            if now.replace(tzinfo=None) <= game_datetime <= now.replace(tzinfo=None) + timedelta(hours=48):
                upcoming_count += 1
                try:
                    weather = get_weather_forecast(game['location'], game_datetime)

                    if is_high_risk(weather):
                        high_risk_games.append({
                            'game':    game,
                            'weather': weather
                        })
                        print(f"  🔴 HIGH RISK: {game['opponent']} - {game['date']} {game['time']}")
                    else:
                        print(f"  🟢 Clear: {game['opponent']}")

                except Exception as weather_error:
                    print(f"  ⚠️  NWS weather error for {game['opponent']}: {weather_error}")
                    continue

        if upcoming_count == 0:
            print("ℹ️  No games in next 48 hours - skipping alert (off-day)")
            log_workflow_run('skipped')
            return

        print(f"\n📊 Found {len(high_risk_games)} high-risk game(s) out of {upcoming_count} total")

        if high_risk_games:
            save_high_risk_predictions(high_risk_games, now.strftime('%Y-%m-%d'))

        message = build_high_risk_message(high_risk_games)

        if post_to_slack(message):
            if high_risk_games:
                print(f"✅ High-risk alert posted for {len(high_risk_games)} game(s)")
            else:
                print("✅ All-clear message posted")
            log_alert('high_risk')
            log_workflow_run('success')
        else:
            print("❌ Failed to post to Slack")
            log_workflow_run('failed')

    except Exception as e:
        print(f"❌ Fatal error in high-risk alert: {e}")
        log_workflow_run('failed')
        raise


if __name__ == "__main__":
    main()
