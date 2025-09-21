"""
简化量化交易系统主程序
Simple Trading System Main Program
"""

import argparse
import sys
from datetime import datetime
import pandas as pd
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from simple_trading_system.config import config
from simple_trading_system.data_provider import get_bitcoin_data, BinanceDataProvider, DataStorage
from simple_trading_system.strategy import MACDStrategy
from simple_trading_system.backtest import run_simple_backtest, optimize_macd_strategy, BacktestRunner
from simple_trading_system.alpaca_trader import AlpacaTrader, TradingBot


def show_menu():
    """显示主菜单"""
    print("\n" + "="*60)
    print("简化量化交易系统")
    print("Simple Trading System")
    print("="*60)
    print("1. 获取比特币数据")
    print("2. 运行MACD策略回测")
    print("3. 优化MACD策略参数")
    print("4. 查看Alpaca账户信息")
    print("5. 实时交易模式")
    print("6. 数据分析")
    print("0. 退出")
    print("="*60)


def get_bitcoin_data_menu():
    """获取比特币数据菜单"""
    print("\n获取比特币数据")
    print("-" * 30)
    
    try:
        days = int(input("请输入获取天数 (默认30天): ") or "30")
        
        print(f"正在获取最近 {days} 天的比特币数据...")
        df = get_bitcoin_data(days=days, save_to_db=True)
        
        print(f"\n数据获取成功！")
        print(f"数据条数: {len(df)}")
        print(f"时间范围: {df.index[0]} 到 {df.index[-1]}")
        print(f"最新价格: ${df['Close'].iloc[-1]:,.2f}")
        print(f"最高价格: ${df['High'].max():,.2f}")
        print(f"最低价格: ${df['Low'].min():,.2f}")
        
        # 显示最近5条数据
        print(f"\n最近5条数据:")
        print(df.tail().round(2))
        
    except Exception as e:
        print(f"获取数据失败: {e}")


def run_backtest_menu():
    """运行回测菜单"""
    print("\n运行MACD策略回测")
    print("-" * 30)
    
    try:
        days = int(input("请输入回测天数 (默认90天): ") or "90")
        cash = float(input("请输入初始资金 (默认10000): ") or "10000")
        
        print(f"正在运行回测...")
        result = run_simple_backtest(days=days, cash=cash)
        
        print("\n回测完成！详细结果已显示在上方。")
        
        # 询问是否保存结果
        save = input("\n是否保存回测结果到文件? (y/n): ").lower()
        if save == 'y':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_result_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("MACD策略回测结果\n")
                f.write("="*50 + "\n")
                for key, value in result['results'].items():
                    f.write(f"{key}: {value}\n")
            
            print(f"回测结果已保存到: {filename}")
        
    except Exception as e:
        print(f"回测失败: {e}")


def optimize_strategy_menu():
    """优化策略菜单"""
    print("\n优化MACD策略参数")
    print("-" * 30)
    
    try:
        days = int(input("请输入优化数据天数 (默认90天): ") or "90")
        
        print("正在进行参数优化，这可能需要几分钟...")
        result = optimize_macd_strategy(days=days)
        
        print("\n参数优化完成！")
        print("最优参数组合:")
        for param, value in result['best_params'].items():
            print(f"  {param}: {value}")
        
    except Exception as e:
        print(f"参数优化失败: {e}")


def alpaca_account_menu():
    """Alpaca账户信息菜单"""
    print("\nAlpaca账户信息")
    print("-" * 30)
    
    try:
        trader = AlpacaTrader()
        
        # 获取账户信息
        account = trader.get_account_info()
        print(f"账户ID: {account['account_id']}")
        print(f"账户状态: {account['status']}")
        print(f"总资产: ${account['equity']:,.2f}")
        print(f"可用资金: ${account['buying_power']:,.2f}")
        print(f"现金: ${account['cash']:,.2f}")
        print(f"投资组合价值: ${account['portfolio_value']:,.2f}")
        
        # 获取持仓
        positions = trader.get_positions()
        if positions:
            print(f"\n当前持仓:")
            for pos in positions:
                print(f"  {pos['symbol']}: {pos['qty']} 股, 市值: ${pos['market_value']:,.2f}")
        else:
            print("\n当前无持仓")
        
        # 获取最近订单
        orders = trader.get_orders(limit=5)
        if orders:
            print(f"\n最近5个订单:")
            for order in orders:
                print(f"  {order['symbol']} {order['side']} {order['qty']} @ {order['status']}")
        
    except Exception as e:
        print(f"获取账户信息失败: {e}")


def live_trading_menu():
    """实时交易菜单"""
    print("\n实时交易模式")
    print("-" * 30)
    print("警告: 这是实盘交易模式，请谨慎操作！")
    
    confirm = input("确认进入实时交易模式? (yes/no): ").lower()
    if confirm != 'yes':
        print("已取消实时交易模式")
        return
    
    try:
        symbol = input("请输入交易标的 (默认AAPL): ") or "AAPL"
        
        # 创建交易机器人
        bot = TradingBot(symbol=symbol)
        
        print(f"交易机器人已启动，监控标的: {symbol}")
        print("按 Ctrl+C 停止交易")
        
        # 获取历史数据用于策略计算
        trader = AlpacaTrader()
        data = trader.get_market_data(symbol, timeframe='1Hour', limit=100)
        
        # 创建策略实例
        strategy = MACDStrategy()
        
        print("开始实时监控...")
        
        import time
        while True:
            try:
                # 获取最新数据
                current_data = trader.get_market_data(symbol, timeframe='1Hour', limit=50)
                
                # 生成信号
                signals_df = strategy.generate_signals(current_data)
                latest_signal = signals_df['Signal'].iloc[-1]
                current_price = current_data['Close'].iloc[-1]
                
                if latest_signal != 0:
                    print(f"检测到信号: {latest_signal} @ ${current_price:.2f}")
                    bot.execute_signal(latest_signal, current_price)
                
                # 等待5分钟
                time.sleep(300)
                
            except KeyboardInterrupt:
                print("\n交易已停止")
                break
            except Exception as e:
                print(f"交易过程中出错: {e}")
                time.sleep(60)  # 出错后等待1分钟再继续
        
        # 显示交易摘要
        summary = bot.get_trade_summary()
        print(f"\n交易摘要:")
        print(f"总交易次数: {summary['total_trades']}")
        print(f"当前持仓: {summary['current_position']}")
        
    except Exception as e:
        print(f"实时交易失败: {e}")


def data_analysis_menu():
    """数据分析菜单"""
    print("\n数据分析")
    print("-" * 30)
    
    try:
        # 从数据库加载数据
        storage = DataStorage()
        df = storage.load_data(config.SYMBOL)
        
        if df.empty:
            print("数据库中没有数据，请先获取数据")
            return
        
        print(f"数据分析 - {config.SYMBOL}")
        print(f"数据条数: {len(df)}")
        print(f"时间范围: {df.index[0]} 到 {df.index[-1]}")
        
        # 基本统计
        print(f"\n价格统计:")
        print(f"当前价格: ${df['Close'].iloc[-1]:,.2f}")
        print(f"最高价格: ${df['High'].max():,.2f}")
        print(f"最低价格: ${df['Low'].min():,.2f}")
        print(f"平均价格: ${df['Close'].mean():,.2f}")
        print(f"价格标准差: ${df['Close'].std():,.2f}")
        
        # 计算收益率
        returns = df['Close'].pct_change().dropna()
        print(f"\n收益率统计:")
        print(f"平均日收益率: {returns.mean():.4f} ({returns.mean()*100:.2f}%)")
        print(f"收益率标准差: {returns.std():.4f} ({returns.std()*100:.2f}%)")
        print(f"最大单日涨幅: {returns.max():.4f} ({returns.max()*100:.2f}%)")
        print(f"最大单日跌幅: {returns.min():.4f} ({returns.min()*100:.2f}%)")
        
        # MACD分析
        strategy = MACDStrategy()
        signals_df = strategy.generate_signals(df)
        
        buy_signals = len(signals_df[signals_df['Signal'] == 1])
        sell_signals = len(signals_df[signals_df['Signal'] == -1])
        
        print(f"\nMACD信号统计:")
        print(f"买入信号: {buy_signals} 次")
        print(f"卖出信号: {sell_signals} 次")
        
        # 显示最近的信号
        recent_signals = signals_df[signals_df['Signal'] != 0].tail(5)
        if not recent_signals.empty:
            print(f"\n最近5个交易信号:")
            for idx, row in recent_signals.iterrows():
                signal_type = "买入" if row['Signal'] == 1 else "卖出"
                print(f"  {idx.strftime('%Y-%m-%d %H:%M')} - {signal_type} @ ${row['Close']:.2f}")
        
    except Exception as e:
        print(f"数据分析失败: {e}")


def main():
    """主程序入口"""
    print("欢迎使用简化量化交易系统！")
    
    while True:
        try:
            show_menu()
            choice = input("\n请选择操作 (0-6): ").strip()
            
            if choice == '0':
                print("感谢使用，再见！")
                break
            elif choice == '1':
                get_bitcoin_data_menu()
            elif choice == '2':
                run_backtest_menu()
            elif choice == '3':
                optimize_strategy_menu()
            elif choice == '4':
                alpaca_account_menu()
            elif choice == '5':
                live_trading_menu()
            elif choice == '6':
                data_analysis_menu()
            else:
                print("无效选择，请重新输入")
            
            input("\n按回车键继续...")
            
        except KeyboardInterrupt:
            print("\n\n程序已中断，再见！")
            break
        except Exception as e:
            print(f"程序出错: {e}")
            input("按回车键继续...")


def cli_main():
    """命令行接口"""
    parser = argparse.ArgumentParser(description='简化量化交易系统')
    parser.add_argument('--mode', choices=['data', 'backtest', 'optimize', 'live'], 
                       help='运行模式')
    parser.add_argument('--days', type=int, default=30, help='数据天数')
    parser.add_argument('--cash', type=float, default=10000, help='初始资金')
    parser.add_argument('--symbol', default='AAPL', help='交易标的')
    
    args = parser.parse_args()
    
    if args.mode == 'data':
        print(f"获取 {args.days} 天的比特币数据...")
        df = get_bitcoin_data(days=args.days)
        print(f"数据获取完成，共 {len(df)} 条记录")
        
    elif args.mode == 'backtest':
        print(f"运行 {args.days} 天回测，初始资金 ${args.cash}")
        result = run_simple_backtest(days=args.days, cash=args.cash)
        
    elif args.mode == 'optimize':
        print(f"优化策略参数，使用 {args.days} 天数据")
        result = optimize_macd_strategy(days=args.days)
        
    elif args.mode == 'live':
        print(f"启动实时交易模式，标的: {args.symbol}")
        bot = TradingBot(symbol=args.symbol)
        print("实时交易模式需要在交互模式下运行")
        
    else:
        # 默认启动交互模式
        main()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli_main()
    else:
        main()