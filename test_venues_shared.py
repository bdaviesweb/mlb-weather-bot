import unittest

from venues import (
    RETRACTABLE_ROOFS,
    STADIUM_COORDINATES,
    get_venue_location,
    get_venue_name_from_location,
    get_venue_roof_info,
    get_venue_roof_type,
    iter_test_venues,
)


class SharedVenueTests(unittest.TestCase):
    def test_regular_season_aliases_map_to_expected_locations(self):
        self.assertEqual(get_venue_location("Rate Field"), "Chicago,US")
        self.assertEqual(get_venue_location("Loan Depot Park"), "Miami,US")
        self.assertEqual(get_venue_location("UNIQLO Field at Dodger Stadium"), "Los Angeles,US")
        self.assertEqual(get_venue_location("Sutter Health Park"), "Oakland,US")
        self.assertEqual(get_venue_location("Daikin Park"), "Houston,US")

    def test_location_to_venue_name_matches_weather_alert_expectations(self):
        self.assertEqual(get_venue_name_from_location("Chicago,US"), "Guaranteed Rate Field")
        self.assertEqual(get_venue_name_from_location("Miami,US"), "loanDepot park")
        self.assertEqual(get_venue_name_from_location("Toronto,CA"), "Rogers Centre")
        self.assertEqual(get_venue_name_from_location("Unknown,US"), "Unknown Venue")

    def test_roof_helpers_preserve_existing_shapes(self):
        self.assertEqual(
            get_venue_roof_info("Rogers Centre"),
            {"has_roof": True, "type": "fixed", "should_alert": False},
        )
        self.assertEqual(
            get_venue_roof_info("Chase Field"),
            {"has_roof": True, "type": "retractable", "should_alert": None},
        )
        self.assertEqual(
            get_venue_roof_info("Daikin Park"),
            {"has_roof": True, "type": "retractable", "should_alert": None},
        )
        self.assertEqual(
            get_venue_roof_type("Chase Field"),
            {"type": "retractable", "description": "🔄 Retractable Roof"},
        )

    def test_retractable_roof_aliases_include_current_names(self):
        self.assertIn("Daikin Park", RETRACTABLE_ROOFS)
        self.assertIn("LoanDepot Park", RETRACTABLE_ROOFS)

    def test_test_venue_coordinates_cover_stadium_coordinates(self):
        test_venue_coords = {
            (venue["lat"], venue["lon"])
            for _, venue in iter_test_venues()
        }

        for location, coords in STADIUM_COORDINATES.items():
            with self.subTest(location=location):
                self.assertIn((coords["lat"], coords["lon"]), test_venue_coords)


if __name__ == "__main__":
    unittest.main()
