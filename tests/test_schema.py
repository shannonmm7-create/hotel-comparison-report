import copy

from hotel_report.schema import validation_errors


def test_example_is_valid(example_data):
    assert validation_errors(example_data) == []


def test_missing_required_top_level_field(example_data):
    data = copy.deepcopy(example_data)
    del data["venue_name"]
    errors = validation_errors(data)
    assert any("venue_name" in e for e in errors)


def test_hotels_cannot_be_empty(example_data):
    data = copy.deepcopy(example_data)
    data["hotels"] = []
    assert validation_errors(data)


def test_room_requires_rates(example_data):
    data = copy.deepcopy(example_data)
    del data["hotels"][0]["rooms"][0]["offered_rate"]
    errors = validation_errors(data)
    assert any("offered_rate" in e for e in errors)


def test_unknown_field_is_rejected(example_data):
    data = copy.deepcopy(example_data)
    data["hotels"][0]["surprise"] = "nope"
    assert validation_errors(data)


def test_rate_may_be_number_or_string(example_data):
    data = copy.deepcopy(example_data)
    data["hotels"][0]["rooms"][0]["offered_rate"] = "Waived"
    assert validation_errors(data) == []


def test_empty_visible_scalars_rejected(example_data):
    for field in ("cutoff", "distance_from_venue"):
        data = copy.deepcopy(example_data)
        data["hotels"][0][field] = ""
        assert validation_errors(data), field
    data = copy.deepcopy(example_data)
    data["hotels"][0]["tripadvisor"]["text"] = ""
    assert validation_errors(data)


def test_numeric_distance_still_valid(example_data):
    data = copy.deepcopy(example_data)
    data["hotels"][0]["distance_from_venue"] = 8
    assert validation_errors(data) == []
