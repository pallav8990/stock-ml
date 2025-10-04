# Stock-ML MongoDB Schema Design

## Database: `stock_ml_db`

### 1. **Universe Collection** (`universe`)
Stores NSE securities master data.

```javascript
{
  _id: ObjectId,
  symbol: "RELIANCE",              // NSE symbol
  name_of_company: "Reliance Industries Limited",
  series: "EQ",                    // EQ, BE, MF, ETF, GS
  date_of_listing: ISODate("1977-11-29"),
  paid_up_value: 10,
  market_lot: 1,
  isin_number: "INE002A01018",
  face_value: 10,
  ticker: "RELIANCE_EQ",           // symbol + "_" + series
  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- `{ticker: 1}` (unique)
- `{symbol: 1, series: 1}` (compound, unique)
- `{series: 1}`

---

### 2. **Prices Collection** (`prices`)
Time-series price data with partitioning by date.

```javascript
{
  _id: ObjectId,
  date: ISODate("2025-10-04"),     // Trading date
  symbol: "RELIANCE",
  series: "EQ",
  ticker: "RELIANCE_EQ",
  open: 2850.50,
  high: 2875.25,
  low: 2840.10,
  close: 2862.75,
  volume: 1234567,
  data_source: "nse_bhavcopy",     // "nse_bhavcopy" | "mock_data"
  dep_type: "prod",                // "prod" | "mock"
  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- `{date: -1, ticker: 1}` (compound, for time-series queries)
- `{ticker: 1, date: -1}` (compound, for stock-specific time series)
- `{date: -1}` (for daily data retrieval)
- `{symbol: 1, series: 1, date: -1}`

---

### 3. **News Collection** (`news`)
Market sentiment data from RSS feeds.

```javascript
{
  _id: ObjectId,
  date: ISODate("2025-10-04"),
  ticker: "_MARKET_",              // Market-wide or specific ticker
  source: "moneycontrol",          // "etmarkets" | "moneycontrol" | "livemint"
  news_count: 25,
  sentiment_mean: 0.125,           // VADER compound score
  sentiment_max: 0.8542,
  sentiment_min: -0.2341,
  sentiment_std: 0.2156,
  articles: [                      // Array of individual articles
    {
      title: "Market rises on strong earnings",
      url: "https://...",
      published_date: ISODate,
      sentiment_score: 0.6249
    }
  ],
  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- `{date: -1, ticker: 1}`
- `{date: -1}`
- `{ticker: 1, date: -1}`

---

### 4. **Features Collection** (`features`)
Technical indicators and engineered features.

```javascript
{
  _id: ObjectId,
  date: ISODate("2025-10-04"),
  ticker: "RELIANCE_EQ",
  
  // Price-based features
  ret1: 0.0125,                    // 1-day return
  ret5: 0.0342,                    // 5-day return
  vol20: 0.0234,                   // 20-day volatility
  
  // Technical indicators
  rsi14: 65.43,                    // 14-day RSI
  macd: 12.56,                     // MACD value
  adx14: 23.45,                    // 14-day ADX
  z_close_20: 1.23,                // Z-score of close price (20-day)
  
  // News sentiment features
  market_news_sent_mean: 0.125,
  market_news_sent_max: 0.854,
  market_news_count: 25,
  
  // Labels (for training)
  y_next: 0.0089,                  // Next day return (target)
  
  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- `{date: -1, ticker: 1}` (primary time-series index)
- `{ticker: 1, date: -1}` (stock-specific queries)
- `{date: -1}` (daily feature retrieval)

---

### 5. **Models Collection** (`models`)
Trained model metadata and artifacts.

```javascript
{
  _id: ObjectId,
  model_id: "lgb_20251004_v1",     // Unique model identifier
  model_type: "lightgbm_regressor",
  training_date: ISODate("2025-10-04"),
  
  // Training metadata
  feature_columns: [               // Features used for training
    "ret1", "ret5", "vol20", "rsi14", "macd", 
    "adx14", "z_close_20", "market_news_sent_mean",
    "market_news_sent_max", "market_news_count"
  ],
  training_samples: 12450,
  validation_scores: {
    "fold_1": {"mse": 0.0234, "rmse": 0.153, "mape": 2.45},
    "fold_2": {"mse": 0.0241, "rmse": 0.155, "mape": 2.52},
    "fold_3": {"mse": 0.0229, "rmse": 0.151, "mape": 2.38},
    "fold_4": {"mse": 0.0238, "rmse": 0.154, "mape": 2.48},
    "fold_5": {"mse": 0.0235, "rmse": 0.153, "mape": 2.43}
  },
  mean_cv_score: {"mse": 0.0235, "rmse": 0.153, "mape": 2.45},
  
  // Model storage (binary data or cloud reference)
  model_data: BinData,             // GridFS reference or binary blob
  model_size_mb: 1.2,
  
  // Model parameters
  hyperparameters: {
    "n_estimators": 100,
    "max_depth": 6,
    "learning_rate": 0.1,
    "random_state": 42
  },
  
  is_active: true,                 // Currently deployed model
  performance_metrics: {
    "last_30d_mape": 2.34,
    "last_30d_directional_accuracy": 0.652
  },
  
  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- `{model_id: 1}` (unique)
- `{is_active: 1, training_date: -1}`
- `{training_date: -1}`

---

### 6. **Predictions Collection** (`predictions`)
Model predictions for future returns.

```javascript
{
  _id: ObjectId,
  prediction_date: ISODate("2025-10-04"),  // Date prediction was made
  target_date: ISODate("2025-10-05"),      // Date being predicted for
  ticker: "RELIANCE_EQ",
  
  model_id: "lgb_20251004_v1",     // Reference to model used
  y_pred: 0.0156,                  // Predicted return
  y_pred_conf: 0.78,               // Prediction confidence (0-1)
  
  // Features used for prediction
  features_used: {
    "ret1": 0.0125,
    "ret5": 0.0342,
    "vol20": 0.0234,
    "rsi14": 65.43,
    "macd": 12.56,
    "adx14": 23.45,
    "z_close_20": 1.23,
    "market_news_sent_mean": 0.125,
    "market_news_sent_max": 0.854,
    "market_news_count": 25
  },
  
  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- `{prediction_date: -1, ticker: 1}`
- `{target_date: -1, ticker: 1}`
- `{ticker: 1, prediction_date: -1}`
- `{model_id: 1, prediction_date: -1}`

---

### 7. **Evaluations Collection** (`evaluations`)
Model performance evaluation and SHAP explanations.

```javascript
{
  _id: ObjectId,
  evaluation_date: ISODate("2025-10-05"), // Date of evaluation
  prediction_date: ISODate("2025-10-04"), // Original prediction date
  ticker: "RELIANCE_EQ",
  
  model_id: "lgb_20251004_v1",
  
  // Actual vs Predicted
  y_pred: 0.0156,                  // Predicted return
  y_actual: 0.0142,                // Actual realized return
  
  // Gap analysis
  abs_gap: 0.0014,                 // |y_actual - y_pred|
  signed_gap: -0.0014,             // y_actual - y_pred
  gap_percentage: 8.97,            // (abs_gap / |y_actual|) * 100
  
  // Performance metrics
  directional_correct: true,       // Same direction prediction
  
  // SHAP explanations
  shap_values: {                   // Feature importance for this prediction
    "ret1": 0.0034,
    "ret5": -0.0012,
    "vol20": 0.0008,
    "rsi14": -0.0015,
    "macd": 0.0023,
    "adx14": 0.0005,
    "z_close_20": -0.0007,
    "market_news_sent_mean": 0.0018,
    "market_news_sent_max": 0.0009,
    "market_news_count": -0.0003
  },
  
  // Top contributing features
  top_positive_features: [
    {"feature": "ret1", "contribution": 0.0034},
    {"feature": "macd", "contribution": 0.0023},
    {"feature": "market_news_sent_mean", "contribution": 0.0018}
  ],
  top_negative_features: [
    {"feature": "rsi14", "contribution": -0.0015},
    {"feature": "ret5", "contribution": -0.0012},
    {"feature": "z_close_20", "contribution": -0.0007}
  ],
  
  // Auto-generated explanation
  gap_reason_text: "The prediction was 8.97% higher than actual return. Key positive drivers were recent 1-day momentum (ret1: +0.34%) and MACD technical signal (+0.23%). However, RSI overbought conditions (-0.15%) and 5-day mean reversion (-0.12%) provided downward pressure.",
  
  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- `{evaluation_date: -1, ticker: 1}`
- `{ticker: 1, evaluation_date: -1}`
- `{model_id: 1, evaluation_date: -1}`
- `{prediction_date: -1}`

---

## **Collection Size Estimates & Optimization**

### **Data Volume Projections (Annual)**
- **Universe**: ~2,500 docs (static, updates rare)
- **Prices**: ~600K docs (2,500 symbols × 240 trading days)
- **News**: ~365 docs (daily market sentiment)
- **Features**: ~600K docs (same as prices)
- **Predictions**: ~600K docs (daily predictions)
- **Evaluations**: ~600K docs (daily evaluations)
- **Models**: ~50 docs (model versions)

### **Partitioning Strategy**
- **Time-based partitioning** by `date` for prices, features, predictions, evaluations
- **Monthly collections**: `prices_2025_10`, `features_2025_10`, etc.
- **Automatic TTL**: Remove old data after configurable retention period

### **Performance Optimizations**
1. **Compound Indexes**: Optimize for common query patterns
2. **Projection**: Only fetch required fields in queries
3. **Aggregation Pipeline**: Use MongoDB's aggregation for analytics
4. **Connection Pooling**: Maintain persistent connection pools
5. **Batch Operations**: Use bulk inserts for pipeline data
6. **GridFS**: Store large model binaries separately

---

## **Environment Configuration**

```python
# Production
MONGODB_URL = "mongodb://localhost:27017"
DB_NAME = "stock_ml_db"

# Cloud deployment
MONGODB_URL = "mongodb+srv://user:pass@cluster.mongodb.net"
DB_NAME = "stock_ml_prod"
```

This schema provides:
✅ **Scalability**: Handles millions of time-series records
✅ **Performance**: Optimized indexes for common queries  
✅ **Flexibility**: Easy to add new features and data sources
✅ **Traceability**: Full audit trail with created_at/updated_at
✅ **Analytics Ready**: Structured for aggregation pipelines