from finnhub_provider import OptionsDataError, fetch_option_snapshot, normalize_option_records


class FakeFinnhubClient:
    def __init__(self, option_chain_payload):
        self._option_chain_payload = option_chain_payload

    def option_chain(self, symbol):
        return self._option_chain_payload

    def quote(self, symbol):
        return {"c": 123.45}

    def company_profile2(self, symbol):
        return {"name": "Example Corp"}


def sample_option_chain():
    return [
        {
            "contractName": "AAPL250321C00175000",
            "type": "CALL",
            "expirationDate": "2025-03-21",
            "strike": 175,
            "lastPrice": 3.1,
            "bid": 3.0,
            "ask": 3.2,
            "volume": 150,
            "openInterest": 220,
            "impliedVolatility": 1.2502,
        },
        {
            "contractName": "AAPL250321P00170000",
            "type": "PUT",
            "expirationDate": "2025-03-21",
            "strike": 170,
            "lastPrice": 2.5,
            "bid": 2.4,
            "ask": 2.6,
            "volume": None,
            "openInterest": None,
            "impliedVolatility": None,
        },
        {
            "contractName": "AAPL250328C00180000",
            "type": "CALL",
            "expirationDate": "2025-03-28",
            "strike": 180,
            "lastPrice": 1.4,
            "bid": 1.3,
            "ask": 1.5,
            "volume": 80,
            "openInterest": 120,
            "impliedVolatility": 0.5123,
        },
        {
            "contractName": "DIRTY",
            "type": "CALL",
            "expirationDate": "",
            "strike": None,
        },
    ]


def test_normalize_option_records_maps_fields_and_iv():
    normalized = normalize_option_records("AAPL", sample_option_chain())

    assert len(normalized) == 3
    assert normalized[0]["type"] == "Call"
    assert normalized[0]["contract_name"] == "AAPL250321C00175000"
    assert normalized[0]["expiration_date"] == "2025-03-21"
    assert normalized[0]["strike_price"] == 175.0
    assert normalized[0]["implied_volatility"] == 125.02
    assert normalized[1]["type"] == "Put"
    assert normalized[1]["volume"] == 0
    assert normalized[1]["open_interest"] == 0
    assert normalized[1]["implied_volatility"] == 0.0


def test_fetch_option_snapshot_filters_recent_expirations():
    snapshot = fetch_option_snapshot(
        "aapl",
        max_expiration_dates=1,
        multiple_expirations=True,
        client=FakeFinnhubClient(sample_option_chain()),
    )

    assert snapshot["symbol"] == "AAPL"
    assert snapshot["company_name"] == "Example Corp"
    assert snapshot["current_price"] == 123.45
    assert snapshot["expiration_dates"] == ["2025-03-21"]
    assert len(snapshot["options_data"]) == 2
    assert snapshot["data_source"] == "finnhub"
    assert snapshot["implied_volatility_unit"] == "percent"


def test_fetch_option_snapshot_raises_for_empty_chain():
    client = FakeFinnhubClient([])

    try:
        fetch_option_snapshot("AAPL", multiple_expirations=True, client=client)
    except OptionsDataError as exc:
        assert "No option data found" in str(exc)
    else:
        raise AssertionError("Expected OptionsDataError for empty option chain")
