"""
币安数据获取模块
Binance Data Provider
"""

import pandas as pd
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import Optional, List
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    # 尝试相对导入（当作为包导入时）
    from .config import config
except ImportError:
    # 如果相对导入失败，使用绝对导入（当直接运行时）
    from simple_trading_system.config import config


class BinanceDataProvider:
    """币安数据提供者 - 直接使用REST API"""
    
    def __init__(self):
        """初始化币安API客户端"""
        self.base_url = "https://api.binance.com"
        self.session = requests.Session()
        
    def get_historical_data(self, 
                          symbol: str = "BTCUSDT",
                          interval: str = "1h",
                          start_time: Optional[int] = None,
                          end_time: Optional[int] = None,
                          limit: int = 1000) -> pd.DataFrame:
        """
        获取历史K线数据
        
        Args:
            symbol: 交易对符号
            interval: 时间间隔 (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            start_time: 开始时间戳(毫秒)
            end_time: 结束时间戳(毫秒)
            limit: 数据条数限制 (最大1000)
            
        Returns:
            包含OHLCV数据的DataFrame
        """
        try:
            # 构建API请求URL
            url = f"{self.base_url}/api/v3/klines"
            
            # 构建请求参数
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': min(limit, 1000)  # 币安API限制最大1000条
            }
            
            if start_time:
                params['startTime'] = start_time
            if end_time:
                params['endTime'] = end_time
            
            # 发送请求
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            klines = response.json()
            
            if not klines:
                raise ValueError("未获取到数据")
            
            # 转换为DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # 数据类型转换
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['Open'] = df['Open'].astype(float)
            df['High'] = df['High'].astype(float)
            df['Low'] = df['Low'].astype(float)
            df['Close'] = df['Close'].astype(float)
            df['Volume'] = df['Volume'].astype(float)
            
            # 设置时间索引
            df.set_index('timestamp', inplace=True)
            
            # 只保留OHLCV列
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            print(f"成功获取 {symbol} 数据，共 {len(df)} 条记录")
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"网络请求错误: {e}")
            raise
        except Exception as e:
            print(f"获取数据失败: {e}")
            raise
    
    def get_latest_price(self, symbol: str = "BTCUSDT") -> float:
        """获取最新价格"""
        try:
            url = f"{self.base_url}/api/v3/ticker/price"
            params = {'symbol': symbol}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return float(data['price'])
            
        except Exception as e:
            print(f"获取最新价格失败: {e}")
            raise
    
    def get_24hr_ticker(self, symbol: str = "BTCUSDT") -> dict:
        """获取24小时价格变动统计"""
        try:
            url = f"{self.base_url}/api/v3/ticker/24hr"
            params = {'symbol': symbol}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"获取24小时统计失败: {e}")
            raise


class DataStorage:
    """数据存储管理"""
    
    def __init__(self, db_path: str = None):
        """初始化数据库连接"""
        self.db_path = db_path or config.DATABASE_PATH
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS price_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, timestamp)
                )
            ''')
            
            # 创建索引
            conn.execute('CREATE INDEX IF NOT EXISTS idx_symbol_timestamp ON price_data(symbol, timestamp)')
    
    def save_data(self, df: pd.DataFrame, symbol: str):
        """保存数据到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 准备数据
                data_to_insert = []
                for timestamp, row in df.iterrows():
                    data_to_insert.append((
                        symbol,
                        timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        row['Open'],
                        row['High'],
                        row['Low'],
                        row['Close'],
                        row['Volume']
                    ))
                
                # 批量插入，忽略重复数据
                conn.executemany('''
                    INSERT OR IGNORE INTO price_data 
                    (symbol, timestamp, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', data_to_insert)
                
                print(f"成功保存 {len(data_to_insert)} 条 {symbol} 数据到数据库")
                
        except Exception as e:
            print(f"保存数据失败: {e}")
            raise
    
    def load_data(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """从数据库加载数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT timestamp, open, high, low, close, volume FROM price_data WHERE symbol = ?"
                params = [symbol]
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date)
                
                query += " ORDER BY timestamp"
                
                df = pd.read_sql_query(query, conn, params=params)
                
                if df.empty:
                    return pd.DataFrame()
                
                # 转换数据类型
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                
                print(f"从数据库加载 {symbol} 数据，共 {len(df)} 条记录")
                return df
                
        except Exception as e:
            print(f"加载数据失败: {e}")
            raise


def get_bitcoin_data(days: int = 30, save_to_db: bool = True) -> pd.DataFrame:
    """
    获取比特币数据的便捷函数
    
    Args:
        days: 获取最近多少天的数据
        save_to_db: 是否保存到数据库
        
    Returns:
        比特币价格数据DataFrame
    """
    provider = BinanceDataProvider()
    storage = DataStorage()
    
    # 计算时间戳范围
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    
    # 获取数据
    df = provider.get_historical_data(
        symbol=config.SYMBOL,
        interval="1h",
        start_time=start_time,
        end_time=end_time
    )
    
    # 保存到数据库
    if save_to_db:
        storage.save_data(df, config.SYMBOL)
    
    return df