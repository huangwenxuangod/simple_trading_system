"""
回测模块 - 集成backtesting.py
Backtesting Module
"""

import pandas as pd
import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover, FractionalBacktest
import talib
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    # 尝试相对导入（当作为包导入时）
    from .data_provider import get_bitcoin_data
    from .config import config
    from .strategy import MACDStrategy
except ImportError:
    # 如果相对导入失败，使用绝对导入（当直接运行时）
    from simple_trading_system.data_provider import get_bitcoin_data
    from simple_trading_system.config import config
    from simple_trading_system.strategy import MACDStrategy


# 使用strategy.py中的MACDStrategy类来生成适配backtesting.py的策略类
def create_macd_strategy(fast_period=12, slow_period=26, signal_period=9, position_size=0.8):
    """
    创建MACD策略类，直接使用strategy.py中的MACDStrategy信号
    
    Args:
        fast_period: 快速EMA周期
        slow_period: 慢速EMA周期  
        signal_period: 信号线EMA周期
        position_size: 仓位大小（0-1之间的分数）
        
    Returns:
        适配backtesting.py的策略类
    """
    
    class MACDBacktestStrategy(Strategy):
        """MACD回测策略 - 直接使用strategy.py中的MACDStrategy信号"""
        
        def init(self):
            """初始化策略"""
            # 设置策略参数
            self.fast_period = fast_period
            self.slow_period = slow_period
            self.signal_period = signal_period
            self.position_size = position_size
            
            # 创建MACDStrategy实例
            self.macd_strategy = MACDStrategy(
                fast_period=self.fast_period,
                slow_period=self.slow_period,
                signal_period=self.signal_period
            )
            
            # 准备数据DataFrame
            df = pd.DataFrame({
                'Open': self.data.Open,
                'High': self.data.High,
                'Low': self.data.Low,
                'Close': self.data.Close,
                'Volume': self.data.Volume
            }, index=range(len(self.data)))
            
            # 使用MACDStrategy生成信号
            signals_df = self.macd_strategy.generate_signals(df)
            
            # 使用backtesting.py的I函数包装信号和指标
            self.macd = self.I(lambda: signals_df['MACD'].values)
            self.signal_line = self.I(lambda: signals_df['MACD_Signal'].values)
            self.histogram = self.I(lambda: signals_df['MACD_Histogram'].values)
            self.signals = self.I(lambda: signals_df['Signal'].values)
        
        def next(self):
            """策略逻辑 - 直接使用MACDStrategy生成的信号"""
            # 跳过前面的NaN值
            if len(self.data) < max(self.fast_period, self.slow_period, self.signal_period) + 10:
                return
            
            # 获取当前信号和前一个信号
            current_signal = self.signals[-1]
            prev_signal = self.signals[-2] if len(self.signals) > 1 else 0
            
            # 跳过NaN值
            if np.isnan(current_signal):
                return
            
            # 只在信号发生变化时执行交易
            # 买入信号：从0或-1变为1
            if current_signal == 1 and prev_signal != 1:
                if not self.position:
                    # 使用仓位大小作为资金比例（0-1之间的分数）
                    # FractionalBacktest支持小数仓位大小
                    self.buy(size=self.position_size)
            
            # 卖出信号：从0或1变为-1
            elif current_signal == -1 and prev_signal != -1:
                if self.position:
                    # 平仓所有持仓
                    self.position.close()
    
    return MACDBacktestStrategy


class BacktestRunner:
    """回测运行器 - 集成strategy.py中的策略"""
    
    def __init__(self, data: pd.DataFrame = None, strategy_params: dict = None):
        """
        初始化回测运行器
        
        Args:
            data: 价格数据DataFrame，如果为None则自动获取比特币数据
            strategy_params: 策略参数字典，包含fast_period, slow_period, signal_period等
        """
        if data is None:
            print("正在获取比特币数据...")
            self.data = get_bitcoin_data(days=90)  # 获取90天数据用于回测
        else:
            self.data = data
        
        # 设置默认策略参数
        self.strategy_params = strategy_params or {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'position_size': 0.8
        }
        
        # 确保数据格式正确
        self._prepare_data()
    
    def _prepare_data(self):
        """准备回测数据"""
        # 确保列名正确
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in self.data.columns:
                raise ValueError(f"数据缺少必需的列: {col}")
        
        # 移除NaN值
        self.data = self.data.dropna()
        
        # 确保数据按时间排序
        self.data = self.data.sort_index()
        
        print(f"回测数据准备完成，共 {len(self.data)} 条记录")
        print(f"数据时间范围: {self.data.index[0]} 到 {self.data.index[-1]}")
    
    def run_backtest(self, 
                    strategy_class=None,
                    cash: float = 100000,  # 恢复到原来的10万美元
                    commission: float = 0.002,
                    exclusive_orders: bool = True) -> dict:
        """
        运行回测
        
        Args:
            strategy_class: 策略类，如果为None则使用默认的MACD策略
            cash: 初始资金
            commission: 手续费率
            exclusive_orders: 是否独占订单
            
        Returns:
            回测结果字典
        """
        try:
            # 如果没有提供策略类，使用默认的MACD策略
            if strategy_class is None:
                strategy_class = create_macd_strategy(**self.strategy_params)
            
            # 创建回测实例 - 使用FractionalBacktest支持小数交易
            bt = FractionalBacktest(
                self.data,
                strategy_class,
                cash=cash,
                commission=commission,
                exclusive_orders=exclusive_orders
            )
            
            print("开始运行回测...")
            print(f"使用策略参数: {self.strategy_params}")
            
            # 运行回测
            result = bt.run()
            # 打印回测结果
            bt.plot()
            # 转换结果为字典格式
            result_dict = {
                'Start': result['Start'],
                'End': result['End'],
                'Duration': result['Duration'],
                'Exposure Time [%]': result['Exposure Time [%]'],
                'Equity Final [$]': result['Equity Final [$]'],
                'Equity Peak [$]': result['Equity Peak [$]'],
                'Return [%]': result['Return [%]'],
                'Buy & Hold Return [%]': result['Buy & Hold Return [%]'],
                'Return (Ann.) [%]': result['Return (Ann.) [%]'],
                'Volatility (Ann.) [%]': result['Volatility (Ann.) [%]'],
                'Sharpe Ratio': result['Sharpe Ratio'],
                'Sortino Ratio': result['Sortino Ratio'],
                'Calmar Ratio': result['Calmar Ratio'],
                'Max. Drawdown [%]': result['Max. Drawdown [%]'],
                'Avg. Drawdown [%]': result['Avg. Drawdown [%]'],
                'Max. Drawdown Duration': result['Max. Drawdown Duration'],
                'Avg. Drawdown Duration': result['Avg. Drawdown Duration'],
                '# Trades': result['# Trades'],
                'Win Rate [%]': result['Win Rate [%]'],
                'Best Trade [%]': result['Best Trade [%]'],
                'Worst Trade [%]': result['Worst Trade [%]'],
                'Avg. Trade [%]': result['Avg. Trade [%]'],
                'Max. Trade Duration': result['Max. Trade Duration'],
                'Avg. Trade Duration': result['Avg. Trade Duration'],
                'Profit Factor': result['Profit Factor'],
                'Expectancy [%]': result['Expectancy [%]'],
                'SQN': result['SQN']
            }
            
            print("回测完成！")
            self._print_results(result_dict)
            
            return {
                'backtest_instance': bt,
                'results': result_dict,
                'raw_results': result,
                'strategy_params': self.strategy_params
            }
            
        except Exception as e:
            print(f"回测运行失败: {e}")
            raise
    
    def _print_results(self, results: dict):
        """打印回测结果"""
        print("\n" + "="*50)
        print("回测结果摘要")
        print("="*50)
        print(f"开始时间: {results['Start']}")
        print(f"结束时间: {results['End']}")
        print(f"回测周期: {results['Duration']}")
        print(f"最终资金: ${results['Equity Final [$]']:,.2f}")
        print(f"总收益率: {results['Return [%]']:.2f}%")
        print(f"买入持有收益率: {results['Buy & Hold Return [%]']:.2f}%")
        print(f"年化收益率: {results['Return (Ann.) [%]']:.2f}%")
        print(f"夏普比率: {results['Sharpe Ratio']:.2f}")
        print(f"最大回撤: {results['Max. Drawdown [%]']:.2f}%")
        print(f"交易次数: {results['# Trades']}")
        print(f"胜率: {results['Win Rate [%]']:.2f}%")
        print("="*50)
    
    def optimize_strategy(self, 
                         fast_range=(8, 16),
                         slow_range=(20, 30),
                         signal_range=(6, 12),
                         position_size_range=(0.5, 1.0),
                         maximize='Return [%]') -> dict:
        """
        优化策略参数 - 使用strategy.py中的策略逻辑
        
        Args:
            fast_range: 快速EMA周期范围
            slow_range: 慢速EMA周期范围
            signal_range: 信号线EMA周期范围
            position_size_range: 仓位大小范围
            maximize: 优化目标指标
            
        Returns:
            优化结果
        """
        try:
            print("开始参数优化...")
            
            # 创建用于优化的策略类
            OptimizationStrategy = create_macd_strategy()
            
            bt = FractionalBacktest(self.data, OptimizationStrategy)
            
            # 运行优化
            optimization_result = bt.optimize(
                fast_period=range(*fast_range),
                slow_period=range(*slow_range),
                signal_period=range(*signal_range),
                position_size=np.arange(*position_size_range, 0.1),
                maximize=maximize,
                constraint=lambda p: p.fast_period < p.slow_period  # 确保快线周期小于慢线周期
            )
            
            print("参数优化完成！")
            print(f"最优参数:")
            print(f"  快速EMA周期: {optimization_result._strategy.fast_period}")
            print(f"  慢速EMA周期: {optimization_result._strategy.slow_period}")
            print(f"  信号线EMA周期: {optimization_result._strategy.signal_period}")
            print(f"  仓位大小: {optimization_result._strategy.position_size}")
            print(f"  优化指标 ({maximize}): {optimization_result[maximize]:.2f}")
            
            # 更新策略参数
            self.strategy_params.update({
                'fast_period': optimization_result._strategy.fast_period,
                'slow_period': optimization_result._strategy.slow_period,
                'signal_period': optimization_result._strategy.signal_period,
                'position_size': optimization_result._strategy.position_size
            })
            
            return {
                'best_params': {
                    'fast_period': optimization_result._strategy.fast_period,
                    'slow_period': optimization_result._strategy.slow_period,
                    'signal_period': optimization_result._strategy.signal_period,
                    'position_size': optimization_result._strategy.position_size
                },
                'best_result': optimization_result,
                'optimization_target': maximize
            }
            
        except Exception as e:
            print(f"参数优化失败: {e}")
            raise


def run_simple_backtest(days: int = 90, cash: float = 10000, strategy_params: dict = None) -> dict:
    """
    运行简单回测的便捷函数 - 使用strategy.py中的策略
    
    Args:
        days: 回测数据天数
        cash: 初始资金
        strategy_params: 策略参数字典
        
    Returns:
        回测结果
    """
    # 获取数据
    data = get_bitcoin_data(days=days)
    
    # 创建回测运行器
    runner = BacktestRunner(data, strategy_params)
    
    # 运行回测
    return runner.run_backtest(cash=cash)


def optimize_macd_strategy(days: int = 90, strategy_params: dict = None) -> dict:
    """
    优化MACD策略参数的便捷函数 - 使用strategy.py中的策略
    
    Args:
        days: 回测数据天数
        strategy_params: 初始策略参数
        
    Returns:
        优化结果
    """
    # 获取数据
    data = get_bitcoin_data(days=days)
    
    # 创建回测运行器
    runner = BacktestRunner(data, strategy_params)
    
    # 运行优化
    return runner.optimize_strategy()


def compare_strategies(days: int = 90, cash: float = 10000) -> dict:
    """
    比较不同策略参数的性能
    
    Args:
        days: 回测数据天数
        cash: 初始资金
        
    Returns:
        比较结果
    """
    # 获取数据
    data = get_bitcoin_data(days=days)
    
    # 定义不同的策略参数组合
    strategy_configs = [
        {'fast_period': 12, 'slow_period': 26, 'signal_period': 9, 'position_size': 0.8},
        {'fast_period': 8, 'slow_period': 21, 'signal_period': 5, 'position_size': 0.6},
        {'fast_period': 15, 'slow_period': 30, 'signal_period': 12, 'position_size': 1.0},
    ]
    
    results = {}
    
    for i, params in enumerate(strategy_configs):
        print(f"\n运行策略配置 {i+1}: {params}")
        runner = BacktestRunner(data, params)
        result = runner.run_backtest(cash=cash)
        results[f"Strategy_{i+1}"] = {
            'params': params,
            'results': result['results']
        }
    
    return results