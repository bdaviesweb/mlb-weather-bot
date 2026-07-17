# mlb_game_status_monitor.py
# Updated: April 2026
# Changes:
#   - Added timeout=10 to requests.get() in get_mlb_game_status()
#   - Fixed check_and_log_false_positives() — now only logs ONCE per game
#     when game reaches FINAL state, not every 10-min cycle
#   - Added false_positive_logged.json to track already-logged false positives
#   - Prevents 406+ false positive inflation from repeated 10-min cycles

import os
import json
import requests
from datetime import datetime
import pytz
from analytics import log_alert, log_workflow_run, log_prediction_accuracy
import notifications
from venues import get_venue_roof_type

SLACK_WEBHOOK = os.environ.get('HIGH_RISK_WEBHOOK_URL')
STATE_FILE    = 'game_states.json'

# ── Normalized state constants ─────────────────────────────────────────────────
STATE_DELAYED   = "DELAYED"
STATE_POSTPONED = "POSTPONED"
STATE_LIVE      = "LIVE"
STATE_FINAL     = "FINAL"
STATE_PREVIEW   = "PREVIEW"
STATE_SUSPENDED = "SUSPENDED"


def load_games():
    with open('config.json', 'r') as f:
        return json.load(f)['games']


def load_game_states():
    """Load previously tracked game states"""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_game_states(states):
    """Save game states for next run"""
    with open(STATE_FILE, 'w') as f:
        json.dump(states, f, indent=2)


def get_venue_info_from_game(game):
    venue      = game.get('venue', {})
    venue_name = venue.get('name', 'Unknown Venue')
    roof_info  = get_venue_roof_type(venue_name)
    return {
        'name':             venue_name,
        'roof_type':        roof_info['type'],
        'roof_description': roof_info['description']
    }


def get_mlb_game_status(game_date):
    url = (f"https://statsapi.mlb.com/api/v1/schedule"
           f"?sportId=1&date={game_date}&hydrate=linescore,venue")
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        games_status = []

        if 'dates' in data and len(data['dates']) > 0:
            for date_info in data['dates']:
                for game in date_info.get('games', []):
                    away_team = game['teams']['away']['team']['name']
                    home_team = game['teams']['home']['team']['name']
                    game_pk   = game['gamePk']
                    status    = game['status']

                    detailed_state = status['detailedState']
                    abstract_state = status['abstractGameState']
                    reason         = status.get('reason', '')

                    venue_info     = get_venue_info_from_game(game)
                    linescore      = game.get('linescore', {})
                    away_score     = game['teams']['away'].get('score', 0)
                    home_score     = game['teams']['home'].get('score', 0)
                    current_inning = linescore.get('currentInning', None)
                    inning_state   = linescore.get('inningState', '')

                    games_status.append({
                        'game_pk':        game_pk,
                        'matchup':        f"{away_team} vs {home_team}",
                        'away_team':      away_team,
                        'home_team':      home_team,
                        'away_score':     away_score,
                        'home_score':     home_score,
                        'inning':         current_inning,
                        'inning_state':   inning_state,
                        'detailed_state': detailed_state,
                        'abstract_state': abstract_state,
                        'reason':         reason,
                        'venue':          venue_info
                    })
        return games_status
    except Exception as e:
        print(f"Error fetching MLB game status: {e}")
        return []


def is_weather_related(reason, detailed_state):
    """
    Check if a delay/postponement is weather-related.
    Does NOT include 'postponed' as a keyword — postponed is a
    separate state, not a delay type.
    """
    combined = detailed_state.lower() + ' ' + reason.lower()
    weather_keywords = ['rain', 'weather', 'storm', 'lightning',
                        'inclement', 'wind', 'snow', 'fog']
    return any(keyword in combined for keyword in weather_keywords)


def is_active_weather_delay(game_status):
    """
    Returns True ONLY if the game is in an active in-game weather delay.
    Explicitly excludes Postponed and Suspended states.
    """
    state = game_status['detailed_state'].lower()
    if 'postponed' in state or 'suspend' in state:
        return False
    is_delayed = 'delay' in state or 'delayed' in state
    return is_delayed and is_weather_related(
        game_status['reason'], game_status['detailed_state']
    )


def is_postponed(game_status):
    """Returns True if game is officially postponed"""
    return 'postponed' in game_status['detailed_state'].lower()


def is_suspended(game_status):
    """Returns True if game is officially suspended"""
    return 'suspend' in game_status['detailed_state'].lower()


def normalize_api_state(game_status):
    """
    Convert raw MLB API state to our normalized internal state constant.
    Ensures consistent comparisons throughout monitor_games().
    """
    detailed = game_status['detailed_state'].lower()
    abstract = game_status['abstract_state']

    if 'postponed' in detailed:
        return STATE_POSTPONED
    if 'suspend' in detailed:
        return STATE_SUSPENDED
    if 'delay' in detailed:
        return STATE_DELAYED
    if abstract == 'Live':
        return STATE_LIVE
    if abstract == 'Final':
        return STATE_FINAL
    return STATE_PREVIEW


def check_and_log_prediction_accuracy(game_pk, game_date):
    """
    When an actual delay/postponement occurs, check if we predicted it
    and log the accuracy result to analytics.
    """
    predictions_file = 'high_risk_predictions.json'
    try:
        with open(predictions_file, 'r') as f:
            predictions = json.load(f)

        today_predictions = predictions.get(game_date, {})
        was_predicted     = str(game_pk) in today_predictions

        log_prediction_accuracy(
            predicted_delay=was_predicted,
            actual_delay=True
        )

        if was_predicted:
            print(f"📊 Accuracy logged: ✅ TRUE POSITIVE — predicted and delay occurred")
        else:
            print(f"📊 Accuracy logged: ❌ FALSE NEGATIVE — delay occurred but not predicted")

    except FileNotFoundError:
        log_prediction_accuracy(predicted_delay=False, actual_delay=True)
        print(f"📊 Accuracy logged: ❌ FALSE NEGATIVE — no predictions on file for today")


def check_and_log_false_positives(game_date):
    """
    Check predicted games that finished as FINAL without any delay.
    Only logs false positive ONCE per game when it reaches FINAL state.
    Uses false_positive_logged.json to prevent logging same game
    multiple times across 10-min monitoring cycles.
    """
    predictions_file   = 'high_risk_predictions.json'
    false_pos_log_file = 'false_positive_logged.json'

    try:
        with open(predictions_file, 'r') as f:
            predictions = json.load(f)

        today_predictions = predictions.get(game_date, {})
        if not today_predictions:
            return

        # Load which game PKs already logged as false positives
        try:
            with open(false_pos_log_file, 'r') as f:
                already_logged = json.load(f)
        except FileNotFoundError:
            already_logged = {}

        today_logged = already_logged.get(game_date, [])
        states       = load_game_states()
        new_logs     = []

        for game_pk in today_predictions:
            # Skip if already logged as false positive
            if game_pk in today_logged:
                continue

            state = states.get(str(game_pk), {}).get('state', '')

            # Only log as false positive when game is FINAL
            # — meaning it completed without ever being delayed
            if state == STATE_FINAL:
                log_prediction_accuracy(
                    predicted_delay=True,
                    actual_delay=False
                )
                print(f"📊 Accuracy logged: ❌ FALSE POSITIVE — "
                      f"predicted delay but game finished normally (pk: {game_pk})")
                new_logs.append(game_pk)

        # Persist which games have been logged to prevent double counting
        if new_logs:
            already_logged[game_date] = today_logged + new_logs
            with open(false_pos_log_file, 'w') as f:
                json.dump(already_logged, f, indent=2)

    except FileNotFoundError:
        pass


def format_score_inning(game_status):
    away         = game_status['away_team']
    home         = game_status['home_team']
    away_score   = game_status['away_score']
    home_score   = game_status['home_score']
    inning       = game_status['inning']
    inning_state = game_status['inning_state']

    score_text = f"{away} {away_score}, {home} {home_score}"

    if inning:
        inning_map = {
            'Middle': f"Middle {inning}",
            'Top':    f"Top {inning}",
            'Bottom': f"Bottom {inning}",
            'End':    f"End of {inning}"
        }
        inning_text = inning_map.get(inning_state, f"Inning {inning}")
        return score_text, inning_text

    return None, None


def send_delay_alert(game_status, alert_type):
    pacific_tz = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pacific_tz)

    venue            = game_status.get('venue', {})
    venue_name       = venue.get('name', 'Unknown Venue')
    roof_description = venue.get('roof_description', '')

    if alert_type == STATE_DELAYED:
        emoji = "🚨"
        title = "RAIN DELAY DETECTED"
        text  = f"🚨 Rain delay: {game_status['matchup']}"
    elif alert_type == "RESUME":
        emoji = "✅"
        title = "GAME RESUMING"
        text  = f"✅ Game resuming: {game_status['matchup']}"
    elif alert_type == STATE_POSTPONED:
        emoji = "📅"
        title = "GAME POSTPONED"
        text  = f"📅 Game postponed: {game_status['matchup']}"
    elif alert_type == STATE_SUSPENDED:
        emoji = "⏸️"
        title = "GAME SUSPENDED"
        text  = f"⏸️ Game suspended: {game_status['matchup']}"
    else:
        emoji = "ℹ️"
        title = "GAME STATUS UPDATE"
        text  = f"ℹ️ Status update: {game_status['matchup']}"

    message = {
        "text": text,
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Game:*\n⚾ {game_status['matchup']}"},
                    {"type": "mrkdwn", "text": f"*Status:*\n{game_status['detailed_state']}"}
                ]
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Venue:*\n{venue_name}"},
                    {"type": "mrkdwn", "text": f"*Stadium Type:*\n{roof_description}"}
                ]
            }
        ]
    }

    score_text, inning_text = format_score_inning(game_status)
    if score_text and alert_type in [STATE_DELAYED, "RESUME"]:
        message["blocks"].append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Score:*\n{score_text}"},
                {"type": "mrkdwn", "text": f"*Inning:*\n{inning_text}"}
            ]
        })

    if game_status['reason']:
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Reason:* {game_status['reason']}"
            }
        })

    if venue.get('roof_type') in ['fixed_dome', 'retractable']:
        if alert_type in [STATE_DELAYED, STATE_POSTPONED]:
            note = (
                "⚠️ *Note:* Stadium has retractable roof — may have been open or roof malfunction"
                if venue.get('roof_type') == 'retractable'
                else "⚠️ *Note:* Fixed dome stadium — delay likely non-weather related"
            )
            message["blocks"].append({
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": note}]
            })

    message["blocks"].append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"<!channel> Alert sent at {now.strftime('%I:%M %p')} PT"
            }
        ]
    })

    delivered = notifications.notify(
        f"MLB Game Status Alert: {game_status['matchup']}",
        message,
        webhook_url=SLACK_WEBHOOK,
        webhook_name="HIGH_RISK_WEBHOOK_URL",
        labels=["weather-alert", "game-status"],
    )

    if delivered:
        print(f"✅ {alert_type} alert sent for {game_status['matchup']} at {venue_name}")
        alert_map = {
            STATE_DELAYED:   'delay',
            "RESUME":        'resumption',
            STATE_POSTPONED: 'postponement',
            STATE_SUSPENDED: 'postponement'
        }
        if alert_type in alert_map:
            log_alert(alert_map[alert_type])
        return True
    else:
        print("❌ Failed to send alert")
        return False


def monitor_games():
    pacific_tz = pytz.timezone('America/Los_Angeles')
    now   = datetime.now(pacific_tz)
    today = now.strftime('%Y-%m-%d')

    print(f"🔍 Monitoring MLB games for {today}...")

    previous_states = load_game_states()
    current_states  = {}

    games = get_mlb_game_status(today)

    if not games:
        print("No games found for today")
        return

    print(f"📅 Found {len(games)} game(s)")

    for game in games:
        game_pk        = str(game['game_pk'])
        venue_name     = game['venue']['name']
        previous_entry = previous_states.get(game_pk, {})
        previous_state = previous_entry.get('state')

        current_normalized = normalize_api_state(game)

        if previous_state is None:
            print(f"   🔍 First seen: {game['matchup']} at {venue_name} "
                  f"({game['venue']['roof_description']}) — state: {current_normalized}")

        # ── Check order: POSTPONED → SUSPENDED → DELAYED → RESUME ─────────────
        if is_postponed(game) and previous_state != STATE_POSTPONED:
            print(f"📅 POSTPONED: {game['matchup']} at {venue_name}")
            if is_weather_related(game['reason'], game['detailed_state']):
                send_delay_alert(game, STATE_POSTPONED)
                check_and_log_prediction_accuracy(game_pk, today)
            else:
                print(f"   ℹ️  Non-weather postponement — skipping alert")
            current_states[game_pk] = {'state': STATE_POSTPONED, 'matchup': game['matchup']}

        elif is_suspended(game) and previous_state != STATE_SUSPENDED:
            print(f"⏸️ SUSPENDED: {game['matchup']} at {venue_name}")
            send_delay_alert(game, STATE_SUSPENDED)
            current_states[game_pk] = {'state': STATE_SUSPENDED, 'matchup': game['matchup']}

        elif is_active_weather_delay(game) and previous_state != STATE_DELAYED:
            print(f"🚨 RAIN DELAY: {game['matchup']} at {venue_name}")
            send_delay_alert(game, STATE_DELAYED)
            check_and_log_prediction_accuracy(game_pk, today)
            current_states[game_pk] = {'state': STATE_DELAYED, 'matchup': game['matchup']}

        elif previous_state == STATE_DELAYED and current_normalized == STATE_LIVE:
            print(f"✅ RESUMING: {game['matchup']} at {venue_name}")
            send_delay_alert(game, "RESUME")
            current_states[game_pk] = {'state': STATE_LIVE, 'matchup': game['matchup']}

        else:
            current_states[game_pk] = {
                'state':   previous_state if previous_state else current_normalized,
                'matchup': game['matchup']
            }
            print(f"   ✅ No change: {game['matchup']} — {current_normalized}")

    # ✅ Check for false positives — only logs ONCE per game when FINAL
    check_and_log_false_positives(today)

    save_game_states(current_states)
    print(f"\n✅ Monitoring complete — checked {len(games)} games")


def main():
    try:
        monitor_games()
        log_workflow_run('success')
    except Exception as e:
        print(f"❌ Error in game status monitor: {e}")
        log_workflow_run('failed')
        raise


if __name__ == "__main__":
    main()
