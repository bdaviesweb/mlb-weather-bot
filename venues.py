STADIUM_COORDINATES = {
    'St Petersburg,US': {'lat': 27.7683, 'lon': -82.6534, 'roof': 'fixed'},
    'Toronto,CA': {'lat': 43.6414, 'lon': -79.3894, 'roof': 'fixed'},
    'Phoenix,US': {'lat': 33.4453, 'lon': -112.0667, 'roof': 'retractable'},
    'Miami,US': {'lat': 25.7781, 'lon': -80.2197, 'roof': 'retractable'},
    'Arlington,US': {'lat': 32.7512, 'lon': -97.0832, 'roof': 'retractable'},
    'Houston,US': {'lat': 29.7573, 'lon': -95.3555, 'roof': 'retractable'},
    'Seattle,US': {'lat': 47.5914, 'lon': -122.3325, 'roof': 'retractable'},
    'Milwaukee,US': {'lat': 43.0280, 'lon': -87.9712, 'roof': 'retractable'},
    'Anaheim,US': {'lat': 33.8003, 'lon': -117.8827, 'roof': 'open'},
    'Los Angeles,US': {'lat': 34.0739, 'lon': -118.2400, 'roof': 'open'},
    'San Francisco,US': {'lat': 37.7786, 'lon': -122.3893, 'roof': 'open'},
    'San Diego,US': {'lat': 32.7076, 'lon': -117.1570, 'roof': 'open'},
    'Denver,US': {'lat': 39.7559, 'lon': -104.9942, 'roof': 'open'},
    'Kansas City,US': {'lat': 39.0517, 'lon': -94.4803, 'roof': 'open'},
    'Minneapolis,US': {'lat': 44.9817, 'lon': -93.2776, 'roof': 'open'},
    'Chicago,US': {'lat': 41.8299, 'lon': -87.6338, 'roof': 'open'},
    'Cleveland,US': {'lat': 41.4962, 'lon': -81.6852, 'roof': 'open'},
    'Detroit,US': {'lat': 42.3390, 'lon': -83.0485, 'roof': 'open'},
    'Cincinnati,US': {'lat': 39.0979, 'lon': -84.5082, 'roof': 'open'},
    'St Louis,US': {'lat': 38.6226, 'lon': -90.1928, 'roof': 'open'},
    'Pittsburgh,US': {'lat': 40.4469, 'lon': -80.0057, 'roof': 'open'},
    'New York,US': {'lat': 40.8296, 'lon': -73.9262, 'roof': 'open'},
    'Philadelphia,US': {'lat': 39.9061, 'lon': -75.1665, 'roof': 'open'},
    'Washington,US': {'lat': 38.8730, 'lon': -77.0074, 'roof': 'open'},
    'Boston,US': {'lat': 42.3467, 'lon': -71.0972, 'roof': 'open'},
    'Baltimore,US': {'lat': 39.2838, 'lon': -76.6216, 'roof': 'open'},
    'Atlanta,US': {'lat': 33.8907, 'lon': -84.4677, 'roof': 'open'},
    'Oakland,US': {'lat': 37.7516, 'lon': -122.2005, 'roof': 'open'},
    'Tempe,US': {'lat': 33.4255, 'lon': -111.9400, 'roof': 'open'},
    'Mesa,US': {'lat': 33.3978, 'lon': -111.8336, 'roof': 'open'},
    'Scottsdale,US': {'lat': 33.4569, 'lon': -111.9456, 'roof': 'open'},
    'Peoria,US': {'lat': 33.5806, 'lon': -112.2374, 'roof': 'open'},
    'Surprise,US': {'lat': 33.6284, 'lon': -112.3681, 'roof': 'open'},
    'Goodyear,US': {'lat': 33.4350, 'lon': -112.3750, 'roof': 'open'},
    'Fort Myers,US': {'lat': 26.6417, 'lon': -81.8557, 'roof': 'open'},
    'Sarasota,US': {'lat': 27.3364, 'lon': -82.4625, 'roof': 'open'},
    'Bradenton,US': {'lat': 27.5001, 'lon': -82.5748, 'roof': 'open'},
    'Port Charlotte,US': {'lat': 26.9787, 'lon': -82.1087, 'roof': 'open'},
    'Jupiter,US': {'lat': 26.9134, 'lon': -80.1165, 'roof': 'open'},
    'West Palm Beach,US': {'lat': 26.7153, 'lon': -80.0534, 'roof': 'open'},
    'Clearwater,US': {'lat': 27.9659, 'lon': -82.7291, 'roof': 'open'},
    'Tampa,US': {'lat': 27.9711, 'lon': -82.5038, 'roof': 'open'},
    'Dunedin,US': {'lat': 28.0194, 'lon': -82.7693, 'roof': 'open'},
}

LOCATION_TO_VENUE = {
    'Phoenix,US': 'Chase Field',
    'Miami,US': 'loanDepot park',
    'Arlington,US': 'Globe Life Field',
    'Houston,US': 'Minute Maid Park',
    'Seattle,US': 'T-Mobile Park',
    'Milwaukee,US': 'American Family Field',
    'St Petersburg,US': 'Tropicana Field',
    'Toronto,CA': 'Rogers Centre',
    'Anaheim,US': 'Angel Stadium',
    'Los Angeles,US': 'Dodger Stadium',
    'San Francisco,US': 'Oracle Park',
    'San Diego,US': 'Petco Park',
    'Denver,US': 'Coors Field',
    'Kansas City,US': 'Kauffman Stadium',
    'Minneapolis,US': 'Target Field',
    'Chicago,US': 'Guaranteed Rate Field',
    'Cleveland,US': 'Progressive Field',
    'Detroit,US': 'Comerica Park',
    'Cincinnati,US': 'Great American Ball Park',
    'St Louis,US': 'Busch Stadium',
    'Pittsburgh,US': 'PNC Park',
    'New York,US': 'Yankee Stadium',
    'Philadelphia,US': 'Citizens Bank Park',
    'Washington,US': 'Nationals Park',
    'Boston,US': 'Fenway Park',
    'Baltimore,US': 'Oriole Park at Camden Yards',
    'Atlanta,US': 'Truist Park',
    'Tempe,US': 'Tempe Diablo Stadium',
    'Mesa,US': 'Sloan Park',
    'Scottsdale,US': 'Salt River Fields',
    'Peoria,US': 'Peoria Sports Complex',
    'Surprise,US': 'Surprise Stadium',
    'Goodyear,US': 'Goodyear Ballpark',
    'Fort Myers,US': 'Hammond Stadium',
    'Sarasota,US': 'Ed Smith Stadium',
    'Bradenton,US': 'LECOM Park',
    'Port Charlotte,US': 'Charlotte Sports Park',
    'Jupiter,US': 'Roger Dean Chevrolet Stadium',
    'West Palm Beach,US': 'The Ballpark of the Palm Beaches',
    'Clearwater,US': 'Spectrum Field',
    'Tampa,US': 'George M. Steinbrenner Field',
    'Dunedin,US': 'TD Ballpark',
}

SPRING_TRAINING_VENUES = {
    'Tempe Diablo Stadium': 'Tempe,US',
    'Camelback Ranch': 'Phoenix,US',
    'Sloan Park': 'Mesa,US',
    'Salt River Fields': 'Scottsdale,US',
    'Salt River Fields at Talking Stick': 'Scottsdale,US',
    'Peoria Sports Complex': 'Peoria,US',
    'Surprise Stadium': 'Surprise,US',
    'Goodyear Ballpark': 'Goodyear,US',
    'Hohokam Stadium': 'Mesa,US',
    'American Family Fields of Phoenix': 'Phoenix,US',
    'JetBlue Park': 'Fort Myers,US',
    'JetBlue Park at Fenway South': 'Fort Myers,US',
    'Ed Smith Stadium': 'Sarasota,US',
    'LECOM Park': 'Bradenton,US',
    'Charlotte Sports Park': 'Port Charlotte,US',
    'Hammond Stadium': 'Fort Myers,US',
    'Roger Dean Chevrolet Stadium': 'Jupiter,US',
    'Clover Park': 'West Palm Beach,US',
    'The Ballpark of the Palm Beaches': 'West Palm Beach,US',
    'Spectrum Field': 'Clearwater,US',
    'George M. Steinbrenner Field': 'Tampa,US',
    'TD Ballpark': 'Dunedin,US',
}

REGULAR_SEASON_VENUES = {
    'Angel Stadium': 'Anaheim,US',
    'Dodger Stadium': 'Los Angeles,US',
    'UNIQLO Field at Dodger Stadium': 'Los Angeles,US',
    'T-Mobile Park': 'Seattle,US',
    'Globe Life Field': 'Arlington,US',
    'Minute Maid Park': 'Houston,US',
    'Daikin Park': 'Houston,US',
    'Sutter Health Park': 'Oakland,US',
    'Kauffman Stadium': 'Kansas City,US',
    'Target Field': 'Minneapolis,US',
    'Guaranteed Rate Field': 'Chicago,US',
    'Rate Field': 'Chicago,US',
    'Progressive Field': 'Cleveland,US',
    'Comerica Park': 'Detroit,US',
    'Yankee Stadium': 'New York,US',
    'Fenway Park': 'Boston,US',
    'Oriole Park at Camden Yards': 'Baltimore,US',
    'Rogers Centre': 'Toronto,CA',
    'Tropicana Field': 'St Petersburg,US',
    'Oracle Park': 'San Francisco,US',
    'Petco Park': 'San Diego,US',
    'Chase Field': 'Phoenix,US',
    'Coors Field': 'Denver,US',
    'Great American Ball Park': 'Cincinnati,US',
    'Busch Stadium': 'St Louis,US',
    'American Family Field': 'Milwaukee,US',
    'PNC Park': 'Pittsburgh,US',
    'Wrigley Field': 'Chicago,US',
    'Citi Field': 'New York,US',
    'Citizens Bank Park': 'Philadelphia,US',
    'Nationals Park': 'Washington,US',
    'Truist Park': 'Atlanta,US',
    'loanDepot park': 'Miami,US',
    'LoanDepot Park': 'Miami,US',
    'loanDepot Park': 'Miami,US',
    'Loan Depot Park': 'Miami,US',
}

FIXED_DOMES = {
    'Tropicana Field': {'has_roof': True, 'type': 'fixed', 'should_alert': False},
    'Rogers Centre': {'has_roof': True, 'type': 'fixed', 'should_alert': False},
}

RETRACTABLE_ROOFS = {
    'Chase Field': {'has_roof': True, 'type': 'retractable'},
    'loanDepot park': {'has_roof': True, 'type': 'retractable'},
    'LoanDepot Park': {'has_roof': True, 'type': 'retractable'},
    'loanDepot Park': {'has_roof': True, 'type': 'retractable'},
    'Loan Depot Park': {'has_roof': True, 'type': 'retractable'},
    'Globe Life Field': {'has_roof': True, 'type': 'retractable'},
    'Minute Maid Park': {'has_roof': True, 'type': 'retractable'},
    'Daikin Park': {'has_roof': True, 'type': 'retractable'},
    'T-Mobile Park': {'has_roof': True, 'type': 'retractable'},
    'American Family Field': {'has_roof': True, 'type': 'retractable'},
}

TEST_VENUES = {
    'Tropicana Field (Fixed Dome)': {'lat': 27.7683, 'lon': -82.6534},
    'Rogers Centre (Fixed Dome)': {'lat': 43.6414, 'lon': -79.3894},
    'Chase Field': {'lat': 33.4453, 'lon': -112.0667},
    'loanDepot park': {'lat': 25.7781, 'lon': -80.2197},
    'Globe Life Field': {'lat': 32.7512, 'lon': -97.0832},
    'Minute Maid Park': {'lat': 29.7573, 'lon': -95.3555},
    'T-Mobile Park': {'lat': 47.5914, 'lon': -122.3325},
    'American Family Field': {'lat': 43.0280, 'lon': -87.9712},
    'Angel Stadium': {'lat': 33.8003, 'lon': -117.8827},
    'Dodger Stadium': {'lat': 34.0739, 'lon': -118.2400},
    'Oracle Park': {'lat': 37.7786, 'lon': -122.3893},
    'Petco Park': {'lat': 32.7076, 'lon': -117.1570},
    'Coors Field': {'lat': 39.7559, 'lon': -104.9942},
    'Kauffman Stadium': {'lat': 39.0517, 'lon': -94.4803},
    'Target Field': {'lat': 44.9817, 'lon': -93.2776},
    'Guaranteed Rate Field': {'lat': 41.8299, 'lon': -87.6338},
    'Progressive Field': {'lat': 41.4962, 'lon': -81.6852},
    'Comerica Park': {'lat': 42.3390, 'lon': -83.0485},
    'Great American Ball Park': {'lat': 39.0979, 'lon': -84.5082},
    'Busch Stadium': {'lat': 38.6226, 'lon': -90.1928},
    'PNC Park': {'lat': 40.4469, 'lon': -80.0057},
    'Wrigley Field': {'lat': 41.9484, 'lon': -87.6553},
    'Yankee Stadium': {'lat': 40.8296, 'lon': -73.9262},
    'Citi Field': {'lat': 40.7571, 'lon': -73.8458},
    'Citizens Bank Park': {'lat': 39.9061, 'lon': -75.1665},
    'Nationals Park': {'lat': 38.8730, 'lon': -77.0074},
    'Fenway Park': {'lat': 42.3467, 'lon': -71.0972},
    'Oriole Park at Camden Yards': {'lat': 39.2838, 'lon': -76.6216},
    'Truist Park': {'lat': 33.8907, 'lon': -84.4677},
    'Sutter Health Park (Athletics)': {'lat': 37.7516, 'lon': -122.2005},
    'Tempe Diablo Stadium': {'lat': 33.4255, 'lon': -111.9400},
    'Camelback Ranch': {'lat': 33.5053, 'lon': -112.1911},
    'Sloan Park': {'lat': 33.3978, 'lon': -111.8336},
    'Salt River Fields': {'lat': 33.4569, 'lon': -111.9456},
    'Peoria Sports Complex': {'lat': 33.5806, 'lon': -112.2374},
    'Surprise Stadium': {'lat': 33.6284, 'lon': -112.3681},
    'Goodyear Ballpark': {'lat': 33.4350, 'lon': -112.3750},
    'American Family Fields of Phoenix': {'lat': 33.4797, 'lon': -112.1347},
    'JetBlue Park': {'lat': 26.6417, 'lon': -81.8557},
    'Ed Smith Stadium': {'lat': 27.3364, 'lon': -82.4625},
    'LECOM Park': {'lat': 27.5001, 'lon': -82.5748},
    'Charlotte Sports Park': {'lat': 26.9787, 'lon': -82.1087},
    'Hammond Stadium': {'lat': 26.6417, 'lon': -81.8557},
    'Roger Dean Chevrolet Stadium': {'lat': 26.9134, 'lon': -80.1165},
    'Clover Park': {'lat': 27.2719, 'lon': -80.3865},
    'The Ballpark of the Palm Beaches': {'lat': 26.7153, 'lon': -80.0534},
    'Spectrum Field': {'lat': 27.9659, 'lon': -82.7291},
    'George M. Steinbrenner Field': {'lat': 27.9711, 'lon': -82.5038},
    'TD Ballpark': {'lat': 28.0194, 'lon': -82.7693},
}


def get_venue_name_from_location(location):
    return LOCATION_TO_VENUE.get(location, 'Unknown Venue')


def get_venue_roof_info(venue_name):
    if venue_name in FIXED_DOMES:
        return FIXED_DOMES[venue_name]
    if venue_name in RETRACTABLE_ROOFS:
        return {**RETRACTABLE_ROOFS[venue_name], 'should_alert': None}
    return {'has_roof': False, 'type': 'open', 'should_alert': True}


def get_venue_roof_type(venue_name):
    roof_info = get_venue_roof_info(venue_name)
    if roof_info['type'] == 'fixed':
        return {'type': 'fixed_dome', 'description': '🏟️ Fixed Dome'}
    if roof_info['type'] == 'retractable':
        return {'type': 'retractable', 'description': '🔄 Retractable Roof'}
    return {'type': 'open_air', 'description': '☀️ Open Air'}


def get_venue_location(venue_name):
    if venue_name in SPRING_TRAINING_VENUES:
        return SPRING_TRAINING_VENUES[venue_name]
    if venue_name in REGULAR_SEASON_VENUES:
        return REGULAR_SEASON_VENUES[venue_name]

    print(f"⚠️  WARNING: Unknown venue '{venue_name}' — defaulting to Phoenix,US")
    print("   👉 Add venue mapping to venues.py")
    return 'Phoenix,US'


def iter_test_venues():
    return TEST_VENUES.items()
