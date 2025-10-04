import pandas as pd, numpy as np, joblib, pathlib, logging, sys, os, pickle, base64
from lightgbm import LGBMRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error
from datetime import datetime

# MongoDB integration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import db_manager
from db.models import FeaturesDAO, ModelsDAO
from db.config import db_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FEAT_COLS = ["ret1","ret5","vol20","rsi14","macd","adx14","z_close_20",
             "market_news_sent_mean","market_news_sent_max","market_news_count"]

def make_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["ticker","date"]).copy()
    df["y_next"] = df.groupby("ticker")["ret1"].shift(-1)  # predict next-day log return
    return df.dropna(subset=["y_next"])

def load_features_from_mongodb() -> pd.DataFrame:
    """Load features data from MongoDB"""
    logger.info("📊 Loading features from MongoDB...")
    
    # Initialize database connection
    db_manager.create_indexes()
    
    # Load features data
    features_dao = FeaturesDAO()
    df = features_dao.get_latest_features(lookback_days=60)  # Get recent features for training
    logger.info(f"✅ Loaded {len(df)} feature records")
    
    return df

def save_model_to_mongodb(model, feat_cols, cv_mae: float) -> str:
    """Save trained model to MongoDB models collection"""
    logger.info("💾 Saving trained model to MongoDB...")
    
    # Serialize model using pickle then base64 encode
    model_bytes = pickle.dumps((model, feat_cols))
    model_data = base64.b64encode(model_bytes).decode('utf-8')
    
    # Create model record
    model_record = {
        "model_type": "LGBMRegressor",
        "feature_columns": feat_cols,
        "model_data": model_data,
        "training_date": datetime.now(),
        "cv_mae": cv_mae,
        "n_estimators": model.n_estimators,
        "learning_rate": model.learning_rate,
        "is_active": True,
        "model_version": "1.0",
        "training_samples": model.n_features_in_
    }
    
    # Use models DAO to save
    models_dao = ModelsDAO()
    model_id = models_dao.save_model(model_record)
    logger.info(f"✅ Model saved with ID: {model_id}")
    
    return model_id

if __name__ == "__main__":
    pathlib.Path("data").mkdir(exist_ok=True)
    
    logger.info(f"🚀 Training model (DEP_TYPE={db_config.DEP_TYPE})...")
    logger.info(f"🔧 Database: {db_config.DB_NAME}")
    
    # Load features from MongoDB
    df = load_features_from_mongodb()
    
    if df.empty:
        logger.error("❌ No feature data found in MongoDB. Run build_features.py first.")
        exit(1)
    
    # Prepare training data
    df = make_labels(df)
    logger.info(f"📊 Training data: {len(df)} samples after label creation")
    
    if len(df) < 50:
        logger.error("❌ Insufficient training data. Need at least 50 samples.")
        exit(1)
    
    # Optional liquidity filter to reduce noise
    # df = df[df["volume"] >= 50000]
    
    X, y = df[FEAT_COLS], df["y_next"]
    logger.info(f"🎯 Training features: {X.shape}, Target: {y.shape}")
    
    # Cross-validation
    tscv = TimeSeriesSplit(n_splits=min(5, len(df)//10))  # Adaptive splits based on data size
    maes = []
    
    logger.info("🔄 Running cross-validation...")
    for fold, (tr, te) in enumerate(tscv.split(X)):
        m = LGBMRegressor(n_estimators=600, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8, verbose=-1)
        m.fit(X.iloc[tr], y.iloc[tr])
        p = m.predict(X.iloc[te])
        fold_mae = mean_absolute_error(y.iloc[te], p)
        maes.append(fold_mae)
        logger.info(f"  Fold {fold+1}: MAE = {fold_mae:.6f}")
    
    cv_mae = float(np.mean(maes))
    logger.info(f"✅ Cross-validation MAE (mean): {cv_mae:.6f}")
    
    # Train final model
    logger.info("🎯 Training final model...")
    model = LGBMRegressor(n_estimators=800, learning_rate=0.03, subsample=0.9, colsample_bytree=0.9, verbose=-1)
    model.fit(X, y)
    
    # Save to MongoDB
    model_id = save_model_to_mongodb(model, FEAT_COLS, cv_mae)
    
    # Also save to joblib for backward compatibility
    joblib.dump((model, FEAT_COLS), "data/model.joblib")
    logger.info("💾 Also saved to joblib for backward compatibility")
    
    logger.info(f"✅ Model training complete!")
    logger.info(f"📊 Model ID: {model_id}, CV MAE: {cv_mae:.6f}")
