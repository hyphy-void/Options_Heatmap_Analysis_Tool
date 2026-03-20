from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Optional


class OptionsDataError(RuntimeError):
    """Raised when option data cannot be fetched or normalized."""


def get_finnhub_api_key() -> str:
    api_key = os.getenv("FINNHUB_API_KEY", "").strip()
    if not api_key:
        raise OptionsDataError("FINNHUB_API_KEY is not configured")
    return api_key


def create_finnhub_client(api_key: Optional[str] = None):
    try:
        import finnhub
    except ImportError as exc:
        raise OptionsDataError("finnhub-python is not installed. Run `uv sync` first.") from exc

    return finnhub.Client(api_key=api_key or get_finnhub_api_key())


def fetch_option_snapshot(
    symbol: str,
    max_expiration_dates: Optional[int] = None,
    multiple_expirations: bool = False,
    client=None,
) -> Dict[str, Any]:
    normalized_symbol = symbol.upper()
    finnhub_client = client or create_finnhub_client()

    option_chain = _call_finnhub(
        lambda: finnhub_client.option_chain(symbol=normalized_symbol),
        symbol=normalized_symbol,
        action="option chain",
    )
    normalized_options = normalize_option_records(normalized_symbol, option_chain)
    expiration_dates = select_expiration_dates(
        normalized_options,
        multiple_expirations=multiple_expirations,
        max_expiration_dates=max_expiration_dates,
    )
    filtered_options = [
        option for option in normalized_options if option["expiration_date"] in expiration_dates
    ]
    if not filtered_options:
        raise OptionsDataError(f"No option contracts remain after filtering for {normalized_symbol}")

    quote = _call_finnhub(
        lambda: finnhub_client.quote(normalized_symbol),
        symbol=normalized_symbol,
        action="quote",
    )
    profile = _call_finnhub(
        lambda: finnhub_client.company_profile2(symbol=normalized_symbol),
        symbol=normalized_symbol,
        action="company profile",
    )

    return {
        "symbol": normalized_symbol,
        "company_name": _extract_company_name(profile, normalized_symbol),
        "current_price": _extract_current_price(quote),
        "expiration_dates": expiration_dates,
        "options_data": filtered_options,
        "data_source": "finnhub",
        "implied_volatility_unit": "percent",
    }


def normalize_option_records(symbol: str, payload: Any) -> List[Dict[str, Any]]:
    records = _extract_option_records(payload)
    normalized_records: List[Dict[str, Any]] = []

    for record in records:
        normalized = _normalize_option_record(symbol, record)
        if normalized is not None:
            normalized_records.append(normalized)

    if not normalized_records:
        raise OptionsDataError(f"No option data found for {symbol}")

    return normalized_records


def select_expiration_dates(
    options_data: Iterable[Dict[str, Any]],
    multiple_expirations: bool = False,
    max_expiration_dates: Optional[int] = None,
) -> List[str]:
    expiration_dates = sorted({option["expiration_date"] for option in options_data})
    if not expiration_dates:
        return []

    if not multiple_expirations:
        return [expiration_dates[0]]

    if max_expiration_dates in (None, 0):
        return expiration_dates

    return expiration_dates[: max(1, max_expiration_dates)]


def _call_finnhub(fetcher, symbol: str, action: str):
    try:
        return fetcher()
    except Exception as exc:  # pragma: no cover - shape depends on SDK/runtime
        raise OptionsDataError(_format_finnhub_error(exc, symbol=symbol, action=action)) from exc


def _format_finnhub_error(exc: Exception, symbol: str, action: str) -> str:
    raw_message = str(exc).strip() or exc.__class__.__name__
    normalized = raw_message.lower()
    action_label = action.replace(" ", "-")

    if "<!doctype html" in normalized or "<html" in normalized:
        return (
            f"Finnhub returned an HTML error page while fetching {action} for {symbol}. "
            "Check API entitlement and endpoint availability."
        )
    if "failed to resolve" in normalized or "name resolution" in normalized or "nodename nor servname provided" in normalized:
        return f"Could not reach Finnhub while fetching {action} for {symbol}. Check local DNS/network access."
    if "401" in normalized or "unauthorized" in normalized:
        return f"Finnhub rejected the request for {symbol} with 401 Unauthorized"
    if "403" in normalized or "forbidden" in normalized:
        if action == "option chain" or "don't have access to this resource" in normalized:
            return f"Finnhub {action_label} endpoint forbidden for {symbol}; likely plan/entitlement issue (403 Forbidden)"
        return f"Finnhub rejected the request for {symbol} with 403 Forbidden"
    if "429" in normalized or "rate limit" in normalized or "too many requests" in normalized:
        return f"Finnhub rate limit reached while fetching {action} for {symbol}"
    if "not found" in normalized or "404" in normalized:
        return f"Finnhub could not find {action} data for {symbol}"

    return f"Finnhub request failed while fetching {action} for {symbol}: {raw_message}"


def _extract_option_records(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]

    if isinstance(payload, dict):
        if "error" in payload:
            raise OptionsDataError(str(payload["error"]))
        if payload.get("code") and payload.get("message"):
            raise OptionsDataError(f"{payload['code']}: {payload['message']}")
        if "s" in payload and payload.get("s") == "no_data":
            raise OptionsDataError("Finnhub returned no option data")

        for key in ("data", "optionChain", "options", "results"):
            records = payload.get(key)
            if isinstance(records, list):
                return [record for record in records if isinstance(record, dict)]

        if "contractName" in payload:
            return [payload]

    raise OptionsDataError("Finnhub returned an unexpected option chain payload")


def _normalize_option_record(symbol: str, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    option_type = _normalize_option_type(record.get("type"))
    expiration_date = str(record.get("expirationDate") or "").strip()
    strike_price = _to_float(record.get("strike"))

    if option_type is None or not expiration_date or strike_price is None:
        return None

    contract_name = str(record.get("contractName") or "").strip()
    if not contract_name:
        contract_name = _build_contract_name(symbol, expiration_date, option_type, strike_price)

    return {
        "type": option_type,
        "contract_name": contract_name,
        "expiration_date": expiration_date,
        "strike_price": strike_price,
        "last_price": _to_float(record.get("lastPrice"), default=0.0),
        "bid": _to_float(record.get("bid"), default=0.0),
        "ask": _to_float(record.get("ask"), default=0.0),
        "volume": _to_int(record.get("volume"), default=0),
        "open_interest": _to_int(record.get("openInterest"), default=0),
        "implied_volatility": _normalize_iv(record.get("impliedVolatility")),
    }


def _extract_company_name(profile: Any, symbol: str) -> str:
    if isinstance(profile, dict):
        return str(profile.get("name") or profile.get("ticker") or symbol)
    return symbol


def _extract_current_price(quote: Any) -> float:
    if isinstance(quote, dict):
        current_price = _to_float(quote.get("c"))
        if current_price is not None:
            return current_price
    return 0.0


def _normalize_option_type(value: Any) -> Optional[str]:
    normalized_value = str(value or "").strip().upper()
    if normalized_value == "CALL":
        return "Call"
    if normalized_value == "PUT":
        return "Put"
    return None


def _normalize_iv(value: Any) -> float:
    iv = _to_float(value, default=0.0)
    if iv is None:
        return 0.0

    return round(iv * 100, 4)


def _build_contract_name(symbol: str, expiration_date: str, option_type: str, strike_price: float) -> str:
    option_code = "C" if option_type == "Call" else "P"
    return f"{symbol}{expiration_date.replace('-', '')}{option_code}{int(strike_price * 1000):08d}"


def _to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value in (None, "", "None"):
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    numeric_value = _to_float(value)
    if numeric_value is None:
        return default
    return int(numeric_value)
