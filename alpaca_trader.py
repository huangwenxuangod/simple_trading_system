"""
Alpaca交易模块
Alpaca Trading Module
"""

import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional, Dict, List
import time
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from simple_trading_system.config import config


class AlpacaTrader:
    """Alpaca交易客户端"""
    
    def __init__(self):
        """初始化Alpaca交易客户端"""
        try:
            self.api = tradeapi.REST(
                config.ALPACA_API_KEY,
                config.ALPACA_SECRET_KEY,
                config.ALPACA_BASE_URL,
                api_version='v2'
            )
            
            # 验证连接
            account = self.api.get_account()
            print(f"Alpaca账户连接成功")
            print(f"账户状态: {account.status}")
            print(f"可用资金: ${float(account.buying_power):,.2f}")
            
        except Exception as e:
            print(f"Alpaca API初始化失败: {e}")
            raise
    
    def get_account_info(self) -> Dict:
        """获取账户信息"""
        try:
            account = self.api.get_account()
            return {
                'account_id': account.id,
                'status': account.status,
                'equity': float(account.equity),
                'buying_power': float(account.buying_power),
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'day_trade_count': account.daytrade_count,
                'pattern_day_trader': account.pattern_day_trader
            }
        except Exception as e:
            print(f"获取账户信息失败: {e}")
            raise
    
    def get_positions(self) -> List[Dict]:
        """获取当前持仓"""
        try:
            positions = self.api.list_positions()
            result = []
            
            for position in positions:
                result.append({
                    'symbol': position.symbol,
                    'qty': float(position.qty),
                    'market_value': float(position.market_value),
                    'cost_basis': float(position.cost_basis),
                    'unrealized_pl': float(position.unrealized_pl),
                    'unrealized_plpc': float(position.unrealized_plpc),
                    'current_price': float(position.current_price),
                    'avg_entry_price': float(position.avg_entry_price)
                })
            
            return result
            
        except Exception as e:
            print(f"获取持仓信息失败: {e}")
            raise
    
    def place_order(self, 
                   symbol: str,
                   qty: float,
                   side: str,
                   order_type: str = 'market',
                   time_in_force: str = 'gtc',
                   limit_price: Optional[float] = None,
                   stop_price: Optional[float] = None) -> Dict:
        """
        下单
        
        Args:
            symbol: 股票代码
            qty: 数量
            side: 'buy' 或 'sell'
            order_type: 'market', 'limit', 'stop', 'stop_limit'
            time_in_force: 'day', 'gtc', 'ioc', 'fok'
            limit_price: 限价单价格
            stop_price: 止损单价格
            
        Returns:
            订单信息字典
        """
        try:
            # 构建订单参数
            order_params = {
                'symbol': symbol,
                'qty': qty,
                'side': side,
                'type': order_type,
                'time_in_force': time_in_force
            }
            
            if limit_price:
                order_params['limit_price'] = limit_price
            
            if stop_price:
                order_params['stop_price'] = stop_price
            
            # 提交订单
            order = self.api.submit_order(**order_params)
            
            print(f"订单提交成功: {side.upper()} {qty} {symbol} @ {order_type}")
            
            return {
                'order_id': order.id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side,
                'order_type': order.order_type,
                'status': order.status,
                'submitted_at': order.submitted_at,
                'filled_qty': float(order.filled_qty or 0),
                'filled_avg_price': float(order.filled_avg_price or 0)
            }
            
        except Exception as e:
            print(f"下单失败: {e}")
            raise
    
    def buy_market(self, symbol: str, qty: float) -> Dict:
        """市价买入"""
        return self.place_order(symbol, qty, 'buy', 'market')
    
    def sell_market(self, symbol: str, qty: float) -> Dict:
        """市价卖出"""
        return self.place_order(symbol, qty, 'sell', 'market')
    
    def buy_limit(self, symbol: str, qty: float, limit_price: float) -> Dict:
        """限价买入"""
        return self.place_order(symbol, qty, 'buy', 'limit', limit_price=limit_price)
    
    def sell_limit(self, symbol: str, qty: float, limit_price: float) -> Dict:
        """限价卖出"""
        return self.place_order(symbol, qty, 'sell', 'limit', limit_price=limit_price)
    
    def get_orders(self, status: str = 'all', limit: int = 50) -> List[Dict]:
        """
        获取订单列表
        
        Args:
            status: 'open', 'closed', 'all'
            limit: 返回订单数量限制
            
        Returns:
            订单列表
        """
        try:
            orders = self.api.list_orders(status=status, limit=limit)
            result = []
            
            for order in orders:
                result.append({
                    'order_id': order.id,
                    'symbol': order.symbol,
                    'qty': float(order.qty),
                    'side': order.side,
                    'order_type': order.order_type,
                    'status': order.status,
                    'submitted_at': order.submitted_at,
                    'filled_at': order.filled_at,
                    'filled_qty': float(order.filled_qty or 0),
                    'filled_avg_price': float(order.filled_avg_price or 0),
                    'limit_price': float(order.limit_price or 0),
                    'stop_price': float(order.stop_price or 0)
                })
            
            return result
            
        except Exception as e:
            print(f"获取订单列表失败: {e}")
            raise
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        try:
            self.api.cancel_order(order_id)
            print(f"订单 {order_id} 已取消")
            return True
        except Exception as e:
            print(f"取消订单失败: {e}")
            return False
    
    def cancel_all_orders(self) -> bool:
        """取消所有未成交订单"""
        try:
            self.api.cancel_all_orders()
            print("所有未成交订单已取消")
            return True
        except Exception as e:
            print(f"取消所有订单失败: {e}")
            return False
    
    def get_portfolio_history(self, period: str = '1M') -> Dict:
        """
        获取投资组合历史
        
        Args:
            period: '1D', '7D', '1M', '3M', '1A', '2A', '5A'
            
        Returns:
            投资组合历史数据
        """
        try:
            portfolio = self.api.get_portfolio_history(period=period)
            
            return {
                'timestamp': portfolio.timestamp,
                'equity': portfolio.equity,
                'profit_loss': portfolio.profit_loss,
                'profit_loss_pct': portfolio.profit_loss_pct,
                'base_value': portfolio.base_value,
                'timeframe': portfolio.timeframe
            }
            
        except Exception as e:
            print(f"获取投资组合历史失败: {e}")
            raise
    
    def get_market_data(self, symbol: str, timeframe: str = '1Day', limit: int = 100) -> pd.DataFrame:
        """
        获取市场数据
        
        Args:
            symbol: 股票代码
            timeframe: '1Min', '5Min', '15Min', '1Hour', '1Day'
            limit: 数据条数
            
        Returns:
            价格数据DataFrame
        """
        try:
            # 计算开始时间
            end_time = datetime.now()
            if timeframe == '1Min':
                start_time = end_time - timedelta(minutes=limit)
            elif timeframe == '5Min':
                start_time = end_time - timedelta(minutes=limit * 5)
            elif timeframe == '15Min':
                start_time = end_time - timedelta(minutes=limit * 15)
            elif timeframe == '1Hour':
                start_time = end_time - timedelta(hours=limit)
            else:  # 1Day
                start_time = end_time - timedelta(days=limit)
            
            # 获取数据
            bars = self.api.get_bars(
                symbol,
                timeframe,
                start=start_time.isoformat(),
                end=end_time.isoformat(),
                limit=limit
            ).df
            
            # 重命名列以匹配标准格式
            bars.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'TradeCount', 'VWAP']
            bars = bars[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            return bars
            
        except Exception as e:
            print(f"获取市场数据失败: {e}")
            raise


class TradingBot:
    """自动交易机器人"""
    
    def __init__(self, symbol: str = "AAPL"):
        """
        初始化交易机器人
        
        Args:
            symbol: 交易标的
        """
        self.trader = AlpacaTrader()
        self.symbol = symbol
        self.position = 0  # 当前持仓数量
        self.last_signal = None
        self.trade_history = []
    
    def update_position(self):
        """更新当前持仓"""
        try:
            positions = self.trader.get_positions()
            self.position = 0
            
            for pos in positions:
                if pos['symbol'] == self.symbol:
                    self.position = pos['qty']
                    break
                    
        except Exception as e:
            print(f"更新持仓失败: {e}")
    
    def execute_signal(self, signal: int, price: float = None):
        """
        执行交易信号
        
        Args:
            signal: 1=买入, -1=卖出, 0=无操作
            price: 当前价格（用于记录）
        """
        try:
            self.update_position()
            
            if signal == 1 and self.position <= 0:  # 买入信号且无多头持仓
                # 计算买入数量（使用可用资金的90%）
                account = self.trader.get_account_info()
                available_cash = account['buying_power'] * 0.9
                
                if price:
                    qty = int(available_cash / price)
                else:
                    # 使用市价单，数量基于可用资金
                    qty = int(available_cash / 100)  # 假设股价约100美元
                
                if qty > 0:
                    order = self.trader.buy_market(self.symbol, qty)
                    self.trade_history.append({
                        'timestamp': datetime.now(),
                        'action': 'BUY',
                        'symbol': self.symbol,
                        'qty': qty,
                        'order_id': order['order_id'],
                        'signal_price': price
                    })
                    print(f"执行买入: {qty} 股 {self.symbol}")
            
            elif signal == -1 and self.position > 0:  # 卖出信号且有多头持仓
                order = self.trader.sell_market(self.symbol, abs(self.position))
                self.trade_history.append({
                    'timestamp': datetime.now(),
                    'action': 'SELL',
                    'symbol': self.symbol,
                    'qty': abs(self.position),
                    'order_id': order['order_id'],
                    'signal_price': price
                })
                print(f"执行卖出: {abs(self.position)} 股 {self.symbol}")
            
            self.last_signal = signal
            
        except Exception as e:
            print(f"执行交易信号失败: {e}")
    
    def get_trade_summary(self) -> Dict:
        """获取交易摘要"""
        if not self.trade_history:
            return {'total_trades': 0}
        
        buy_trades = [t for t in self.trade_history if t['action'] == 'BUY']
        sell_trades = [t for t in self.trade_history if t['action'] == 'SELL']
        
        return {
            'total_trades': len(self.trade_history),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'current_position': self.position,
            'last_signal': self.last_signal,
            'trade_history': self.trade_history
        }