# -*- coding:utf8 -*-
"""
期权数据与热力图工具函数合集
"""
import json
import time
from datetime import datetime
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import warnings
warnings.filterwarnings('ignore')
import sys

from finnhub_provider import OptionsDataError, fetch_option_snapshot

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# ================= 数据获取与保存 =================

def get_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    return DATA_DIR


def fetch_options_data(
    symbol="AAPL",
    max_retries=5,
    multiple_expirations=False,
    max_expiration_dates=3,
    client=None,
):
    """从 Finnhub 获取期权数据并保存到 data 目录。"""
    data_dir = get_data_dir()
    normalized_symbol = symbol.upper()
    fetch_start_time = datetime.now()
    print(f"开始获取 {normalized_symbol} 期权数据...")
    print(f"获取开始时间: {fetch_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("----------------------------------------------------------------------------------------------------")
    for attempt in range(max_retries):
        try:
            print(f"尝试第 {attempt + 1} 次获取数据...")
            snapshot = fetch_option_snapshot(
                symbol=normalized_symbol,
                max_expiration_dates=max_expiration_dates,
                multiple_expirations=multiple_expirations,
                client=client,
            )
            options_data = snapshot["options_data"]
            total_calls = len([item for item in options_data if item["type"] == "Call"])
            total_puts = len([item for item in options_data if item["type"] == "Put"])

            print(f"股票代码: {normalized_symbol}")
            print(f"公司名称: {snapshot['company_name']}")
            print(f"数据源: Finnhub")
            print(f"当前股价: ${snapshot['current_price']}")
            print(f"可用的到期日期: {', '.join(snapshot['expiration_dates'])}")
            print(f"市场时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("----------------------------------------------------------------------------------------------------")

            print(f"\n总共获取到 {len(options_data)} 个期权合约的数据")
            print(f"看涨期权: {total_calls} 个")
            print(f"看跌期权: {total_puts} 个")
            fetch_end_time = datetime.now()
            fetch_duration = fetch_end_time - fetch_start_time
            payload = {
                'symbol': normalized_symbol,
                'company_name': snapshot['company_name'],
                'current_price': snapshot['current_price'],
                'expiration_dates': snapshot['expiration_dates'],
                'fetch_start_time': fetch_start_time.isoformat(),
                'fetch_end_time': fetch_end_time.isoformat(),
                'fetch_duration_seconds': fetch_duration.total_seconds(),
                'data_timestamp': fetch_end_time.isoformat(),
                'total_options': len(options_data),
                'calls_count': total_calls,
                'puts_count': total_puts,
                'data_source': snapshot['data_source'],
                'implied_volatility_unit': snapshot['implied_volatility_unit'],
                'options_data': options_data,
            }
            json_path = os.path.join(data_dir, f'{normalized_symbol}_options_data.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            print(f"数据已保存到 {json_path}")
            print(f"获取完成时间: {fetch_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"总耗时: {fetch_duration.total_seconds():.2f} 秒")
            generate_csv_data(normalized_symbol, options_data, data_dir)
            return payload
        except OptionsDataError:
            raise
        except Exception as e:
            print(f"第 {attempt + 1} 次尝试失败: {e}")
            if attempt < max_retries - 1:
                delay = min(2 * (attempt + 1), 5)
                print(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
                print("准备重试...")
            else:
                raise OptionsDataError(
                    f"Failed to fetch options data for {normalized_symbol}: {e}"
                ) from e


def generate_csv_data(symbol, options_data, data_dir):
    if not options_data:
        print("没有数据可保存")
        return
    csv_content = "期权类型,合约名称,到期日期,执行价格,最新价格,买价,卖价,成交量,未平仓合约,隐含波动率\n"
    for option in options_data:
        csv_content += f"{option['type']},{option['contract_name']},{option['expiration_date']},{option['strike_price']},{option['last_price']},{option['bid']},{option['ask']},{option['volume']},{option['open_interest']},{option['implied_volatility']}\n"
    csv_path = os.path.join(data_dir, f'{symbol}_options_data.csv')
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    print(f"CSV数据已保存到 {csv_path}")

def load_options_data(symbol="AAPL"):
    """加载期权数据"""
    data_dir = get_data_dir()
    json_path = os.path.join(data_dir, f'{symbol}_options_data.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"未找到 {json_path} 文件，请先运行期权数据获取命令")
        return None

# ================= 数据处理与热力图 =================

def create_heatmap_data(data):
    """创建热力图数据"""
    if not data or 'options_data' not in data:
        print("数据格式错误")
        return None
    df = pd.DataFrame(data['options_data'])
    if df.empty:
        print("没有可用的期权数据")
        return None
    numeric_columns = ['strike_price', 'last_price', 'bid', 'ask', 'volume', 'open_interest', 'implied_volatility']
    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors='coerce')
    df['direction'] = df['type'].map({'Call': 1, 'Put': -1})
    df['direction_oi'] = df['direction'] * df['open_interest']
    df['direction_oi'] = df['direction_oi'].fillna(0)
    if 'implied_volatility' in df.columns:
        iv_unit = data.get('implied_volatility_unit')
        if iv_unit != 'percent' and df['implied_volatility'].max() <= 1:
            df['implied_volatility'] = df['implied_volatility'] * 100
        df['implied_volatility'] = df['implied_volatility'].fillna(0)
    else:
        df['implied_volatility'] = 0
    df['expiration_date'] = pd.to_datetime(df['expiration_date'])
    df['expiration_display'] = df['expiration_date'].dt.strftime('%m-%d')
    return df

def generate_heatmap(df, symbol="AAPL"):
    """生成热力图（补全所有strike/expiration组合，避免空白）"""
    if df is None or df.empty:
        print("没有数据可以生成热力图")
        return
    min_strike = int(np.floor(df['strike_price'].min()))
    max_strike = int(np.ceil(df['strike_price'].max()))
    step = 1
    if max_strike - min_strike > 50:
        step = 5
    if max_strike - min_strike > 200:
        step = 10
    strike_range = np.arange(min_strike, max_strike + step, step)
    all_expirations = sorted(df['expiration_display'].unique(), key=lambda x: datetime.strptime(x, '%m-%d'))
    pivot_data = df.pivot_table(
        values='direction_oi',
        index='strike_price',
        columns='expiration_display',
        aggfunc='sum',
        fill_value=0
    )
    pivot_data = pivot_data.reindex(index=strike_range, columns=all_expirations, fill_value=0)
    plt.figure(figsize=(max(10, len(all_expirations)*0.8), max(8, len(strike_range)*0.18)))
    sns.heatmap(
        pivot_data,
        annot=False,
        cmap='RdBu_r',
        center=0,
        cbar_kws={'label': '方向 × 未平仓量'},
        linewidths=0,
        square=False
    )
    plt.title(f'{symbol} 期权方向×未平仓量热力图\n(红色=看涨偏好，蓝色=看跌偏好)', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('到期日期', fontsize=12)
    plt.ylabel('执行价格 ($)', fontsize=12)
    plt.yticks(rotation=0)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{symbol}_options_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"热力图已保存为 {symbol}_options_heatmap.png")
    plt.show()

def generate_volatility_heatmap(df, symbol="AAPL"):
    """生成波动率热力图"""
    if df is None or df.empty:
        print("没有数据可以生成波动率热力图")
        return
    if 'implied_volatility' not in df.columns or df['implied_volatility'].sum() == 0:
        print("没有可用的波动率数据")
        return
    pivot_iv = df.pivot_table(
        values='implied_volatility',
        index='strike_price',
        columns='expiration_display',
        aggfunc='mean',
        fill_value=0
    ).sort_index()
    plt.figure(figsize=(12, 8))
    sns.heatmap(
        pivot_iv,
        annot=False,
        cmap='viridis',
        cbar_kws={'label': '隐含波动率 (%)'},
        linewidths=0,
        square=False
    )
    plt.title(f'{symbol} 期权隐含波动率热力图', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('到期日期', fontsize=12)
    plt.ylabel('执行价格 ($)', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'{symbol}_volatility_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"波动率热力图已保存为 {symbol}_volatility_heatmap.png")
    plt.show()

def generate_enhanced_heatmap(df, symbol="AAPL"):
    """生成增强版热力图，包含更多信息"""
    if df is None or df.empty:
        print("没有数据可以生成热力图")
        return
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 18))
    pivot_oi = df.pivot_table(
        values='direction_oi',
        index='strike_price',
        columns='expiration_display',
        aggfunc='sum',
        fill_value=0
    ).sort_index()
    sns.heatmap(
        pivot_oi,
        ax=ax1,
        annot=False,
        cmap='RdBu_r',
        center=0,
        cbar_kws={'label': '方向 × 未平仓量'},
        linewidths=0,
        square=False
    )
    ax1.set_title(f'{symbol} 期权方向×未平仓量热力图\n(红色=看涨偏好，蓝色=看跌偏好)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('')
    ax1.set_ylabel('执行价格 ($)', fontsize=12)
    pivot_volume = df.pivot_table(
        values='volume',
        index='strike_price',
        columns='expiration_display',
        aggfunc='sum',
        fill_value=0
    ).sort_index()
    sns.heatmap(
        pivot_volume,
        ax=ax2,
        annot=False,
        cmap='YlOrRd',
        cbar_kws={'label': '成交量'},
        linewidths=0,
        square=False
    )
    ax2.set_title(f'{symbol} 期权成交量热力图', fontsize=14, fontweight='bold')
    ax2.set_xlabel('')
    ax2.set_ylabel('执行价格 ($)', fontsize=12)
    if 'implied_volatility' in df.columns and df['implied_volatility'].sum() > 0:
        pivot_iv = df.pivot_table(
            values='implied_volatility',
            index='strike_price',
            columns='expiration_display',
            aggfunc='mean',
            fill_value=0
        ).sort_index()
        sns.heatmap(
            pivot_iv,
            ax=ax3,
            annot=False,
            cmap='viridis',
            cbar_kws={'label': '隐含波动率 (%)'},
            linewidths=0,
            square=False
        )
        ax3.set_title(f'{symbol} 期权隐含波动率热力图', fontsize=14, fontweight='bold')
        ax3.set_xlabel('到期日期', fontsize=12)
        ax3.set_ylabel('执行价格 ($)', fontsize=12)
    else:
        ax3.text(0.5, 0.5, '无波动率数据', ha='center', va='center', transform=ax3.transAxes, fontsize=16)
        ax3.set_title(f'{symbol} 期权隐含波动率热力图 (无数据)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{symbol}_options_enhanced_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"增强版热力图已保存为 {symbol}_options_enhanced_heatmap.png")
    plt.show()

def print_summary_statistics(df, symbol="AAPL"):
    if df is None or df.empty:
        return
    print(f"\n=== {symbol} 期权数据汇总 ===")
    print(f"总期权数量: {len(df)}")
    print(f"看涨期权数量: {len(df[df['type'] == 'Call'])}")
    print(f"看跌期权数量: {len(df[df['type'] == 'Put'])}")
    print(f"到期日期数量: {df['expiration_date'].nunique()}")
    print(f"执行价格范围: ${df['strike_price'].min():.2f} - ${df['strike_price'].max():.2f}")
    print(f"\n按到期日期统计:")
    date_stats = df.groupby('expiration_display').agg({
        'direction_oi': 'sum',
        'volume': 'sum',
        'open_interest': 'sum',
        'implied_volatility': 'mean'
    }).round(2)
    print(date_stats)
    max_call_oi = df[df['direction_oi'] > 0]['direction_oi'].max()
    max_put_oi = abs(df[df['direction_oi'] < 0]['direction_oi'].min())
    print(f"\n最大看涨偏好: {max_call_oi:,.0f}")
    print(f"最大看跌偏好: {max_put_oi:,.0f}")
    if 'implied_volatility' in df.columns and df['implied_volatility'].sum() > 0:
        print(f"\n波动率统计:")
        print(f"最小IV: {df['implied_volatility'].min():.2f}%")
        print(f"最大IV: {df['implied_volatility'].max():.2f}%")
        print(f"平均IV: {df['implied_volatility'].mean():.2f}%")
        print(f"中位数IV: {df['implied_volatility'].median():.2f}%")
    else:
        print(f"\n波动率数据: 无可用数据")

# ================= 命令行入口 =================

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'fetch':
        # 极简获取模式：uv run python utils_option.py fetch TSLA 3
        if len(sys.argv) < 3:
            print("用法: uv run python utils_option.py fetch 股票代码 [最多到期日数]")
            return
        symbol = sys.argv[2].upper()
        max_exp = int(sys.argv[3]) if len(sys.argv) > 3 else None
        try:
            fetch_options_data(symbol, max_expiration_dates=max_exp, multiple_expirations=True)
            print(f"已获取 {symbol} 的期权数据到 data 目录")
        except OptionsDataError as exc:
            print(f"获取失败: {exc}")
        return
    # 默认分析和画图
    symbol = "AAPL"
    print("正在加载期权数据...")
    data = load_options_data(symbol)
    if data is None:
        return
    print("正在处理数据...")
    df = create_heatmap_data(data)
    if df is None:
        return
    print("正在生成热力图...")
    generate_heatmap(df, symbol)
    generate_enhanced_heatmap(df, symbol)
    generate_volatility_heatmap(df, symbol)
    print_summary_statistics(df, symbol)

if __name__ == "__main__":
    main() 
