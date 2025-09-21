"""
系统测试模块
System Testing Module
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from simple_trading_system.data_provider import BinanceDataProvider, DataStorage, get_bitcoin_data
from simple_trading_system.strategy import MACDStrategy
from simple_trading_system.backtest import BacktestRunner, run_simple_backtest
from simple_trading_system.config import config


class TestDataProvider(unittest.TestCase):
    """数据提供者测试"""
    
    def setUp(self):
        """测试设置"""
        self.provider = BinanceDataProvider()
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.storage = DataStorage(self.temp_db.name)
    
    def tearDown(self):
        """清理测试环境"""
        try:
            if hasattr(self, 'temp_db'):
                # 关闭数据库连接
                if hasattr(self.storage, 'db_path'):
                    import sqlite3
                    # 强制关闭所有连接
                    try:
                        conn = sqlite3.connect(self.temp_db.name)
                        conn.close()
                    except:
                        pass
                
                # 删除临时文件
                import time
                time.sleep(0.1)  # 短暂等待
                try:
                    os.unlink(self.temp_db.name)
                except PermissionError:
                    # 如果文件被占用，跳过删除
                    pass
        except Exception:
            pass
    
    def test_get_historical_data(self):
        """测试获取历史数据"""
        try:
            # 获取最近7天的数据
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
            
            data = self.provider.get_historical_data(
                symbol='BTCUSDT',
                interval='1h',
                start_time=start_time,
                end_time=end_time
            )
            
            self.assertIsInstance(data, pd.DataFrame)
            self.assertGreater(len(data), 0)
            self.assertIn('Close', data.columns)
            self.assertIn('Volume', data.columns)
            
            print(f"✓ 历史数据测试通过，获取到 {len(data)} 条数据")
            
        except Exception as e:
            print(f"✗ 历史数据测试失败: {e}")
            self.fail(f"获取历史数据失败: {e}")
    
    def test_get_latest_price(self):
        """测试获取最新价格"""
        try:
            price = self.provider.get_latest_price('BTCUSDT')
            
            self.assertIsInstance(price, float)
            self.assertGreater(price, 0)
            
            print(f"✓ 最新价格测试通过，当前价格: ${price:,.2f}")
            
        except Exception as e:
            print(f"✗ 最新价格测试失败: {e}")
            self.fail(f"获取最新价格失败: {e}")
    
    def test_data_storage(self):
        """测试数据存储"""
        try:
            # 创建测试数据
            dates = pd.date_range(start='2023-01-01', periods=100, freq='H')
            test_data = pd.DataFrame({
                'Open': np.random.uniform(40000, 50000, 100),
                'High': np.random.uniform(50000, 60000, 100),
                'Low': np.random.uniform(30000, 40000, 100),
                'Close': np.random.uniform(40000, 50000, 100),
                'Volume': np.random.uniform(1000, 10000, 100)
            }, index=dates)
            
            # 测试保存数据
            self.storage.save_data(test_data, 'TEST')
            
            # 测试加载数据
            loaded_data = self.storage.load_data('TEST')
            
            self.assertIsInstance(loaded_data, pd.DataFrame)
            self.assertEqual(len(loaded_data), len(test_data))
            
            print(f"✓ 数据存储测试通过，保存并加载了 {len(loaded_data)} 条数据")
            
        except Exception as e:
            print(f"✗ 数据存储测试失败: {e}")
            self.fail(f"数据存储失败: {e}")


class TestMACDStrategy(unittest.TestCase):
    """MACD策略测试"""
    
    def setUp(self):
        """测试设置"""
        self.strategy = MACDStrategy()
        
        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        np.random.seed(42)  # 固定随机种子
        
        # 生成趋势数据
        trend = np.cumsum(np.random.normal(0, 1, 100)) * 100 + 45000
        noise = np.random.normal(0, 500, 100)
        prices = trend + noise
        
        self.test_data = pd.DataFrame({
            'Open': prices * 0.999,
            'High': prices * 1.002,
            'Low': prices * 0.998,
            'Close': prices,
            'Volume': np.random.uniform(1000, 10000, 100)
        }, index=dates)
    
    def test_calculate_macd(self):
        """测试MACD计算"""
        try:
            # 传递Close价格序列而不是整个DataFrame
            macd_line, signal_line, histogram = self.strategy.calculate_macd(self.test_data['Close'])
            
            self.assertIsInstance(macd_line, pd.Series)
            self.assertIsInstance(signal_line, pd.Series)
            self.assertIsInstance(histogram, pd.Series)
            
            # 检查数据完整性
            self.assertEqual(len(macd_line), len(self.test_data))
            
            print(f"✓ MACD计算测试通过")
            
        except Exception as e:
            print(f"✗ MACD计算测试失败: {e}")
            self.fail(f"MACD计算失败: {e}")
    
    def test_generate_signals(self):
        """测试信号生成"""
        try:
            signals = self.strategy.generate_signals(self.test_data)
            
            self.assertIsInstance(signals, pd.DataFrame)
            self.assertIn('Signal', signals.columns)
            
            # 检查信号值
            unique_signals = signals['Signal'].unique()
            for signal in unique_signals:
                self.assertIn(signal, [-1, 0, 1])
            
            # 统计信号
            buy_signals = len(signals[signals['Signal'] == 1])
            sell_signals = len(signals[signals['Signal'] == -1])
            
            print(f"✓ 信号生成测试通过，买入信号: {buy_signals}, 卖出信号: {sell_signals}")
            
        except Exception as e:
            print(f"✗ 信号生成测试失败: {e}")
            self.fail(f"信号生成失败: {e}")


class TestBacktesting(unittest.TestCase):
    """回测测试"""
    
    def setUp(self):
        """测试设置"""
        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        # 生成有趋势的价格数据
        trend = np.linspace(45000, 50000, 100)
        noise = np.random.normal(0, 500, 100)
        prices = trend + noise
        
        self.test_data = pd.DataFrame({
            'Open': prices * 0.999,
            'High': prices * 1.002,
            'Low': prices * 0.998,
            'Close': prices,
            'Volume': np.random.uniform(1000, 10000, 100)
        }, index=dates)
    
    def test_backtest_runner(self):
        """测试回测运行器"""
        try:
            runner = BacktestRunner(self.test_data)
            
            # 运行回测
            result = runner.run_backtest(
                cash=10000,
                commission=0.002
            )
            
            self.assertIsInstance(result, dict)
            self.assertIn('results', result)
            self.assertIn('backtest_instance', result)
            
            # 检查关键指标
            results = result['results']
            self.assertIn('Return [%]', results)
            self.assertIn('Max. Drawdown [%]', results)
            
            print(f"✓ 回测运行器测试通过")
            print(f"  总收益率: {results.get('Return [%]', 'N/A'):.2f}%")
            print(f"  最大回撤: {results.get('Max. Drawdown [%]', 'N/A'):.2f}%")
            
        except Exception as e:
            print(f"✗ 回测运行器测试失败: {e}")
            self.fail(f"回测运行器失败: {e}")


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        print("\n开始完整工作流程测试...")
        
        try:
            # 1. 获取数据
            print("1. 获取比特币数据...")
            df = get_bitcoin_data(days=7, save_to_db=False)
            self.assertIsInstance(df, pd.DataFrame)
            self.assertGreater(len(df), 0)
            print(f"   ✓ 获取到 {len(df)} 条数据")
            
            # 2. 生成信号
            print("2. 生成MACD信号...")
            strategy = MACDStrategy()
            signals = strategy.generate_signals(df)
            
            buy_signals = len(signals[signals['Signal'] == 1])
            sell_signals = len(signals[signals['Signal'] == -1])
            print(f"   ✓ 买入信号: {buy_signals}, 卖出信号: {sell_signals}")
            
            # 3. 运行回测
            print("3. 运行回测...")
            result = run_simple_backtest(days=7, cash=10000)
            self.assertIsInstance(result, dict)
            print(f"   ✓ 回测完成")
            
            print("✓ 完整工作流程测试通过")
            
        except Exception as e:
            print(f"✗ 完整工作流程测试失败: {e}")
            self.fail(f"完整工作流程失败: {e}")


def run_performance_test():
    """性能测试"""
    print("\n" + "="*50)
    print("性能测试")
    print("="*50)
    
    import time
    
    # 测试数据获取性能
    print("测试数据获取性能...")
    start_time = time.time()
    try:
        df = get_bitcoin_data(days=30, save_to_db=False)
        end_time = time.time()
        print(f"✓ 获取30天数据耗时: {end_time - start_time:.2f}秒")
        print(f"  数据量: {len(df)} 条")
    except Exception as e:
        print(f"✗ 数据获取性能测试失败: {e}")
    
    # 测试策略计算性能
    print("\n测试策略计算性能...")
    if 'df' in locals() and not df.empty:
        start_time = time.time()
        try:
            strategy = MACDStrategy()
            signals = strategy.generate_signals(df)
            end_time = time.time()
            print(f"✓ MACD策略计算耗时: {end_time - start_time:.4f}秒")
            print(f"  处理数据量: {len(df)} 条")
        except Exception as e:
            print(f"✗ 策略计算性能测试失败: {e}")


def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("简化量化交易系统 - 测试套件")
    print("="*60)
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_suite.addTest(unittest.makeSuite(TestDataProvider))
    test_suite.addTest(unittest.makeSuite(TestMACDStrategy))
    test_suite.addTest(unittest.makeSuite(TestBacktesting))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 运行性能测试
    run_performance_test()
    
    # 测试总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n成功率: {success_rate:.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)