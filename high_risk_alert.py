# high_risk_alert.py
# Updated: April 2026
# Weather API: National Weather Service (NWS) — replaces OpenWeatherMap
# Changes:
#   - Removed WEATHER_API_KEY / OpenWeatherMap entirely
#   - NWS API: no API key, hourly updates, ~92-95% accuracy (US only)
#   - Toronto (Rogers Centre) hardcoded as fixed dome — roof always closed
#   - get_weather_forecast() replaced with NWS implementation
#   - Rain threshold tightened: HIGH_RISK 75% → 80%
#   - Cold temp threshold tightened: 20°F → 35°F
#   - Forecast targets exact game start hour (not closest 3-hr bucket)
#   - Thunderstorm detection smarter: ignores "Slight Chance" +
#     "Scattered" + "Chance Showers And Thunderstorms" and requires rain >= 40%
#   - Added "Why Triggered" reason line to HIGH RISK alerts
#   - Added delay probability language to HIGH RISK alerts
#   - Slack footer updated to reflect new thresholds

import os
import json
import requests
import pytz
from datetime import datetime, timedelta
from analytics import log_alert, log_workflow_run, log_prediction_accuracy
from venues import get_venue_name_from_location, get_venue_roof_info
from weather import get_weather_forecast, is_high_risk

SLACK_WEBHOOK = os.environ.get('HIGH_RISK_WEBHOOK_URL')


# ─────────────────────────────────────────────────────────────
# HELPERS
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
                    f"{weather_details}\n"
                    f"📋 *Why:* {weather.get('trigger_reason', 'N/A')}\n"
                    f"🎯 *Delay Probability:* {weather.get('delay_probability', 'N/A')}"
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
                    "🔴 *HIGH RISK* = ≥80% rain OR thunderstorms (≥40% rain) OR "
                    "temps ≤35°F / ≥100°F OR wind gusts ≥30 mph"
                )
            }
        ]
    })

    return message


def post_to_slack(message):
    if not SLACK_WEBHOOK:
        print("⚠️  HIGH_RISK_WEBHOOK_URL is not configured - skipping Slack post")
        return False

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
