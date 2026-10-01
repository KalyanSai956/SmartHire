from backend.services.jobs.location_normalizer import (
    normalize_location,
    is_india_location,
)


def test_bangalore_is_normalized():
    result = normalize_location(
        "Bangalore, Karnataka, India"
    )

    assert result.is_india is True
    assert result.is_valid is True
    assert result.city == "Bengaluru"
    assert result.region == "Karnataka"
    assert result.country == "India"


def test_bengaluru_is_normalized():
    result = normalize_location(
        "Bengaluru, India"
    )

    assert result.is_india is True
    assert result.city == "Bengaluru"
    assert result.region == "Karnataka"


def test_hyderabad_is_normalized():
    result = normalize_location(
        "Hyderabad, Telangana, India"
    )

    assert result.is_india is True
    assert result.city == "Hyderabad"
    assert result.region == "Telangana"


def test_pune_is_normalized():
    result = normalize_location(
        "Pune, Maharashtra"
    )

    assert result.is_india is True
    assert result.city == "Pune"
    assert result.region == "Maharashtra"


def test_remote_india():
    result = normalize_location(
        "Remote - India"
    )

    assert result.is_india is True
    assert result.is_remote is True
    assert result.country == "India"
    assert result.display == "Remote — India"


def test_remote_india_with_remote_type():
    result = normalize_location(
        "India",
        remote_type="remote",
    )

    assert result.is_india is True
    assert result.is_remote is True


def test_tirupati():
    result = normalize_location(
        "Tirupati, Andhra Pradesh, India"
    )

    assert result.is_india is True
    assert result.city == "Tirupati"
    assert result.region == "Andhra Pradesh"


def test_united_states_is_rejected():
    result = normalize_location(
        "United States"
    )

    assert result.is_india is False
    assert result.is_valid is False


def test_united_kingdom_is_rejected():
    result = normalize_location(
        "London, United Kingdom"
    )

    assert result.is_india is False
    assert result.is_valid is False


def test_united_nations_is_rejected():
    result = normalize_location(
        "United Nations"
    )

    assert result.is_india is False
    assert result.is_valid is False


def test_unknown_location_is_rejected():
    result = normalize_location(
        "Some Random Place"
    )

    assert result.is_india is False
    assert result.is_valid is False


def test_india_only():
    result = normalize_location(
        "India"
    )

    assert result.is_india is True
    assert result.is_valid is True
    assert result.country == "India"
    assert result.city is None


def test_india_helper():
    assert is_india_location(
        "Bangalore, India"
    ) is True

    assert is_india_location(
        "New York, USA"
    ) is False