"""
MACD策略实现
MACD Strategy Implementation
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
import talib


class MACDStrategy:
    """MACD策略类"""
    
    def __init__(self, 
                 fast_period: int = 12,
                 slow_period: int = 26,
                 signal_period: int = 9):
        """
        初始化MACD策略
        
        Args:
            fast_period: 快速EMA周期
            slow_period: 慢速EMA周期
            signal_period: 信号线EMA周期
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
        # 策略状态
        self.position = 0  # 0: 无仓位, 1: 多头, -1: 空头
        self.last_signal = None
        
    def calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算MACD指标
        
        Args:
            prices: 价格序列（通常是收盘价）
            
        Returns:
            (macd_line, signal_line, histogram)
        """
        # 使用TA-Lib计算MACD
        macd_line, signal_line, histogram = talib.MACD(
            prices.values,
            fastperiod=self.fast_period,
            slowperiod=self.slow_period,
            signalperiod=self.signal_period
        )
        
        return (
            pd.Series(macd_line, index=prices.index),
            pd.Series(signal_line, index=prices.index),
            pd.Series(histogram, index=prices.index)
        )
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            包含信号的DataFrame
        """
        # 复制数据
        result = df.copy()
        
        # 计算MACD指标
        macd_line, signal_line, histogram = self.calculate_macd(df['Close'])
        
        # 添加MACD指标到结果
        result['MACD'] = macd_line
        result['MACD_Signal'] = signal_line
        result['MACD_Histogram'] = histogram
        
        # 初始化信号列
        result['Signal'] = 0
        result['Position'] = 0
        
        # 生成交易信号
        for i in range(1, len(result)):
            current_macd = result['MACD'].iloc[i]
            current_signal = result['MACD_Signal'].iloc[i]
            prev_macd = result['MACD'].iloc[i-1]
            prev_signal = result['MACD_Signal'].iloc[i-1]
            
            # 跳过NaN值
            if pd.isna(current_macd) or pd.isna(current_signal) or pd.isna(prev_macd) or pd.isna(prev_signal):
                continue
            
            # 买入信号：MACD线从下方穿越信号线
            if prev_macd <= prev_signal and current_macd > current_signal:
                result.loc[result.index[i], 'Signal'] = 1  # 买入信号
                self.position = 1
            
            # 卖出信号：MACD线从上方穿越信号线
            elif prev_macd >= prev_signal and current_macd < current_signal:
                result.loc[result.index[i], 'Signal'] = -1  # 卖出信号
                self.position = -1
            
            # 记录当前仓位
            result.loc[result.index[i], 'Position'] = self.position
        
        return result

class BacktestingStrategy:
    """
    适配backtesting.py库的策略类
    """
    
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def init(self):
        """初始化策略（backtesting.py要求的方法）"""
        # 计算MACD指标
        close = self.data.Close
        
        self.macd, self.signal, self.histogram = talib.MACD(
            close.values,
            fastperiod=self.fast_period,
            slowperiod=self.slow_period,
            signalperiod=self.signal_period
        )
        
        # 转换为pandas Series
        self.macd = pd.Series(self.macd, index=close.index)
        self.signal = pd.Series(self.signal, index=close.index)
        self.histogram = pd.Series(self.histogram, index=close.index)
    
    def next(self):
        """每个时间步的策略逻辑（backtesting.py要求的方法）"""
        # 获取当前和前一个MACD值
        if len(self.data) < 2:
            return
        
        current_macd = self.macd[-1]
        current_signal = self.signal[-1]
        prev_macd = self.macd[-2]
        prev_signal = self.signal[-2]
        
        # 跳过NaN值
        if pd.isna(current_macd) or pd.isna(current_signal) or pd.isna(prev_macd) or pd.isna(prev_signal):
            return
        
        # 买入信号：MACD线从下方穿越信号线
        if prev_macd <= prev_signal and current_macd > current_signal:
            if not self.position:
                self.buy()
        
        # 卖出信号：MACD线从上方穿越信号线
        elif prev_macd >= prev_signal and current_macd < current_signal:
            if self.position:
                self.sell()


def create_backtesting_strategy(fast_period=12, slow_period=26, signal_period=9):
    """
    创建适用于backtesting.py的策略类
    
    Args:
        fast_period: 快速EMA周期
        slow_period: 慢速EMA周期
        signal_period: 信号线EMA周期
        
    Returns:
        策略类
    """
    from backtesting import Strategy
    
    class MACDBacktestStrategy(Strategy):
        # 策略参数
        fast_period = fast_period
        slow_period = slow_period
        signal_period = signal_period
        
        def init(self):
            """初始化策略"""
            close = self.data.Close
            
            # 计算MACD指标
            macd, signal, histogram = talib.MACD(
                close.values,
                fastperiod=self.fast_period,
                slowperiod=self.slow_period,
                signalperiod=self.signal_period
            )
            
            # 存储指标
            self.macd = self.I(lambda: macd)
            self.signal = self.I(lambda: signal)
            self.histogram = self.I(lambda: histogram)
        
        def next(self):
            """策略逻辑"""
            # 获取当前和前一个MACD值
            if len(self.data) < 2:
                return
            
            current_macd = self.macd[-1]
            current_signal = self.signal[-1]
            prev_macd = self.macd[-2]
            prev_signal = self.signal[-2]
            
            # 跳过NaN值
            if np.isnan(current_macd) or np.isnan(current_signal) or np.isnan(prev_macd) or np.isnan(prev_signal):
                return
            
            # 买入信号：MACD线从下方穿越信号线
            if prev_macd <= prev_signal and current_macd > current_signal:
                if not self.position:
                    self.buy()
            
            # 卖出信号：MACD线从上方穿越信号线
            elif prev_macd >= prev_signal and current_macd < current_signal:
                if self.position:
                    self.sell()
    
    return MACDBacktestStrategy