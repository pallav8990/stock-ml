<<<<<<< HEAD
# Stock-ML (Analysis-Only)

**Purpose:** Daily, automated pipeline to **collect** NSE EOD prices & public news, **build features**, **train** a next‑day return model, **predict**, and **evaluate** with gap explanations. No trading or broker APIs.

## Project layout
```
stock-ml/
  app/
    serve.py                # FastAPI endpoints for predictions, accuracy, explanations
  pipeline/
    build_universe.py       # Build full NSE equity universe (EQ/BE) from official sources
    collect_prices_nse.py   # Download daily bhavcopy (entire market EOD)
    collect_news.py         # Collect RSS news and score sentiment (VADER)
    build_features.py       # Merge price & news features per (date, ticker)
    train_model.py          # Train LightGBM regressor to predict next-day log return
    predict.py              # Predict next-day returns for latest date
    evaluate_and_explain.py # Compare with realized returns, SHAP-based reasoning
    scheduler.py            # Daily IST cron-style scheduler (APScheduler)
  conf/
    schedule.yaml
    news_sources.yaml
  data/                     # Parquet outputs (created at runtime)
  requirements.txt
  README.md
```

## Quick start
1. **Python 3.10+** recommended
2. Install deps: `pip install -r requirements.txt`
3. First run (one-time or to backfill today):
   ```bash
   python pipeline/build_universe.py
   python pipeline/collect_prices_nse.py
   python pipeline/collect_news.py
   python pipeline/build_features.py
   python pipeline/train_model.py
   python pipeline/predict.py
   python pipeline/evaluate_and_explain.py
   ```
4. **API**:
   ```bash
   uvicorn app.serve:app --host 0.0.0.0 --port 8000
   # GET /predict_today, /explain_gap, /accuracy_by_stock?window=60
   ```
5. **Scheduler (IST timings)**:
   ```bash
   python pipeline/scheduler.py
   ```

### Notes
- This is **analysis-only**. No buy/sell, no broker APIs.
- Uses **NSE bhavcopy** (EOD zip CSV). If a day's bhavcopy isn't published yet, it falls back to the previous trading day.
- News are pulled from configurable public RSS feeds and sentiment-scored with VADER. You can later swap in FinBERT or paid APIs.
- Make sure outbound internet access is allowed on the host/container for downloads.

### Disclaimer
This repository is for **educational analysis** only. It is **not investment advice**.
=======
# stock-ml
>>>>>>> a0729cb6267b23f82b83fdf3249997437419e52c
