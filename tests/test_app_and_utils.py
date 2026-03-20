import base64
import json

import pytest

import app as web_app
import utils_option
from finnhub_provider import OptionsDataError


def sample_payload():
    return {
        "symbol": "AAPL",
        "company_name": "Example Corp",
        "current_price": 123.45,
        "expiration_dates": ["2025-03-21", "2025-03-28"],
        "fetch_start_time": "2025-03-01T10:00:00",
        "fetch_end_time": "2025-03-01T10:00:02",
        "fetch_duration_seconds": 2.0,
        "data_timestamp": "2025-03-01T10:00:02",
        "total_options": 3,
        "calls_count": 2,
        "puts_count": 1,
        "data_source": "finnhub",
        "implied_volatility_unit": "percent",
        "options_data": [
            {
                "type": "Call",
                "contract_name": "AAPL250321C00175000",
                "expiration_date": "2025-03-21",
                "strike_price": 175.0,
                "last_price": 3.1,
                "bid": 3.0,
                "ask": 3.2,
                "volume": 150,
                "open_interest": 220,
                "implied_volatility": 125.02,
            },
            {
                "type": "Put",
                "contract_name": "AAPL250321P00170000",
                "expiration_date": "2025-03-21",
                "strike_price": 170.0,
                "last_price": 2.5,
                "bid": 2.4,
                "ask": 2.6,
                "volume": 90,
                "open_interest": 140,
                "implied_volatility": 88.1,
            },
            {
                "type": "Call",
                "contract_name": "AAPL250328C00180000",
                "expiration_date": "2025-03-28",
                "strike_price": 180.0,
                "last_price": 1.4,
                "bid": 1.3,
                "ask": 1.5,
                "volume": 80,
                "open_interest": 120,
                "implied_volatility": 51.23,
            },
        ],
    }


class FakeFinnhubClient:
    def __init__(self, option_chain_payload):
        self._option_chain_payload = option_chain_payload

    def option_chain(self, symbol):
        return self._option_chain_payload

    def quote(self, symbol):
        return {"c": 123.45}

    def company_profile2(self, symbol):
        return {"name": "Example Corp"}


def test_fetch_options_data_writes_json_and_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(utils_option, "DATA_DIR", str(tmp_path))
    option_chain = [
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
        }
    ]

    payload = utils_option.fetch_options_data(
        "AAPL",
        multiple_expirations=True,
        max_expiration_dates=None,
        client=FakeFinnhubClient(option_chain),
    )

    json_path = tmp_path / "AAPL_options_data.json"
    csv_path = tmp_path / "AAPL_options_data.csv"
    assert json_path.exists()
    assert csv_path.exists()
    assert payload["data_source"] == "finnhub"

    saved_payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert saved_payload["options_data"][0]["implied_volatility"] == 125.02


def test_fetch_options_data_does_not_write_files_on_empty_chain(tmp_path, monkeypatch):
    monkeypatch.setattr(utils_option, "DATA_DIR", str(tmp_path))

    with pytest.raises(OptionsDataError):
        utils_option.fetch_options_data(
            "AAPL",
            multiple_expirations=True,
            client=FakeFinnhubClient([]),
        )

    assert not (tmp_path / "AAPL_options_data.json").exists()
    assert not (tmp_path / "AAPL_options_data.csv").exists()


def test_create_heatmap_data_and_generate_heatmap_image(tmp_path, monkeypatch):
    payload = sample_payload()
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "AAPL_options_data.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(web_app, "__file__", str(tmp_path / "app.py"))

    df = utils_option.create_heatmap_data(payload)

    assert df is not None
    assert df["implied_volatility"].max() == 125.02

    image_base64 = web_app.generate_heatmap_image(df, "AAPL", "iv")
    assert image_base64 is not None
    assert len(base64.b64decode(image_base64)) > 0


def test_api_load_data_success(monkeypatch):
    monkeypatch.setattr(web_app, "refresh_options_data_web", lambda symbol, max_expirations=None: sample_payload())
    client = web_app.app.test_client()

    response = client.post("/api/load_data", json={"symbol": "AAPL", "max_expirations": 2})
    body = response.get_json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["company_name"] == "Example Corp"
    assert body["statistics"]["total_options"] == 3


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("FINNHUB_API_KEY is not configured", "FINNHUB_API_KEY is not configured"),
        (
            "Finnhub returned an HTML error page while fetching option chain for AAPL. Check API entitlement and endpoint availability.",
            "HTML error page",
        ),
        ("No option data found for AAPL", "No option data found"),
    ],
)
def test_api_load_data_surfaces_finnhub_errors(monkeypatch, message, expected):
    def raise_error(symbol, max_expirations=None):
        raise OptionsDataError(message)

    monkeypatch.setattr(web_app, "refresh_options_data_web", raise_error)
    client = web_app.app.test_client()

    response = client.post("/api/load_data", json={"symbol": "AAPL"})
    body = response.get_json()

    assert response.status_code == 200
    assert body["success"] is False
    assert expected in body["message"]
