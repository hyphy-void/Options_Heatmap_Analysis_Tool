# Options Heatmap Analysis Tool

Language / 语言: [简体中文](./README.md) | English

[![Python](https://img.shields.io/badge/Python-3.9-blue.svg)](./.python-version)
[![Flask](https://img.shields.io/badge/Flask-2.3-black.svg)](https://flask.palletsprojects.com/)
[![uv](https://img.shields.io/badge/uv-managed-6f42c1.svg)](https://docs.astral.sh/uv/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

A portfolio-ready options analytics web app built with [Flask](https://flask.palletsprojects.com/) and powered by [Finnhub](https://finnhub.io/docs/api). It turns raw option-chain snapshots into analyst-friendly heatmaps, summary statistics, and a lightweight API that can be demoed locally in minutes.

## Table of Contents

- [Highlights](#highlights)
- [Screenshots](#screenshots)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [FAQ](#faq)
- [Development and Testing](#development-and-testing)
- [Project Structure](#project-structure)

## Highlights

- End-to-end workflow from option-chain ingestion to normalized snapshots, summary metrics, and rendered heatmaps
- Official [`finnhub-python`](https://github.com/Finnhub-Stock-API/finnhub-python) client integration for quotes, company profiles, and option-chain data
- Three visualization modes for fast market inspection:
  - `Direction × Open Interest`
  - `Volume`
  - `Implied Volatility`
- Heatmaps include a current-price reference line and data timestamp for better market context
- Local JSON / CSV snapshot generation for reproducibility, debugging, and follow-up analysis
- Lightweight Flask UI plus API endpoints, making the project easy to demo, extend, or integrate
- Explicit error handling for permission issues, empty responses, and transient upstream failures
- Tests covering provider normalization, persistence, API behavior, and heatmap generation

## Screenshots

### Dashboard

![Panel](assets/panel.jpg)

### Heatmap Example

![Heatmap](assets/heatmap2.jpg)

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/hyphy-void/Options_Heatmap_Analysis_Tool
cd Options_Heatmap_Analysis_Tool
```

### 2. Configure your API key

```bash
export FINNHUB_API_KEY="your_finnhub_key"
```

### 3. Install dependencies

```bash
uv sync
```

### 4. Start the app

```bash
uv run python app.py
```

If port `5000` is already in use:

```bash
PORT=5001 uv run python app.py
```

Then open:

- Default: [http://localhost:5000](http://localhost:5000)
- Custom port example: [http://localhost:5001](http://localhost:5001)

## Configuration

### Required environment variable

| Variable | Required | Description |
| --- | --- | --- |
| `FINNHUB_API_KEY` | Yes | Finnhub API key |

### Optional environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `PORT` | `5000` | Flask server port |
| `HOST` | `0.0.0.0` | Flask bind host |
| `FLASK_DEBUG` | `true` | Enable debug mode |

## Usage

### Web workflow

1. Start the Flask server.
2. Open the dashboard in your browser.
3. Enter a stock symbol such as `AAPL` or `TSLA`.
4. Choose how many recent expirations to fetch.
5. Load the data and switch between the available heatmap views.

### CLI data fetch

Fetch option data for a symbol and a limited number of expirations:

```bash
uv run python utils_option.py fetch AAPL 4
```

This generates the following files under `data/`:

- `{SYMBOL}_options_data.json`
- `{SYMBOL}_options_data.csv`

## API Endpoints

### `GET /`

Returns the main web page.

### `POST /api/load_data`

Fetches, normalizes, and loads option data for a symbol.

Example payload:

```json
{
  "symbol": "AAPL",
  "max_expirations": 4
}
```

### `POST /api/generate_heatmap`

Generates a heatmap from the currently loaded dataset.

Supported `chart_type` values:

- `direction_oi`
- `volume`
- `iv`

### `GET /api/available_symbols`

Returns locally cached symbols.

### `GET /health`

Returns a simple health-check response.

## FAQ

### 1. `Port 5000 is in use`

Another process is already using port `5000`. Start the app on a different port:

```bash
PORT=5001 uv run python app.py
```

### 2. `FINNHUB_API_KEY is not configured`

Your current shell session does not have the API key configured yet:

```bash
export FINNHUB_API_KEY="your_finnhub_key"
```

### 3. `Finnhub option-chain endpoint forbidden ...`

If:

- `quote('AAPL')` works
- `company_profile2('AAPL')` works
- `option_chain('AAPL')` returns `403`

the most likely cause is that your Finnhub plan does not include access to the `option-chain` endpoint.

### 4. The page shows an HTML error response or a network failure

Common reasons:

- Temporary Finnhub endpoint issues
- Local DNS or network access problems
- API key entitlement limitations

## Development and Testing

Run the test suite with:

```bash
uv run pytest -q
```

Development conventions:

- `uv` is the default dependency manager
- `finnhub_provider.py` owns data retrieval and normalization
- the Flask layer stays intentionally lightweight
- local snapshots are used for both rendering and troubleshooting

## Project Structure

```text
Options_Heatmap_Analysis_Tool/
├── app.py                  # Flask web service
├── finnhub_provider.py     # Finnhub integration and error handling
├── utils_option.py         # Normalization, persistence, and heatmap helpers
├── templates/
│   └── index.html          # Frontend page
├── assets/                 # README preview images
├── tests/                  # Test suite
├── pyproject.toml          # Project metadata and dependencies
├── uv.lock                 # uv lockfile
└── LICENSE
```

## License

Released under the [MIT License](./LICENSE).
