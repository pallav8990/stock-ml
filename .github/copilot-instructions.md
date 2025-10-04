# Stock-ML Copilot Instructions

## Architecture Overview
This is a **time-series ML pipeline** for NSE stock analysis (educational/analysis-only). The system follows a strict linear data flow:
1. **Data Collection** → 2. **Feature Engineering** → 3. **Model Training** → 4. **Prediction** → 5. **Evaluation**

### Key Components
- **Pipeline scripts** (`pipeline/`): Sequential daily data processing chain
- **API endpoints** (`app/serve.py`): Read-only access to predictions and evaluations
- **Scheduler** (`pipeline/scheduler.py`): IST-based cron automation
- **Data store**: Parquet files in `data/` directory (created at runtime)

## Critical Patterns

### Data Flow Dependencies
Pipeline scripts **must run in sequence**:
```bash
build_universe.py → collect_prices_nse.py → collect_news.py → 
build_features.py → train_model.py → predict.py → evaluate_and_explain.py
```
Each step depends on parquet outputs from previous steps. Never modify this order.

### File Naming Convention
All data files follow `{purpose}_daily.parquet` pattern:
- `prices_daily.parquet` - NSE bhavcopy data
- `news_daily.parquet` - RSS sentiment scores  
- `features_daily.parquet` - Technical indicators + news features
- `predictions_daily.parquet` - Next-day return predictions
- `eval_explain_daily.parquet` - SHAP-based explanations

### Time Series Considerations
- **Date-based grouping**: Always sort by `["ticker", "date"]` for time series operations
- **Forward-looking prevention**: Use `shift(-1)` for labels, never future data for features
- **IST timezone**: All scheduling in `scheduler.py` uses `Asia/Kolkata` timezone
- **Trading day logic**: `collect_prices_nse.py` falls back to previous trading day if current bhavcopy unavailable

### Model Architecture
- **Target**: Next-day log returns (`y_next = groupby("ticker")["ret1"].shift(-1)`)
- **Features**: Fixed list in `FEAT_COLS` (technical indicators + market-wide news sentiment)
  - Technical: `ret1`, `ret5`, `vol20`, `rsi14`, `macd`, `adx14`, `z_close_20`
  - News: `market_news_sent_mean`, `market_news_sent_max`, `market_news_count`
- **Multi-Asset Support**: Framework supports 5 NSE series types:
  - `EQ`: Equity shares (most liquid, primary focus)
  - `BE`: Book Entry securities (dematerialized only)
  - `MF`: Mutual Fund units
  - `ETF`: Exchange Traded Funds
  - `GS`: Government Securities (bonds, treasury bills)
- **Model**: LightGBM regressor with TimeSeriesSplit CV (5 folds)
- **Model persistence**: `joblib.dump((model, FEAT_COLS), "data/model.joblib")`
- **Cross-validation**: Always use `TimeSeriesSplit` for temporal data

### SHAP Explainability Workflow
- **Global explanations**: `shap.TreeExplainer` on previous day's features
- **Top features**: Ranks features by mean absolute SHAP values across all stocks
- **Explanation text**: Auto-generated from top 6 contributing features
- **Gap analysis**: Compares predicted vs realized returns with `abs_gap` and `signed_gap`
- **Evaluation metrics**: MAPE, RMSE, and directional accuracy per stock
- **Output**: `eval_explain_daily.parquet` with `gap_reason_text` column

## External Integration Points

### NSE Data Sources
- **Bhavcopy URL**: `https://www1.nseindia.com/content/historical/EQUITIES/{year}/{MON}/cm{dd}{MON}{year}bhav.csv.zip`
- **Universe sources**: 
  - Master list: `https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv`
  - Live securities: `https://www.nseindia.com/market-data/securities-available-for-trading` (scrapes CSV link)
- **Fallback logic**: If today's bhavcopy fails, automatically tries previous trading day
- **Required headers**: `{"User-Agent": "Mozilla/5.0", "Accept": "text/html,application/xhtml+xml..."}` to avoid blocking
- **SSL verification**: Disabled (`verify=False`) for NSE APIs due to certificate issues
- **Series filtering**: Processes `EQ` (Equity), `BE` (Book Entry), `MF` (Mutual Fund), `ETF` (Exchange Traded Fund), and `GS` (Government Securities) series

### News Sources
- **Configuration**: `conf/news_sources.yaml` with RSS feed URLs (ETMarkets, Moneycontrol, LiveMint)
- **Sentiment engine**: VADER (compound score) - market-wide aggregation only
- **Ticker mapping**: Currently uses `"_MARKET_"` placeholder; individual ticker mapping is TODO
- **Feed parsing**: Uses `feedparser` library, processes up to 300 entries per source

## Development Workflows

### Testing Pipeline
```bash
# Full pipeline test (use for integration testing)
python pipeline/build_universe.py && \
python pipeline/collect_prices_nse.py && \
python pipeline/collect_news.py && \
python pipeline/build_features.py && \
python pipeline/train_model.py && \
python pipeline/predict.py && \
python pipeline/evaluate_and_explain.py
```

### API Development
```bash
# Local development server
uvicorn app.serve:app --reload --host 0.0.0.0 --port 8000
# Key endpoints: /predict_today, /explain_gap, /accuracy_by_stock?window=60
```

### Adding New Features
1. Modify `build_features()` function in `build_features.py`
2. Update `FEAT_COLS` list in `train_model.py`
3. Ensure feature engineering preserves temporal order
4. Test with existing model loading logic

## Configuration Management
- **Schedule timings**: `conf/schedule.yaml` (IST 24h format)
- **News sources**: `conf/news_sources.yaml` (RSS URLs)
- **No database**: Pure file-based system using parquet format
- **Data directory**: Auto-created at runtime, never commit to git

## Model Evaluation Patterns
- **Prediction confidence**: Uses `1.0 / (1e-6 + abs(y_pred - rolling_mean))` as proxy
- **Gap metrics**: `abs_gap` (MAE), `signed_gap` (bias), directional accuracy
- **Performance tracking**: `/accuracy_by_stock?window=60` for rolling 60-day metrics
- **SHAP integration**: Global feature importance drives explanation text generation
- **Temporal validation**: Evaluation always uses next trading day's realized returns