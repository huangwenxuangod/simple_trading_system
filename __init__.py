"""
简化量化交易系统
Simple Trading System

一个基于Python的量化交易系统，支持：
- 币安API数据获取
- MACD策略实现
- backtesting.py回测
- Alpaca API实盘交易
- SQLite数据存储
"""

__version__ = "1.0.0"
__author__ = "Trading System Developer"
__email__ = "developer@example.com"

# 导入主要模块
from .config import config
from .data_provider import BinanceDataProvider, DataStorage, get_bitcoin_data
from .strategy import MACDStrategy
from .backtest import BacktestRunner, run_simple_backtest, optimize_macd_strategy
from .alpaca_trader import AlpacaTrader, TradingBot

# 导出的公共接口
__all__ = [
    # 配置
    'config',
    
    # 数据提供者
    'BinanceDataProvider',
    'DataStorage', 
    'get_bitcoin_data',
    
    # 策略
    'MACDStrategy',
    
    # 回测
    'BacktestRunner',
    'run_simple_backtest',
    'optimize_macd_strategy',
    
    # 交易
    'AlpacaTrader',
    'TradingBot',
]

def get_version():
    """获取版本信息"""
    return __version__

def get_system_info():
    """获取系统信息"""
    return {
        'name': '简化量化交易系统',
        'version': __version__,
        'author': __author__,
        'features': [
            '币安API数据获取',
            'MACD策略实现', 
            'backtesting.py回测',
            'Alpaca API交易',
            'SQLite数据存储'
        ]
    }

def quick_start():
    """快速开始指南"""
    print("="*50)
    print("简化量化交易系统 - 快速开始")
    print("="*50)
    print("1. 配置环境变量:")
    print("   - 复制 .env.example 为 .env")
    print("   - 填入你的 Alpaca API 密钥")
    print()
    print("2. 获取数据:")
    print("   from simple_trading_system import get_bitcoin_data")
    print("   df = get_bitcoin_data(days=30)")
    print()
    print("3. 运行回测:")
    print("   from simple_trading_system import run_simple_backtest")
    print("   result = run_simple_backtest(days=90)")
    print()
    print("4. 启动主程序:")
    print("   python -m simple_trading_system.main")
    print("="*50)

# 系统启动时的初始化
def _initialize_system():
    """系统初始化"""
    try:
        # 创建数据库表
        storage = DataStorage()
        storage.init_database()
        
        return True
    except Exception as e:
        print(f"系统初始化失败: {e}")
        return False

# 自动初始化
_system_ready = _initialize_system()

if not _system_ready:
    print("警告: 系统初始化未完全成功，某些功能可能不可用")
    print("请检查配置文件和环境变量设置")