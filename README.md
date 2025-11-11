# German30 Trading Strategy Simulator

A professional Flask-based web application for practicing German30 (DAX) trading strategies with historical data replay, multi-timeframe analysis, and comprehensive performance tracking.

![German30 Simulator](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey)

## Overview

This simulator helps traders perfect their German30 (DAX) trading strategy by replaying historical price action candle-by-candle. Practice your decision-making with real market data in a risk-free environment.

### Key Features

- **Multi-Timeframe Analysis**: Simultaneous view of 4H, 1H, and 3-minute charts
- **Progressive Replay**: Reveal candles one by one to practice real-time decision-making
- **Strategy-Focused**: Locked to Mon/Thu/Fri trading days with specific time windows
- **Automatic Risk Management**: Fixed 18-point SL and 54-point TP (1:3 RR) auto-calculated
- **Drawing Tools**: Mark support/resistance, order blocks, and key levels
- **Performance Tracking**: Comprehensive statistics, trade journal, and win rate analysis
- **A-Grade Setup Tracking**: Track quality of your trade setups

## Trading Rules

The simulator enforces your specific trading strategy rules:

- **Valid Trading Days**: Monday, Thursday, Friday only
- **Time Windows** (BST/GMT+1):
  - Morning 1: 08:06 - 08:23
  - Morning 2: 09:06 - 09:23
  - Afternoon 1: 14:30 - 14:45
  - Afternoon 2: 15:06 - 15:23
- **Stop Loss**: Fixed 18 points
- **Take Profit**: 54 points (1:3 Risk-Reward Ratio)

## Installation

### Prerequisites

- Python 3.10 or higher
- Git
- Internet connection (for fetching historical data)

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/nomaan02/trading-simulator.git
   cd trading-simulator
   ```

2. **Run the application** (Windows):
   ```bash
   run.bat
   ```

   Or manually:
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac

   # Install dependencies
   pip install -r requirements.txt

   # Run the app
   python app.py
   ```

3. **Access the application**:
   - Open your browser and navigate to `http://localhost:5000`

## Usage Guide

### 1. Create a Practice Session

1. Navigate to the Simulator page
2. Select your date range (start and end dates)
3. Choose a time window
4. Click "Generate Playlist"
5. The system will filter and load valid trading days

### 2. Analyze Price Action

- **4H Chart**: View the overall trend and bias
- **1H Chart**: Identify order blocks and structure
- **3M Chart**: Find precise entry signals

### 3. Replay Controls

- **Play**: Auto-advance candles at selected speed (1x, 2x, 5x, 10x)
- **Pause**: Stop auto-replay
- **Next**: Manually reveal the next candle

### 4. Enter Trades

1. Analyze the setup using all three timeframes
2. Click "Enter Long" or "Enter Short"
3. Add trade notes describing your reasoning
4. Check A-Grade criteria if applicable:
   - ✓ 4H bias aligned
   - ✓ 1H order block confirmed
   - ✓ 3-min entry signal clear
   - ✓ Valid time window
5. The system automatically calculates SL and TP
6. Trade outcome is determined instantly

### 5. Review Statistics

- Navigate to the Statistics page to view:
  - Overall win rate and P&L
  - Trade-by-trade journal
  - Performance by time window
  - A-Grade setup accuracy

## Project Structure

```
trading-sim-ger30/
├── app.py                    # Main Flask application
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── run.bat                   # Windows run script
├── data/
│   ├── fetcher.py            # Data acquisition from yfinance
│   └── processor.py          # Data filtering and processing
├── models/
│   ├── candle.py             # Candle data model
│   ├── session.py            # Practice session model
│   └── trade.py              # Trade record model
├── routes/
│   ├── api.py                # REST API endpoints
│   └── views.py              # Page routes
├── static/
│   ├── css/
│   │   ├── main.css          # Main stylesheet
│   │   └── chart.css         # Chart styles
│   └── js/
│       ├── chart.js          # Lightweight Charts integration
│       ├── replay.js         # Replay engine
│       ├── trade-entry.js    # Trade management
│       └── stats.js          # Statistics display
└── templates/
    ├── base.html             # Base template
    ├── index.html            # Landing page
    ├── simulator.html        # Main simulator interface
    └── stats.html            # Statistics dashboard
```

## API Documentation

### Core Endpoints

- `GET /api/available-dates` - Get valid trading dates
- `POST /api/session/start` - Create practice session
- `GET /api/candles` - Get candle data for replay
- `POST /api/trade/enter` - Enter a trade
- `GET /api/trade/<id>/outcome` - Get trade outcome
- `GET /api/session/<id>/stats` - Get session statistics

## Technical Stack

- **Backend**: Flask (Python 3.10+)
- **Database**: SQLite with SQLAlchemy ORM
- **Data Source**: yfinance (Yahoo Finance)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Charting**: Lightweight Charts (TradingView library)
- **Timezone**: All data stored in UTC, displayed in BST (GMT+1)

## Data Management

### Data Caching

- Historical data is cached in SQLite database (`data/cache.db`)
- Reduces API calls to Yahoo Finance
- Cache expires after 30 days

### Data Sources

- Primary: yfinance (Yahoo Finance)
- Symbol: ^GDAXI (DAX index)
- Resolution: 1-minute bars, resampled to 3-minute

## Configuration

Edit `config.py` to customize:

- Trading rules (SL, TP, valid days)
- Time windows
- Data source settings
- UI configuration

## Troubleshooting

### Common Issues

**Data not loading**:
- Check internet connection
- Yahoo Finance API may be temporarily unavailable
- Try a different date range

**Charts not displaying**:
- Ensure JavaScript is enabled
- Check browser console for errors
- Try refreshing the page

**Database errors**:
- Delete `data/cache.db` to reset database
- Restart the application

## Development

### Running in Debug Mode

```python
# In app.py, set:
app.run(debug=True)
```

### Adding New Features

1. Backend changes: Modify models, routes, or data processors
2. Frontend changes: Edit templates or JavaScript files
3. Styling: Update CSS in `static/css/`

## Contributing

This is a personal project, but suggestions and improvements are welcome!

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your fork
5. Submit a pull request

## License

This project is for personal use and educational purposes.

## Acknowledgments

- TradingView for Lightweight Charts library
- Yahoo Finance for historical data
- Flask community for excellent documentation

## Contact

- GitHub: [@nomaan02](https://github.com/nomaan02)
- Repository: [trading-simulator](https://github.com/nomaan02/trading-simulator)

---

**Disclaimer**: This simulator is for practice and educational purposes only. Past performance does not guarantee future results. Always practice proper risk management when trading live markets.

## Roadmap

Future enhancements being considered:

- [ ] Pattern recognition helper
- [ ] Trade performance heatmaps
- [ ] Export reports to PDF
- [ ] Multi-user support
- [ ] Cloud deployment
- [ ] Mobile-responsive design
- [ ] Additional data sources (OANDA, Alpha Vantage)
- [ ] Advanced drawing tools
- [ ] Trade replay feature

## Version History

### v1.0.0 (Current)
- Initial release
- Core simulation functionality
- Multi-timeframe charts
- Trade entry and outcome determination
- Statistics tracking
- SQLite data caching

---

Made with ❤️ for serious German30 traders
