from fastapi import FastAPI, HTTPException
import os, pandas as pd, sys, logging
from datetime import datetime

# MongoDB integration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import db_manager
from db.models import PredictionsDAO, EvaluationsDAO
from db.config import db_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Stock ML (Analysis Only)")

# Initialize database connection on startup
@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 Starting Stock-ML API (DEP_TYPE={db_config.DEP_TYPE})")
    logger.info(f"🔧 Database: {db_config.DB_NAME}")
    db_manager.create_indexes()

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Stock ML (analysis-only)", 
        "environment": db_config.DEP_TYPE,
        "database": db_config.DB_NAME,
        "endpoints": [
            "/predict_today", 
            "/explain_gap", 
            "/accuracy_by_stock", 
            "/health"
        ]
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Test database connectivity
        predictions_dao = PredictionsDAO()
        test_df = predictions_dao.get_latest_predictions()
        
        return {
            "status": "healthy",
            "database": db_config.DB_NAME,
            "environment": db_config.DEP_TYPE,
            "mongodb_connection": "ok",
            "latest_predictions_count": len(test_df),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/predict_today")
async def predict_today():
    """Get latest predictions from MongoDB"""
    try:
        predictions_dao = PredictionsDAO()
        df = predictions_dao.get_latest_predictions()
        
        if df.empty:
            return {"status": "no_predictions", "message": "No predictions found in database"}
        
        # Handle data conversion for JSON serialization
        df = df.copy()
        
        # Convert datetime columns to strings
        for col in df.columns:
            if df[col].dtype == 'datetime64[ns]' or 'date' in col.lower():
                df[col] = df[col].astype(str)
        
        # Replace NaN with None for proper JSON serialization
        df = df.where(pd.notnull(df), None)
        
        # Get the latest prediction date
        if 'prediction_date' in df.columns:
            latest_date = str(df['prediction_date'].max())
        elif 'date' in df.columns:
            latest_date = str(df['date'].max())
        else:
            latest_date = "unknown"
            
        return {
            "status": "ok",
            "date": latest_date, 
            "count": len(df),
            "predictions": df.to_dict(orient="records")
        }
        
    except Exception as e:
        logger.error(f"Error in predict_today: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get predictions: {str(e)}")

@app.get("/explain_gap")
async def explain_gap():
    """Get latest evaluation explanations from MongoDB"""
    try:
        evaluations_dao = EvaluationsDAO()
        ev = evaluations_dao.get_latest_evaluations(days=5)
        
        if ev.empty:
            return {"status": "no_eval", "message": "No evaluations found in database"}
        
        # Get latest evaluation date
        if 'target_date' in ev.columns:
            latest = ev[ev["target_date"] == ev["target_date"].max()]
        elif 'date' in ev.columns:
            latest = ev[ev["date"] == ev["date"].max()]
        else:
            latest = ev.head(20)  # Fallback to first 20 records
            
        # Select relevant columns for explanation
        available_cols = latest.columns.tolist()
        desired_cols = ["ticker", "y_pred", "y_true", "abs_gap", "gap_reason_text"]
        out_cols = [col for col in desired_cols if col in available_cols]
        
        if not out_cols:
            return {"status": "no_data", "message": "Required columns not found in evaluations"}
            
        out = latest[out_cols].copy()
        
        # Handle NaN values and data types
        out = out.fillna({
            "gap_reason_text": "No explanation available",
            "y_pred": 0.0,
            "y_true": 0.0,
            "abs_gap": 0.0
        })
        
        # Convert datetime columns to strings
        for col in out.columns:
            if out[col].dtype == 'datetime64[ns]' or 'date' in col.lower():
                out[col] = out[col].astype(str)
        
        # Replace remaining NaN with None
        out = out.where(pd.notnull(out), None)
        
        # Get evaluation date
        if 'target_date' in latest.columns:
            eval_date = str(latest["target_date"].max())
        elif 'date' in latest.columns:
            eval_date = str(latest["date"].max())
        else:
            eval_date = "unknown"
            
        return {
            "status": "ok",
            "date": eval_date, 
            "count": len(out),
            "explanations": out.to_dict(orient="records")
        }
        
    except Exception as e:
        logger.error(f"Error in explain_gap: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get explanations: {str(e)}")

@app.get("/accuracy_by_stock")
async def accuracy_by_stock(window: int = 60):
    """Get accuracy statistics by stock from MongoDB evaluations"""
    try:
        evaluations_dao = EvaluationsDAO()
        ev = evaluations_dao.get_latest_evaluations(days=max(window, 30))
        
        if ev.empty:
            return {"status": "no_eval", "message": "No evaluations found in database"}
        
        # Sort by date and take last N records per ticker
        date_col = 'target_date' if 'target_date' in ev.columns else 'date'
        if date_col not in ev.columns:
            return {"status": "error", "message": "No date column found in evaluations"}
            
        ev = ev.sort_values(date_col).groupby("ticker").tail(window)
        
        # Check required columns exist
        required_cols = ['abs_gap']
        missing_cols = [col for col in required_cols if col not in ev.columns]
        if missing_cols:
            return {"status": "error", "message": f"Missing columns: {missing_cols}"}
        
        def rmse(x):
            import numpy as np
            return float(((x**2).mean())**0.5) if len(x) > 0 else 0.0
            
        def directional_accuracy(x):
            return float((x > 0).mean()) if len(x) > 0 else 0.0
        
        # Calculate statistics per ticker
        agg_dict = {
            "mape": ("abs_gap", "mean"),
            "rmse": ("abs_gap", rmse)
        }
        
        # Add directional accuracy if signed_gap column exists
        if 'signed_gap' in ev.columns:
            agg_dict["directional_acc"] = ("signed_gap", directional_accuracy)
        
        grp = ev.groupby("ticker").agg(agg_dict).reset_index()
        
        # Flatten column names if they are multi-level
        if isinstance(grp.columns, pd.MultiIndex):
            grp.columns = [col[0] if col[1] == '' else col[0] for col in grp.columns.values]
        
        # Handle NaN values
        grp = grp.fillna(0.0)
        
        # Convert to proper numeric types
        numeric_cols = ['mape', 'rmse', 'directional_acc']
        for col in numeric_cols:
            if col in grp.columns:
                grp[col] = pd.to_numeric(grp[col], errors='coerce').fillna(0.0)
        
        return {
            "status": "ok",
            "window_days": window, 
            "total_stocks": len(grp),
            "total_evaluations": len(ev),
            "stats": grp.to_dict(orient="records")
        }
        
    except Exception as e:
        logger.error(f"Error in accuracy_by_stock: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get accuracy stats: {str(e)}")
