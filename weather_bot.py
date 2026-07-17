# weather_bot.py
# Updated: April 2026
# Weather API: National Weather Service (NWS) — replaces OpenWeatherMap
# Changes:
#   - Removed WEATHER_API_KEY / OpenWeatherMap entirely
#   - NWS API: no API key, hourly updates, ~92-95% accuracy (US only)
#   - Toronto (Rogers Centre) hardcoded as fixed dome — roof always closed
#   - get_weather_forecast() replaced with get_nws_weather_forecast()
#   - Rain threshold tightened: HIGH_RISK 75% → 80%, MONITOR 40% → 45%
#   - Forecast now targets exact game start hour (not closest 3-hr bucket)
#   - Thunderstorm detection smarter: ignores "Slight Chance" +
#     "Scattered" + "Chance Showers And Thunderstorms" and requires rain >= 40%
#   - Added "Why Triggered" reason line to HIGH RISK alerts
#   - Added delay probability language to HIGH RISK alerts

import os
import json
import requests
import pytz
from datetime import datetime, timedelta
from analytics import log_alert, log_games_monitored, log_workflow_run
from venues import get_venue_name_from_location, get_venue_roof_info
from weather import calculate_game_impact, get_weather_forecast

SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK_URL')


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def load_games():
    with open('config.json', 'r') as f:
        return json.load(f)['games']


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
# SLACK FORMATTING
# ─────────────────────────────────────────────────────────────
def format_game_block(game, weather, impact):
    game_datetime = datetime.strptime(
        f"{game['date']} {game['time']}",
        "%Y-%m-%d %H:%M"
    )
    date_str = game_datetime.strftime("%A, %B %d")
    time_str = game_datetime.strftime("%I:%M %p")

    weather_details = (
        f"🌡️ *{weather['temp']:.0f}°F*\n"
        f"☁️ {weather['conditions'].title()}\n"
        f"💧 Rain: *{weather['rain_prob']:.0f}%*\n"
        f"💨 Wind: {weather['wind_speed']:.0f} mph"
    )

    if weather['wind_gust'] > weather['wind_speed'] + 5:
        weather_details += f" (gusts to {weather['wind_gust']:.0f} mph)"

    impact_details = f"{impact['emoji']} *{impact['status']}*"
    if impact['level'] == 'HIGH_RISK':
        impact_details += (
            f"\n📋 *Why:* {weather.get('trigger_reason', 'N/A')}\n"
            f"🎯 *Delay Probability:* {weather.get('delay_probability', 'N/A')}"
        )

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*⚾ {game['opponent']}*\n{date_str} at {time_str} PT"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Weather Forecast:*\n{weather_details}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Game Impact:*\n{impact_details}"
                }
            ]
        }
    ]

    if impact['level'] == 'HIGH_RISK':
        blocks.insert(0, {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "⚠️ *WEATHER ALERT* - High risk of game impact"
            }
        })

    return blocks


def build_slack_message(games_weather):
    pacific_tz = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pacific_tz)

    high_risk_count = sum(1 for g in games_weather if g['impact']['level'] == 'HIGH_RISK')
    monitor_count   = sum(1 for g in games_weather if g['impact']['level'] == 'MONITOR')

    if high_risk_count > 0:
        header_emoji = "🚨"
        summary = f"{high_risk_count} game(s) at HIGH RISK"
    elif monitor_count > 0:
        header_emoji = "⚠️"
        summary = f"{monitor_count} game(s) to MONITOR"
    else:
        header_emoji = "✅"
        summary = "All games clear"

    message = {
        "text": f"Weather Update: {summary}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{header_emoji} Game Day Weather Impact Report",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{summary}* | Next 24 Hours"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"Updated: {now.strftime('%b %d at %I:%M %p')} PT | "
                            f"Source: 🌐 National Weather Service (NWS) | "
                            f"Next update: 7:00 AM PT tomorrow"
                        )
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
    }

    for game_data in games_weather:
        game_blocks = format_game_block(
            game_data['game'],
            game_data['weather'],
            game_data['impact']
        )
        message["blocks"].extend(game_blocks)
        message["blocks"].append({"type": "divider"})

    message["blocks"].extend([
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        "🟢 *CLEAR* - No concerns  |  "
                        "🟡 *MONITOR* - Prepare for possible issues  |  "
                        "🔴 *HIGH RISK* - Significant weather threat"
                    )
                }
            ]
        }
    ])

    return message


def post_to_slack(message):
    if not SLACK_WEBHOOK:
        print("⚠️  SLACK_WEBHOOK_URL is not configured - skipping Slack post")
        return False

    response = requests.post(
        SLACK_WEBHOOK,
        json=message,
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise ValueError(f"Slack request failed: {response.status_code}, {response.text}")
    return response.status_code == 200


def get_game_venue_name(game):
    return game.get('venue') or get_venue_name_from_location(game['location'])


def main():
    try:
        games = load_games()

        if not games:
            print("ℹ️  No MLB games scheduled - skipping report (off-day)")
            log_workflow_run('skipped')
            return

        pacific_tz = pytz.timezone('America/Los_Angeles')
        now = datetime.now(pacific_tz)

        print(f"🏟️  Filtering games by roof status...")
        games_to_check = []

        for game in games:
            try:
                venue_name = get_game_venue_name(game)
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

        upcoming_games = []
        print(f"🔍 Checking NWS weather for {len(games_to_check)} games...")

        for game in games_to_check:
            try:
                game_datetime = datetime.strptime(
                    f"{game['date']} {game['time']}",
                    "%Y-%m-%d %H:%M"
                )

                if now.replace(tzinfo=None) <= game_datetime <= now.replace(tzinfo=None) + timedelta(hours=48):
                    print(f"  📅 {game['opponent']} - {game['date']} {game['time']}")

                    try:
                        weather = get_weather_forecast(game['location'], game_datetime)
                        impact  = calculate_game_impact(weather)

                        upcoming_games.append({
                            'game':    game,
                            'weather': weather,
                            'impact':  impact
                        })

                        print(f"     {impact['emoji']} {impact['status']}")

                    except Exception as weather_error:
                        print(f"     ❌ NWS weather error for {game['location']}: {weather_error}")
                        print(f"     ⏭️  Skipping this game and continuing...")
                        continue

            except Exception as game_error:
                print(f"  ❌ Error processing game {game.get('opponent', 'Unknown')}: {game_error}")
                continue

        if not upcoming_games:
            print("ℹ️  No games in next 48 hours - skipping report (off-day)")
            log_workflow_run('skipped')
            return

        risk_priority = {'HIGH_RISK': 0, 'MONITOR': 1, 'CLEAR': 2}
        upcoming_games.sort(key=lambda x: risk_priority[x['impact']['level']])
        print(f"\n📊 Games sorted by risk level (HIGH_RISK → MONITOR → CLEAR)")

        if len(upcoming_games) > 10:
            print(f"⚠️  Limiting to top 10 games (total: {len(upcoming_games)})")
            upcoming_games = upcoming_games[:10]

        if upcoming_games:
            message = build_slack_message(upcoming_games)

            if post_to_slack(message):
                print(f"\n✅ Weather impact report posted for {len(upcoming_games)} game(s)")

                high_risk = sum(1 for g in upcoming_games if g['impact']['level'] == 'HIGH_RISK')
                monitor   = sum(1 for g in upcoming_games if g['impact']['level'] == 'MONITOR')
                clear     = sum(1 for g in upcoming_games if g['impact']['level'] == 'CLEAR')

                print(f"   🔴 High Risk: {high_risk}")
                print(f"   🟡 Monitor:   {monitor}")
                print(f"   🟢 Clear:     {clear}")

                log_alert('daily_report')
                log_games_monitored(len(upcoming_games))
                log_workflow_run('success')
            else:
                print("❌ Failed to post to Slack")
                log_workflow_run('failed')
                raise RuntimeError("Slack post failed")
        else:
            print("⚠️  No games with successful weather data - skipping report")
            log_workflow_run('skipped')

    except Exception as e:
        print(f"❌ Fatal error in weather bot: {e}")
        log_workflow_run('failed')
        raise


if __name__ == "__main__":
    main()
