# test_venues.py
# Updated: April 2026
# Tests NWS API connectivity for all MLB stadium coordinates
# No API key required — NWS is free and open
# Run manually via test-venues.yml workflow

import requests
from venues import TEST_VENUES

NWS_USER_AGENT = "MLBWeatherBot/2.0 (github.com/Sports-Weather2/mlb-weather-bot)"

# All stadium coordinates are defined in venues.py
VENUES = TEST_VENUES

def test_nws_venue(venue_name, lat, lon):
    """
    Test NWS API connectivity for a stadium lat/lon.
    Step 1: Get gridpoint URL
    Step 2: Fetch hourly forecast
    Returns True if both steps succeed.
    """
    headers = {
        'User-Agent': NWS_USER_AGENT,
        'Accept': 'application/geo+json'
    }

    # ── Step 1: Points lookup ──────────────────────────────────
    points_url = f"https://api.weather.gov/points/{lat},{lon}"
    try:
        resp = requests.get(points_url, headers=headers, timeout=10)

        if resp.status_code != 200:
            print(f"❌ {venue_name:<45} | FAILED points lookup: HTTP {resp.status_code}")
            return False

        props        = resp.json().get('properties', {})
        hourly_url   = props.get('forecastHourly')
        grid_id      = props.get('gridId', '?')
        grid_x       = props.get('gridX', '?')
        grid_y       = props.get('gridY', '?')
        tz           = props.get('timeZone', '?')

        if not hourly_url:
            print(f"❌ {venue_name:<45} | FAILED: No hourly URL in response")
            return False

    except requests.exceptions.Timeout:
        print(f"❌ {venue_name:<45} | ERROR: Points request timed out")
        return False
    except Exception as e:
        print(f"❌ {venue_name:<45} | ERROR: {e}")
        return False

    # ── Step 2: Hourly forecast fetch ─────────────────────────
    try:
        resp2 = requests.get(hourly_url, headers=headers, timeout=10)

        if resp2.status_code != 200:
            print(f"❌ {venue_name:<45} | FAILED hourly fetch: HTTP {resp2.status_code}")
            return False

        periods = resp2.json().get('properties', {}).get('periods', [])

        if not periods:
            print(f"❌ {venue_name:<45} | FAILED: No forecast periods returned")
            return False

        # Show first period as sample
        first         = periods[0]
        temp          = first.get('temperature', '?')
        unit          = first.get('temperatureUnit', 'F')
        forecast      = first.get('shortForecast', '?')
        pop           = first.get('probabilityOfPrecipitation', {})
        rain_pct      = pop.get('value', 0) if isinstance(pop, dict) else 0

        print(f"✅ {venue_name:<45} | {grid_id}/{grid_x},{grid_y} | "
              f"{tz:<30} | {temp}°{unit} | {rain_pct}% rain | {forecast}")
        return True

    except requests.exceptions.Timeout:
        print(f"❌ {venue_name:<45} | ERROR: Hourly forecast request timed out")
        return False
    except Exception as e:
        print(f"❌ {venue_name:<45} | ERROR: {e}")
        return False


def main():
    print("🔍 Testing NWS API for All MLB Venue Coordinates...\n")
    print(f"{'VENUE NAME':<45} | {'NWS GRID':<20} | {'TIMEZONE':<30} | FORECAST SAMPLE")
    print("-" * 130)

    sections = {
        "🏟️  FIXED DOME STADIUMS (excluded from alerts)": [
            'Tropicana Field (Fixed Dome)',
            'Rogers Centre (Fixed Dome)'
        ],
        "🔄 RETRACTABLE ROOF STADIUMS": [
            'Chase Field', 'loanDepot park', 'Globe Life Field',
            'Minute Maid Park', 'T-Mobile Park', 'American Family Field'
        ],
        "☀️  OPEN AIR — REGULAR SEASON": [
            'Angel Stadium', 'Dodger Stadium', 'Oracle Park', 'Petco Park',
            'Coors Field', 'Kauffman Stadium', 'Target Field',
            'Guaranteed Rate Field', 'Progressive Field', 'Comerica Park',
            'Great American Ball Park', 'Busch Stadium', 'PNC Park',
            'Wrigley Field', 'Yankee Stadium', 'Citi Field',
            'Citizens Bank Park', 'Nationals Park', 'Fenway Park',
            'Oriole Park at Camden Yards', 'Truist Park',
            'Sutter Health Park (Athletics)'
        ],
        "🌵 SPRING TRAINING — CACTUS LEAGUE (AZ)": [
            'Tempe Diablo Stadium', 'Camelback Ranch', 'Sloan Park',
            'Salt River Fields', 'Peoria Sports Complex', 'Surprise Stadium',
            'Goodyear Ballpark', 'American Family Fields of Phoenix'
        ],
        "🌴 SPRING TRAINING — GRAPEFRUIT LEAGUE (FL)": [
            'JetBlue Park', 'Ed Smith Stadium', 'LECOM Park',
            'Charlotte Sports Park', 'Hammond Stadium',
            'Roger Dean Chevrolet Stadium', 'Clover Park',
            'The Ballpark of the Palm Beaches', 'Spectrum Field',
            'George M. Steinbrenner Field', 'TD Ballpark'
        ]
    }

    total   = 0
    passed  = 0
    failed  = 0

    for section_name, venue_list in sections.items():
        print(f"\n{section_name}:")
        for venue in venue_list:
            if venue in VENUES:
                coords  = VENUES[venue]
                result  = test_nws_venue(venue, coords['lat'], coords['lon'])
                total  += 1
                if result:
                    passed += 1
                else:
                    failed += 1

    print("\n" + "=" * 130)
    print(f"📊 Results: {passed}/{total} venues passed  |  "
          f"{'✅ All good!' if failed == 0 else f'❌ {failed} venue(s) need attention'}")
    print("🌐 Source: National Weather Service (NWS) API — no API key required")
    print("=" * 130)


if __name__ == "__main__":
    main()
