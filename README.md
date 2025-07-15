# 期权热力图分析工具 / Options Heatmap Analysis Tool

[English](#english) | [中文](#chinese)

## English

### Overview

A Flask-based web application for analyzing options data and generating heatmaps. This tool helps traders and investors visualize options market sentiment by displaying open interest and volume data in an interactive heatmap format.

### Features

- **Real-time Data Fetching**: Automatically fetches options data from Yahoo Finance
- **Interactive Heatmaps**: Visualize options data with strike price vs expiration date
- **Multiple Metrics**: Display Open Interest, Volume, and other key metrics
- **Web Interface**: User-friendly web interface for data analysis
- **Command Line Tools**: CLI support for batch data processing
- **Data Persistence**: Local storage of options data for offline analysis

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd option
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create data directory**
   ```bash
   mkdir data
   ```

### Usage

#### Web Interface

1. **Start the Flask application**
   ```bash
   python app.py
   ```

2. **Open your browser and navigate to**
   ```
   http://localhost:5000
   ```

3. **Select a stock symbol and view the options heatmap**

#### Command Line Interface

**Fetch options data for a specific symbol:**
```bash
python utils_option.py --symbol AAPL --mode fetch
```

**Generate heatmap for a specific symbol:**
```bash
python utils_option.py --symbol AAPL --mode heatmap
```

**Complete analysis (fetch + heatmap):**
```bash
python utils_option.py --symbol AAPL --mode full
```

### Project Structure

```
option/
├── app.py                 # Flask web application
├── utils_option.py        # Core utilities for data fetching and heatmap generation
├── templates/             # HTML templates
│   └── index.html
├── static/                # Static assets
├── data/                  # Options data storage
└── README.md             # This file
```

### API Endpoints

- `GET /`: Main page with options heatmap interface
- `GET /api/available_symbols`: Get list of available stock symbols
- `GET /api/options_data/<symbol>`: Get options data for a specific symbol
- `GET /api/heatmap/<symbol>`: Generate and return heatmap for a symbol

### Configuration

The application uses default settings for Yahoo Finance data fetching. You can modify the following parameters in `utils_option.py`:

- `num_expirations`: Number of expiration dates to fetch (default: 4)
- `data_dir`: Directory for storing options data (default: "data")

### Dependencies

- Flask: Web framework
- pandas: Data manipulation
- plotly: Interactive plotting
- requests: HTTP requests
- yfinance: Yahoo Finance data access

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Chinese

### 项目概述

基于Flask的期权数据分析和热力图生成工具。该工具帮助交易者和投资者通过交互式热力图格式显示未平仓量和成交量数据，可视化期权市场情绪。

### 主要功能

- **实时数据获取**: 自动从雅虎财经获取期权数据
- **交互式热力图**: 以执行价格vs到期日期的形式可视化期权数据
- **多种指标**: 显示未平仓量、成交量和其他关键指标
- **Web界面**: 用户友好的数据分析Web界面
- **命令行工具**: 支持批量数据处理的CLI工具
- **数据持久化**: 本地存储期权数据，支持离线分析

### 安装说明

1. **克隆仓库**
   ```bash
   git clone <repository-url>
   cd option
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **创建数据目录**
   ```bash
   mkdir data
   ```

### 使用方法

#### Web界面

1. **启动Flask应用**
   ```bash
   python app.py
   ```

2. **在浏览器中打开**
   ```
   http://localhost:5000
   ```

3. **选择股票代码并查看期权热力图**

#### 命令行界面

**获取特定股票的期权数据:**
```bash
python utils_option.py --symbol AAPL --mode fetch
```

**为特定股票生成热力图:**
```bash
python utils_option.py --symbol AAPL --mode heatmap
```

**完整分析（获取数据+生成热力图）:**
```bash
python utils_option.py --symbol AAPL --mode full
```

### 项目结构

```
option/
├── app.py                 # Flask Web应用
├── utils_option.py        # 数据获取和热力图生成的核心工具
├── templates/             # HTML模板
│   └── index.html
├── static/                # 静态资源
├── data/                  # 期权数据存储
└── README.md             # 本文件
```

### API接口

- `GET /`: 期权热力图界面主页面
- `GET /api/available_symbols`: 获取可用股票代码列表
- `GET /api/options_data/<symbol>`: 获取特定股票的期权数据
- `GET /api/heatmap/<symbol>`: 生成并返回股票的热力图

### 配置说明

应用程序使用雅虎财经数据获取的默认设置。您可以在 `utils_option.py` 中修改以下参数：

- `num_expirations`: 获取的到期日期数量（默认: 4）
- `data_dir`: 期权数据存储目录（默认: "data"）

### 依赖包

- Flask: Web框架
- pandas: 数据处理
- plotly: 交互式绘图
- requests: HTTP请求
- yfinance: 雅虎财经数据访问

### 贡献指南

1. Fork 本仓库
2. 创建功能分支
3. 进行您的修改
4. 如适用，添加测试
5. 提交 Pull Request

### 许可证

本项目采用 MIT 许可证 - 详情请参阅 LICENSE 文件。 