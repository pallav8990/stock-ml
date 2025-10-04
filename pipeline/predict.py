import pandas as pd, numpy as np, joblib, pathlib, logging, sys, os
from datetime import datetime

# MongoDB integration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import db_manager
from db.models import FeaturesDAO, ModelsDAO, PredictionsDAO
from db.config import db_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_model_from_mongodb():
    """Load the active model from MongoDB"""
    logger.info("🤖 Loading active model from MongoDB...")
    
    models_dao = ModelsDAO()
    model_obj, feat_cols = models_dao.load_model_object()
    
    if model_obj is None:
        logger.error("❌ No active model found in MongoDB")
        return None, None
    
    logger.info(f"✅ Loaded active model with {len(feat_cols)} features")
    return model_obj, feat_cols

def load_latest_features():
    """Load latest features from MongoDB"""
    logger.info("📊 Loading latest features from MongoDB...")
    
    features_dao = FeaturesDAO()
    feats = features_dao.get_latest_features(lookback_days=5)
    
    if feats.empty:
        logger.error("❌ No features found in MongoDB")
        return pd.DataFrame()
    
    logger.info(f"✅ Loaded {len(feats)} feature records")
    return feats

def save_predictions_to_mongodb(predictions_df: pd.DataFrame, model_id: str):
    """Save predictions to MongoDB"""
    logger.info(f"💾 Saving {len(predictions_df)} predictions to MongoDB...")
    
    predictions_dao = PredictionsDAO()
    records_saved = predictions_dao.insert_predictions(predictions_df, model_id)
    logger.info(f"✅ Predictions saved: {records_saved} records processed")

if __name__ == "__main__":
    pathlib.Path("data").mkdir(exist_ok=True)
    
    logger.info(f"🚀 Making predictions (DEP_TYPE={db_config.DEP_TYPE})...")
    logger.info(f"🔧 Database: {db_config.DB_NAME}")
    
    # Initialize database connection
    db_manager.create_indexes()
    
    # Load model from MongoDB
    model, FEATS = load_model_from_mongodb()
    if model is None:
        logger.error("❌ No model available. Run train_model.py first.")
        exit(1)
    
    # Load features from MongoDB
    feats = load_latest_features()
    if feats.empty:
        logger.error("❌ No features available. Run build_features.py first.")
        exit(1)
    
    # Get latest date data
    today = feats["date"].max()
    today_rows = feats[feats["date"]==today].copy()
    
    if today_rows.empty:
        logger.error(f"❌ No feature rows for latest date: {today}")
        exit(1)
    
    logger.info(f"🎯 Making predictions for {today} ({len(today_rows)} tickers)")
    
    # Make predictions
    try:
        today_rows["y_pred"] = model.predict(today_rows[FEATS])
        
        # Simple confidence proxy based on volatility
        rolling_mean = today_rows.groupby("ticker")["ret1"].transform(lambda x: x.rolling(min(20, len(x)), min_periods=1).mean())
        today_rows["y_pred_conf"] = 1.0 / (1e-6 + np.abs(today_rows["y_pred"] - rolling_mean))
        
        # Prepare output
        out = today_rows[["date","ticker","y_pred","y_pred_conf"]].copy()
        out["prediction_date"] = datetime.now()
        
        # Get model info for saving
        models_dao = ModelsDAO()
        active_model = models_dao.get_active_model()
        model_id = active_model.get("model_id", "unknown")
        
        # Save to MongoDB
        save_predictions_to_mongodb(out, model_id)
        
        # Also save to parquet for backward compatibility
        out.to_parquet("data/predictions_daily.parquet", index=False)
        logger.info("💾 Also saved to parquet for backward compatibility")
        
        logger.info(f"✅ Predictions complete for {today}: {len(out)} tickers")
        
        # Show sample predictions
        logger.info("📊 Sample predictions:")
        sample = out.head(5)[["ticker", "y_pred", "y_pred_conf"]]
        for _, row in sample.iterrows():
            logger.info(f"  {row['ticker']}: pred={row['y_pred']:.4f}, conf={row['y_pred_conf']:.4f}")
            
    except Exception as e:
        logger.error(f"❌ Prediction error: {e}")
        exit(1)
