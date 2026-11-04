import pytest

from src.ingestion.acs import build_acs_tract_url, parse_acs_response


def test_build_acs_tract_url_for_dallas():
    url, params = build_acs_tract_url("113", api_key="test-key")

    assert url.endswith("/2024/acs/acs5")
    assert params["for"] == "tract:*"
    assert params["in"] == "state:48 county:113"
    assert params["key"] == "test-key"
    assert "B01003_001E" in params["get"]


def test_build_acs_tract_url_rejects_unknown_county():
    with pytest.raises(ValueError, match="Unsupported county"):
        build_acs_tract_url("999")


def test_parse_acs_response_creates_geoid():
    payload = [
        [
            "NAME",
            "B01003_001E",
            "B05002_013E",
            "B17001_002E",
            "B08201_002E",
            "B25003_003E",
            "state",
            "county",
            "tract",
        ],
        [
            "Census Tract 1; Dallas County; Texas",
            "1000",
            "200",
            "100",
            "50",
            "300",
            "48",
            "113",
            "000100",
        ],
    ]

    frame = parse_acs_response(payload, "113", year=2023)

    assert frame.loc[0, "geoid"] == "48113000100"
    assert frame.loc[0, "county_name"] == "Dallas"
    assert frame.loc[0, "population"] == 1000
    assert frame.loc[0, "foreign_born_population"] == 200
    assert frame.loc[0, "acs_year"] == 2023


class FakeResponse:
    def __init__(self, text, content_type="text/html", status_code=200):
        self.text = text
        self.headers = {"content-type": content_type}
        self.status_code = status_code

    def raise_for_status(self):
        return None

    def json(self):
        raise AssertionError("json() should not be called for non-JSON responses")


def test_fetch_acs_reports_invalid_key(monkeypatch):
    from src.ingestion import acs

    monkeypatch.setattr(
        acs.requests,
        "get",
        lambda *args, **kwargs: FakeResponse("<html><h1>Invalid Key</h1></html>"),
    )

    with pytest.raises(RuntimeError, match="activated"):
        acs.fetch_acs_tracts("113", api_key="bad-key")
