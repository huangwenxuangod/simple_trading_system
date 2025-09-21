# 简化量化交易系统

一个基于Python的现代化量化交易系统，集成币安数据获取、MACD策略、backtesting.py回测和Alpaca实盘交易功能。支持小数交易和完整的测试覆盖。

## 功能特性

- 🚀 **币安API数据获取**: 直接通过REST API获取比特币历史数据和实时价格
- 📊 **MACD策略**: 实现经典的MACD技术指标策略，支持参数优化
- 🔄 **回测系统**: 集成backtesting.py进行策略回测，支持FractionalBacktest小数交易
- 💰 **实盘交易**: 支持Alpaca API进行美股实盘交易
- 💾 **数据存储**: SQLite数据库存储历史数据
- 🎯 **交互界面**: 提供命令行交互界面和CLI模式
- 🧪 **完整测试**: 包含单元测试、集成测试和覆盖率报告
- 📦 **现代化包管理**: 使用pyproject.toml进行项目配置

## 项目结构

```
simple_trading_system/
├── __init__.py          # 包初始化文件
├── config.py            # 配置管理
├── data_provider.py     # 数据获取模块
├── strategy.py          # MACD策略实现
├── backtest.py          # 回测模块（支持FractionalBacktest）
├── alpaca_trader.py     # Alpaca交易模块
├── main.py              # 主程序入口
├── test_system.py       # 完整测试套件
├── pyproject.toml       # 现代化项目配置
├── .env.example         # 环境变量示例
└── .gitignore           # Git忽略文件
```

## 快速开始

### 1. 安装依赖

```bash
# 进入项目目录
cd simple_trading_system

# 安装项目及依赖
pip install -e .
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件，填入你的API密钥
# ALPACA_API_KEY=your_alpaca_api_key
# ALPACA_SECRET_KEY=your_alpaca_secret_key
```

### 3. 运行系统

#### 交互模式
```bash
python -m simple_trading_system.main
```

#### 命令行模式
```bash
# 获取数据
python -m simple_trading_system.main --mode data --days 30

# 运行回测
python -m simple_trading_system.main --mode backtest --days 90 --cash 10000

# 优化策略参数
python -m simple_trading_system.main --mode optimize --days 90
```

### 4. 编程接口使用

```python
from simple_trading_system import get_bitcoin_data, run_simple_backtest

# 获取比特币数据
df = get_bitcoin_data(days=30)
print(f"获取到 {len(df)} 条数据")

# 运行回测
result = run_simple_backtest(days=90, cash=10000)
print(f"总收益率: {result['results']['Return [%]']:.2f}%")
```

## 主要模块说明

### 数据获取 (data_provider.py)

- `BinanceDataProvider`: 币安数据提供者
  - 获取历史K线数据
  - 获取实时价格
  - 获取24小时价格统计

- `DataStorage`: 数据存储管理
  - SQLite数据库操作
  - 数据保存和加载

- `get_bitcoin_data()`: 便捷函数，获取比特币数据

### 策略实现 (strategy.py)

- `MACDStrategy`: MACD策略类
  - MACD指标计算
  - 交易信号生成
  - 策略回测

### 回测系统 (backtest.py)

- `BacktestRunner`: 回测运行器
  - 集成backtesting.py和FractionalBacktest
  - 支持小数交易和仓位管理
  - 策略回测执行和参数优化

- `create_macd_strategy()`: 创建MACD策略类
- `run_simple_backtest()`: 简单回测函数
- `optimize_macd_strategy()`: 策略参数优化

### 交易模块 (alpaca_trader.py)

- `AlpacaTrader`: Alpaca交易接口
  - 账户信息管理
  - 订单执行
  - 持仓管理

- `TradingBot`: 自动交易机器人
  - 信号执行
  - 风险管理
  - 交易记录

## 配置说明

### 环境变量

```bash
# Alpaca API配置
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # 纸上交易

# 数据库配置
DATABASE_PATH=trading_data.db

# 策略参数
MACD_FAST_PERIOD=12
MACD_SLOW_PERIOD=26
MACD_SIGNAL_PERIOD=9

# 风险管理
MAX_POSITION_SIZE=0.95
STOP_LOSS_PCT=0.05
TAKE_PROFIT_PCT=0.10
```

### 项目配置 (pyproject.toml)

项目使用现代Python包管理，支持：
- 依赖管理
- 开发工具配置
- 构建系统配置

## 测试

运行完整测试套件：

```bash
# 运行所有测试
python -m pytest test_system.py -v

# 运行测试并生成覆盖率报告
python -m pytest test_system.py -v --cov=. --cov-report=html --cov-report=term

# 查看覆盖率报告
# 报告将生成在 htmlcov/ 目录中
```

测试包括：
- ✅ **数据获取测试**: 币安API数据获取功能
- ✅ **策略计算测试**: MACD指标计算和信号生成
- ✅ **回测功能测试**: FractionalBacktest回测功能
- ✅ **交易模块测试**: Alpaca交易接口
- ✅ **集成测试**: 完整工作流程测试
- ✅ **性能测试**: 系统性能基准测试

### 测试覆盖率

当前测试覆盖率约为 **42%**，主要覆盖核心功能模块。

## API参考

### 数据获取

```python
from simple_trading_system import BinanceDataProvider, get_bitcoin_data

# 创建数据提供者
provider = BinanceDataProvider()

# 获取历史数据
data = provider.get_historical_data('BTCUSDT', '1h', start_time, end_time)

# 获取最新价格
price = provider.get_latest_price('BTCUSDT')

# 便捷函数
df = get_bitcoin_data(days=30, save_to_db=True)
```

### 策略使用

```python
from simple_trading_system import MACDStrategy

# 创建策略
strategy = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)

# 计算MACD
macd_data = strategy.calculate_macd(df)

# 生成信号
signals = strategy.generate_signals(df)
```

### 回测

```python
from simple_trading_system import run_simple_backtest, optimize_macd_strategy

# 简单回测
result = run_simple_backtest(days=90, cash=10000)

# 参数优化
best_params = optimize_macd_strategy(days=90)
```

### 交易

```python
from simple_trading_system import AlpacaTrader, TradingBot

# 创建交易者
trader = AlpacaTrader()

# 获取账户信息
account = trader.get_account_info()

# 创建交易机器人
bot = TradingBot(symbol='AAPL')

# 执行信号
bot.execute_signal(signal=1, price=150.0)  # 买入信号
```

## 注意事项

1. **API限制**: 币安API有请求频率限制，请合理使用
2. **实盘交易**: 默认使用Alpaca纸上交易，实盘交易需要修改配置
3. **数据质量**: 建议定期更新历史数据以保证回测准确性
4. **风险管理**: 实盘交易前请充分测试策略并设置合理的风险参数
5. **小数交易**: 系统支持FractionalBacktest进行小数仓位交易
6. **测试覆盖**: 建议在修改代码后运行完整测试套件

## 版本历史

### v1.0.0 (当前版本)
- ✅ 完整的MACD策略实现
- ✅ 币安数据获取集成
- ✅ FractionalBacktest回测支持
- ✅ Alpaca交易接口
- ✅ 完整测试套件
- ✅ 现代化项目配置

## 许可证

MIT License - 详见 LICENSE 文件

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/your-username/simple-trading-system.git
cd simple-trading-system

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
python -m pytest test_system.py -v

# 代码格式化
black .

# 类型检查
mypy .
```

## 联系方式

如有问题或建议，请通过以下方式联系：
- GitHub Issues
- Email: developer@example.com