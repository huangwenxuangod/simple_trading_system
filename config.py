"""
配置管理
Configuration Management
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """系统配置"""
    
    BINANCE_BASE_URL: str = "https://api.binance.com"
    
    # Alpaca API配置
    ALPACA_API_KEY: Optional[str] = None
    ALPACA_SECRET_KEY: Optional[str] = None
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets/v2"
    
    # 交易配置
    SYMBOL: str = "BTCUSDT"  # 币安交易对
    ALPACA_SYMBOL: str = "BTC/USD"  # Alpaca交易对
    INITIAL_CAPITAL: float = 10000.0
    
    # 数据库配置
    DATABASE_PATH: str = "trading_data.db"
    
    # MACD策略参数
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    
    def __post_init__(self):
        """从环境变量加载配置"""
        # 加载 .env 文件
        from dotenv import load_dotenv
        load_dotenv()
        
        # 优先使用标准的 APCA_ 前缀环境变量
        self.ALPACA_API_KEY = (
            os.getenv('APCA_API_KEY_ID') or 
            os.getenv('ALPACA_API_KEY') or 
            self.ALPACA_API_KEY
        )
        self.ALPACA_SECRET_KEY = (
            os.getenv('APCA_API_SECRET_KEY') or 
            os.getenv('ALPACA_SECRET_KEY') or 
            self.ALPACA_SECRET_KEY
        )
        self.ALPACA_BASE_URL = (
            os.getenv('APCA_API_BASE_URL') or 
            self.ALPACA_BASE_URL
        )

# 全局配置实例
config = Config()