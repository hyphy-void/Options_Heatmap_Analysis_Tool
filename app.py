# -*- coding:utf8 -*-
"""
期权热力图Web应用
基于Flask的Web服务，提供期权热力图生成和展示功能
"""

import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template, request, jsonify, send_file
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import os
import io
import base64
import warnings
import sys
warnings.filterwarnings('ignore')

from utils_option import (
    scrape_options_data,
    load_options_data,
    create_heatmap_data,
    generate_heatmap,
    generate_volatility_heatmap,
    generate_enhanced_heatmap,
    print_summary_statistics
)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

app = Flask(__name__)

# 全局变量存储当前数据
current_data = None
current_symbol = None

def load_options_data_web(symbol="AAPL", max_expirations=None):
    """每次都强制抓取最新期权数据，覆盖旧数据"""
    try:
        # 修改为从data目录读取
        file_path = os.path.join(os.path.dirname(__file__), 'data', f'{symbol}_options_data.json')
        # 直接调用utils_option中的函数抓取数据
        print(f"强制抓取 {symbol} 的最新期权数据……")
        
        # 调用utils_option中的scrape_options_data函数
        from utils_option import scrape_options_data
        scrape_options_data(
            symbol=symbol, 
            max_retries=3, 
            multiple_expirations=True, 
            max_expiration_dates=max_expirations if max_expirations else 4
        )
        
        if not os.path.exists(file_path):
            print(f"抓取失败，未生成 {file_path}")
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}，文件内容可能不是有效数据，已删除该文件")
            os.remove(file_path)
            return None
        if isinstance(data, list):
            data = {'options_data': data}
        return data
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None

def generate_heatmap_image(df, symbol="AAPL", chart_type="direction_oi"):
    """Generate heatmap and return base64 image (English labels, with current price line and data timestamp)"""
    if df is None or df.empty:
        return None
    import datetime
    current_price = None
    data_timestamp = None
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'data', f'{symbol}_options_data.json')
        import json as _json
        with open(file_path, 'r', encoding='utf-8') as f:
            raw = _json.load(f)
            current_price = raw.get('current_price')
            # 获取数据时间戳
            data_timestamp = raw.get('data_timestamp')
            if data_timestamp:
                # 将ISO格式时间戳转换为可读格式
                try:
                    dt = datetime.datetime.fromisoformat(data_timestamp.replace('Z', '+00:00'))
                    data_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    data_timestamp = None
    except Exception:
        pass
    
    if chart_type == "direction_oi":
        value_col = 'direction_oi'
        cmap = 'RdBu_r'
        title = f'{symbol} Option OI Direction Heatmap\n(Red = Call Preference, Blue = Put Preference)'
        cbar_label = 'Direction × Open Interest'
        center = 0
    elif chart_type == "volume":
        value_col = 'volume'
        cmap = 'YlOrRd'
        title = f'{symbol} Option Volume Heatmap'
        cbar_label = 'Volume'
        center = None
    elif chart_type == "iv":
        value_col = 'implied_volatility'
        cmap = 'viridis'
        title = f'{symbol} Option Implied Volatility Heatmap'
        cbar_label = 'Implied Volatility (%)'
        center = None
    else:
        return None
    pivot_data = df.pivot_table(
        values=value_col,
        index='strike_price',
        columns='expiration_display',
        aggfunc='sum',
        fill_value=0
    ).sort_index()
    plt.figure(figsize=(12, 8))
    ax = sns.heatmap(
        pivot_data,
        annot=False,
        cmap=cmap,
        center=center,
        cbar_kws={'label': cbar_label},
        linewidths=0,
        square=False
    )
    if current_price is not None:
        try:
            strike_prices = pivot_data.index.values
            if strike_prices[0] <= current_price <= strike_prices[-1]:
                y_pos = np.interp(current_price, strike_prices, np.arange(len(strike_prices)))
                ax.axhline(y=y_pos + 0.5, color='orange', linestyle='--', linewidth=2, label=f'Current Price: {current_price}')
                ax.legend(loc='upper right')
        except Exception:
            pass
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Expiration Date', fontsize=12)
    plt.ylabel('Strike Price ($)', fontsize=12)
    
    # 添加数据时间戳（优先显示数据时间，如果没有则显示生成时间）
    if data_timestamp:
        timestamp_text = f'Data from: {data_timestamp}'
    else:
        timestamp_text = f'Generated at: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    
    plt.text(0.5, -0.13, timestamp_text, fontsize=11, color='gray', ha='center', va='center', transform=ax.transAxes)
    plt.tight_layout()
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()
    return img_base64

def get_summary_statistics(df, symbol="AAPL"):
    """获取汇总统计信息"""
    if df is None or df.empty:
        return {}
    
    stats = {
        'symbol': symbol,
        'total_options': len(df),
        'call_options': len(df[df['type'] == 'Call']),
        'put_options': len(df[df['type'] == 'Put']),
        'expiration_dates': df['expiration_date'].nunique(),
        'strike_range': {
            'min': float(df['strike_price'].min()),
            'max': float(df['strike_price'].max())
        }
    }
    
    # 按到期日期统计
    date_stats = df.groupby('expiration_display').agg({
        'direction_oi': 'sum',
        'volume': 'sum',
        'open_interest': 'sum',
        'implied_volatility': 'mean'  # 添加IV平均值统计
    }).round(2).to_dict('index')
    
    stats['date_statistics'] = date_stats
    
    # 最大看涨和看跌偏好
    max_call_oi = df[df['direction_oi'] > 0]['direction_oi'].max()
    max_put_oi = abs(df[df['direction_oi'] < 0]['direction_oi'].min())
    
    stats['max_call_preference'] = float(max_call_oi) if not pd.isna(max_call_oi) else 0
    stats['max_put_preference'] = float(max_put_oi) if not pd.isna(max_put_oi) else 0
    
    # IV统计信息
    if 'implied_volatility' in df.columns and df['implied_volatility'].sum() > 0:
        stats['iv_stats'] = {
            'min': float(df['implied_volatility'].min()),
            'max': float(df['implied_volatility'].max()),
            'mean': float(df['implied_volatility'].mean()),
            'median': float(df['implied_volatility'].median())
        }
    else:
        stats['iv_stats'] = None
    
    return stats

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/load_data', methods=['POST'])
def api_load_data():
    """API: 加载期权数据"""
    global current_data, current_symbol
    data = request.get_json()
    symbol = data.get('symbol', 'AAPL').upper()
    max_expirations = data.get('max_expirations')
    if max_expirations is not None:
        try:
            max_expirations = int(max_expirations)
        except Exception:
            max_expirations = None
    # 加载数据
    raw_data = load_options_data_web(symbol, max_expirations)
    if raw_data is None:
        return jsonify({'success': False, 'message': f'No option data file found for {symbol}'})
    # 处理数据
    df = create_heatmap_data(raw_data)
    if df is None:
        return jsonify({'success': False, 'message': 'Data processing failed'})
    # 保存到全局变量
    current_data = df
    current_symbol = symbol
    # 获取统计信息
    stats = get_summary_statistics(df, symbol)
    # 获取公司名
    company_name = raw_data.get('company_name', symbol)
    
    # 获取数据时间戳信息
    data_info = {
        'data_timestamp': raw_data.get('data_timestamp'),
        'scrape_start_time': raw_data.get('scrape_start_time'),
        'scrape_end_time': raw_data.get('scrape_end_time'),
        'scrape_duration_seconds': raw_data.get('scrape_duration_seconds')
    }
    
    return jsonify({
        'success': True,
        'message': f'{symbol} data loaded successfully',
        'statistics': stats,
        'company_name': company_name,
        'data_info': data_info
    })

@app.route('/api/generate_heatmap', methods=['POST'])
def api_generate_heatmap():
    """API: 生成热力图"""
    global current_data, current_symbol
    
    if current_data is None:
        return jsonify({'success': False, 'message': '请先加载数据'})
    
    data = request.get_json()
    chart_type = data.get('chart_type', 'direction_oi')
    
    # 生成热力图
    img_base64 = generate_heatmap_image(current_data, current_symbol, chart_type)
    
    if img_base64 is None:
        return jsonify({'success': False, 'message': '生成热力图失败'})
    
    return jsonify({
        'success': True,
        'image': img_base64,
        'chart_type': chart_type
    })

@app.route('/api/available_symbols')
def api_available_symbols():
    """API: 获取可用的股票代码"""
    symbols = []
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    if os.path.exists(data_dir):
        for file in os.listdir(data_dir):
            if file.endswith('_options_data.json'):
                symbol = file.replace('_options_data.json', '')
                symbols.append(symbol)
    
    return jsonify({'symbols': symbols})

@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'options-heatmap'
    })

if __name__ == '__main__':
    # 创建templates目录
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("期权热力图Web服务启动中...")
    print("访问地址: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True) 