# Options Heatmap Analysis Tool

[English](#english) | [中文](#目录)

[![Python](https://img.shields.io/badge/Python-3.9-blue.svg)](./.python-version)
[![Flask](https://img.shields.io/badge/Flask-2.3-black.svg)](https://flask.palletsprojects.com/)
[![uv](https://img.shields.io/badge/uv-managed-6f42c1.svg)](https://docs.astral.sh/uv/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

一个面向量化研究与交易可视化展示的期权热力图项目：基于 Flask 构建 Web 界面，使用 [Finnhub](https://finnhub.io/docs/api) 获取市场数据，并将期权链标准化为可复用的本地快照，再生成多维热力图用于快速研判市场结构。

这个项目覆盖了一个完整的小型数据产品链路：数据接入、清洗标准化、缓存落盘、图表生成、错误处理、测试补齐，以及面向 GitHub 开源展示的工程化交付。

## 目录

- [项目亮点](#项目亮点)
- [界面预览](#界面预览)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [使用方式](#使用方式)
- [GitHub Dependents 识别](#github-dependents-识别)
- [API 接口](#api-接口)
- [常见问题](#常见问题)
- [开发与测试](#开发与测试)
- [项目结构](#项目结构)
- [English](#english)

## 项目亮点

- 使用官方 [`finnhub-python`](https://github.com/Finnhub-Stock-API/finnhub-python) 客户端获取期权链、现价和公司资料
- 构建了从第三方金融 API 到本地标准化快照再到可视化前端的完整链路
- 支持三种核心分析视图：
  - `Direction × Open Interest`
  - `Volume`
  - `Implied Volatility`
- 默认使用 `uv` 管理环境和依赖，保持现代化且轻量的 Python 工作流
- 保持简单直接的 Flask Web 界面，适合快速分析、演示和二次开发
- 失败时返回明确错误，不静默回退到其他数据源，便于排查权限和网络问题

## 界面预览

### 主界面

![Panel](assets/panel.jpg)

### 热力图示例

![Heatmap](assets/heatmap2.jpg)

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd Options_Heatmap_Analysis_Tool
```

### 2. 配置 API Key

```bash
export FINNHUB_API_KEY="your_finnhub_key"
```

### 3. 安装依赖

```bash
uv sync
```

说明：

- `uv` 是本项目唯一推荐的安装与运行方式
- 根目录中的 `requirements.txt` 仅用于 GitHub Dependency Graph / Dependents 识别
- 不建议使用 `pip install -r requirements.txt` 作为日常开发工作流

### 4. 启动服务

```bash
uv run python app.py
```

如果 `5000` 端口已被占用：

```bash
PORT=5001 uv run python app.py
```

启动后访问：

- 默认地址：[http://localhost:5000](http://localhost:5000)
- 自定义端口示例：[http://localhost:5001](http://localhost:5001)

## 配置说明

### 必需环境变量

| 变量名 | 必需 | 说明 |
| --- | --- | --- |
| `FINNHUB_API_KEY` | 是 | Finnhub API Key |

### 可选环境变量

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `PORT` | `5000` | Flask 启动端口 |
| `HOST` | `0.0.0.0` | Flask 监听地址 |
| `FLASK_DEBUG` | `true` | 是否启用调试模式 |

## 使用方式

### Web 界面

1. 启动 Flask 服务
2. 打开浏览器进入首页
3. 输入股票代码，例如 `AAPL`、`TSLA`
4. 选择抓取最近 N 个到期日的数据
5. 点击加载数据并生成热力图

### 命令行获取数据

获取指定股票最近几个到期日的期权数据：

```bash
uv run python utils_option.py fetch AAPL 4
```

执行后会在 `data/` 目录生成：

- `{SYMBOL}_options_data.json`
- `{SYMBOL}_options_data.csv`

## GitHub Dependents 识别

为了提高 GitHub 对本仓库依赖关系的识别概率，仓库额外保留了一个根目录 `requirements.txt`：

- 它是由 `uv` 从 `uv.lock` 导出的镜像文件
- 目标是帮助 GitHub 的 Python dependency graph 更稳定地识别 `finnhub-python`
- 它不是本项目的主依赖入口，不改变 `uv sync` / `uv run ...` 的主工作流

当你修改了 `pyproject.toml` 或更新了 `uv.lock` 后，需要重新导出该文件：

```bash
uv export --frozen --no-dev --format requirements.txt --no-hashes --no-annotate --output-file requirements.txt
```

仓库还包含一个 GitHub Actions 校验工作流，会检查 `requirements.txt` 是否和当前锁文件保持同步。

如果你是仓库管理员，建议同时在 GitHub 仓库设置中确认开启：

- Dependency graph
- GitHub Actions
- Automatic dependency submission

这样 GitHub 才能在静态识别之外补全更多传递依赖。

## API 接口

### `GET /`

返回主页面。

### `POST /api/load_data`

获取、标准化并加载指定股票的期权数据。

请求示例：

```json
{
  "symbol": "AAPL",
  "max_expirations": 4
}
```

### `POST /api/generate_heatmap`

基于当前已加载数据生成热力图。

支持的 `chart_type`：

- `direction_oi`
- `volume`
- `iv`

### `GET /api/available_symbols`

返回本地缓存过的股票代码列表。

### `GET /health`

健康检查接口。

## 常见问题

### 1. `Port 5000 is in use`

本机已有其他程序占用了 `5000` 端口。可直接切换端口启动：

```bash
PORT=5001 uv run python app.py
```

### 2. `FINNHUB_API_KEY is not configured`

说明当前 shell 会话没有配置 API Key。请先执行：

```bash
export FINNHUB_API_KEY="your_finnhub_key"
```

### 3. `Finnhub option-chain endpoint forbidden ...`

如果：

- `quote('AAPL')` 可用
- `company_profile2('AAPL')` 可用
- `option_chain('AAPL')` 返回 `403`

通常表示当前 Finnhub Key 没有 `option-chain` endpoint 的访问权限，属于 Finnhub 套餐或 entitlement 限制，而不是本项目仍在使用旧数据链路。

### 4. 页面提示 Finnhub HTML 错误页或网络错误

常见原因：

- Finnhub 端点临时异常
- 本机 DNS / 网络访问异常
- API Key 权限不足

## 开发与测试

### 运行测试

```bash
uv run pytest -q
```

### 校验 `requirements.txt` 是否与 `uv` 同步

```bash
uv export --frozen --no-dev --format requirements.txt --no-hashes --no-annotate --output-file requirements.txt
git diff --exit-code requirements.txt
```

### 代码约定

- 统一使用 `uv` 管理依赖
- 期权数据通过 `finnhub_provider.py` 获取并标准化
- Web 层尽量保持轻量，业务逻辑放在工具层
- 本地缓存用于热力图生成和调试分析

## 项目结构

```text
Options_Heatmap_Analysis_Tool/
├── app.py                  # Flask Web 服务
├── finnhub_provider.py     # Finnhub 数据获取与错误处理
├── utils_option.py         # 数据标准化、落盘、热力图处理
├── templates/
│   └── index.html          # 前端页面
├── assets/                 # README 预览图
├── tests/                  # 测试用例
├── pyproject.toml          # 项目依赖定义
├── requirements.txt        # GitHub Dependency Graph 识别镜像
├── uv.lock                 # uv 锁文件
└── LICENSE
```

## License

本项目基于 [MIT License](./LICENSE) 开源。

---

## English

A compact but end-to-end options visualization project powered by [Finnhub](https://finnhub.io/docs/api), built with Flask, and managed with `uv`. It covers the full path from market data ingestion and normalization to local caching, chart rendering, and developer-friendly delivery.

### Quick Start

```bash
git clone <repository-url>
cd Options_Heatmap_Analysis_Tool
export FINNHUB_API_KEY="your_finnhub_key"
uv sync
uv run python app.py
```

`requirements.txt` is kept only as a GitHub dependency-graph mirror generated from `uv`, not as the primary install workflow.

If port `5000` is already occupied:

```bash
PORT=5001 uv run python app.py
```

### Core Capabilities

- Fetches option chains, quotes, and company profiles from Finnhub
- Builds a reusable local snapshot layer between external APIs and the UI
- Normalizes snapshots into local JSON / CSV files
- Generates heatmaps for direction x open interest, volume, and implied volatility
- Exposes a small Flask API for loading data and rendering charts

### Important Note

If `quote('AAPL')` and `company_profile2('AAPL')` work but `option_chain('AAPL')` returns `403`, your Finnhub key likely does not include access to the `option-chain` endpoint.
