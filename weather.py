from datetime import datetime

import pytz
import requests

from venues import STADIUM_COORDINATES

NWS_USER_AGENT = "MLBWeatherBot/2.0 (github.com/Sports-Weather2/mlb-weather-bot)"
NWS_POINTS_URL = "https://api.weather.gov/points/{lat},{lon}"

IMPACT_RULES = {
    'high_risk': {
        'rain_prob': 80,
        'wind_gust': 30,
        'lightning': True,
        'temp_extreme': [35, 100]
    },
    'monitor': {
        'rain_prob': 35,
        'wind_sustained': 20,
        'temp_concern': [40, 95]
    }
}


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


def parse_wind_speed(wind_str):
    try:
        wind_parts = [
            int(p)
            for p in wind_str.replace('mph', '').split('to')
            if p.strip().isdigit()
        ]
        return max(wind_parts) if wind_parts else 0
    except Exception:
        return 0


def detect_active_thunderstorm(combined_forecast, rain_prob):
    is_slight_chance = any(w in combined_forecast for w in [
        'slight chance', 'isolated', 'chance thunderstorm',
        'chance of thunderstorm', 'few thunderstorm',
        'scattered thunderstorm',
        'chance showers and thunderstorm',
        'chance shower'
    ])

    return (
        any(w in combined_forecast for w in ['thunder', 'tstm', 'lightning'])
        and not is_slight_chance
        and rain_prob >= 40
    )


def build_trigger_reason(rain_prob, has_thunderstorm, wind_speed, temp):
    trigger_reasons = []
    high_risk = IMPACT_RULES['high_risk']

    if rain_prob >= high_risk['rain_prob']:
        trigger_reasons.append(
            f"Rain {rain_prob:.0f}% ≥ {high_risk['rain_prob']}% threshold"
        )
    if has_thunderstorm:
        trigger_reasons.append(f"Active thunderstorms + Rain {rain_prob:.0f}%")
    if wind_speed >= high_risk['wind_gust']:
        trigger_reasons.append(
            f"Wind {wind_speed} mph ≥ {high_risk['wind_gust']} mph threshold"
        )
    if temp <= high_risk['temp_extreme'][0]:
        trigger_reasons.append(
            f"Temp {temp}°F ≤ {high_risk['temp_extreme'][0]}°F threshold"
        )
    if temp >= high_risk['temp_extreme'][1]:
        trigger_reasons.append(
            f"Temp {temp}°F ≥ {high_risk['temp_extreme'][1]}°F threshold"
        )

    return ' | '.join(trigger_reasons) if trigger_reasons else 'No trigger'


def build_delay_probability(rain_prob, has_thunderstorm, wind_speed, temp):
    high_risk = IMPACT_RULES['high_risk']

    if rain_prob >= 90 or (has_thunderstorm and rain_prob >= 70):
        return "🔴 *VERY HIGH* — Delay or postponement likely"
    if rain_prob >= 80 or (has_thunderstorm and rain_prob >= 50):
        return "🟠 *HIGH* — Delay probable at game time"
    if has_thunderstorm or wind_speed >= high_risk['wind_gust']:
        return "🟡 *ELEVATED* — Conditions may impact play"
    if temp <= high_risk['temp_extreme'][0]:
        return "🟡 *ELEVATED* — Extreme cold may impact play"
    return "🟡 *ELEVATED* — Weather warrants monitoring"


def build_weather_from_period(location, game_local, period):
    wind_speed = parse_wind_speed(period.get('windSpeed', '0 mph'))

    pop_data = period.get('probabilityOfPrecipitation', {})
    rain_prob = pop_data.get('value') if isinstance(pop_data, dict) else 0
    rain_prob = rain_prob or 0

    temp = period.get('temperature', 72)
    short_forecast = period.get('shortForecast', '')
    detailed_forecast = period.get('detailedForecast', '')
    combined = (short_forecast + ' ' + detailed_forecast).lower()
    has_thunderstorm = detect_active_thunderstorm(combined, rain_prob)
    trigger_reason = build_trigger_reason(
        rain_prob,
        has_thunderstorm,
        wind_speed,
        temp
    )
    delay_probability = build_delay_probability(
        rain_prob,
        has_thunderstorm,
        wind_speed,
        temp
    )

    print(f"   📡 NWS [{location}] @ {game_local.strftime('%I:%M %p %Z')}: "
          f"{temp}°F | {rain_prob}% rain | {wind_speed}mph wind | "
          f"{short_forecast} | ⚡thunderstorm={has_thunderstorm} | "
          f"trigger={trigger_reason}")

    return {
        'temp': temp,
        'feels_like': temp,
        'rain_prob': rain_prob,
        'conditions': short_forecast,
        'wind_speed': wind_speed,
        'wind_gust': wind_speed,
        'humidity': 0,
        'has_thunderstorm': has_thunderstorm,
        'nws_period_start': period.get('startTime', ''),
        'trigger_reason': trigger_reason,
        'delay_probability': delay_probability
    }


def find_best_period(periods, game_local):
    for period in periods:
        period_start = datetime.fromisoformat(period['startTime'])
        period_end = datetime.fromisoformat(period['endTime'])
        if period_start <= game_local < period_end:
            return period

    closest = None
    closest_diff = float('inf')
    for period in periods:
        period_start = datetime.fromisoformat(period['startTime'])
        diff = abs((period_start - game_local).total_seconds())
        if diff < closest_diff and diff <= 3600:
            closest_diff = diff
            closest = period

    return closest


def get_weather_forecast(location, game_datetime):
    if location not in STADIUM_COORDINATES:
        raise ValueError(f"No coordinates found for location: {location}")

    coords = STADIUM_COORDINATES[location]
    hourly_url, tz_name = get_nws_hourly_forecast_url(coords['lat'], coords['lon'])

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

    best_period = find_best_period(periods, game_local)
    if not best_period:
        raise ValueError(f"No NWS forecast period found for {location} at {game_local}")

    return build_weather_from_period(location, game_local, best_period)


def is_high_risk(weather):
    high_risk = IMPACT_RULES['high_risk']
    return (
        weather['rain_prob'] >= high_risk['rain_prob'] or
        weather['wind_gust'] >= high_risk['wind_gust'] or
        weather['has_thunderstorm'] or
        weather['temp'] <= high_risk['temp_extreme'][0] or
        weather['temp'] >= high_risk['temp_extreme'][1]
    )


def calculate_game_impact(weather):
    if is_high_risk(weather):
        return {
            'level': 'HIGH_RISK',
            'emoji': '🔴',
            'status': 'HIGH RISK',
            'color': '#dc3545'
        }

    monitor = IMPACT_RULES['monitor']
    if (weather['rain_prob'] >= monitor['rain_prob'] or
        weather['wind_speed'] >= monitor['wind_sustained'] or
        weather['temp'] <= monitor['temp_concern'][0] or
        weather['temp'] >= monitor['temp_concern'][1]):
        return {
            'level': 'MONITOR',
            'emoji': '🟡',
            'status': 'MONITOR',
            'color': '#ffc107'
        }

    return {
        'level': 'CLEAR',
        'emoji': '🟢',
        'status': 'CLEAR',
        'color': '#28a745'
    }
