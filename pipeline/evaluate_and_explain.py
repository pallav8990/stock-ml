import pandas as pd, numpy as np, shap, joblib, pathlib, logging, sys, os
from datetime import datetime

# MongoDB integration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import db_manager
from db.models import FeaturesDAO, PredictionsDAO, ModelsDAO, EvaluationsDAO
from db.config import db_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def shap_top_features(model, X, topk=6):
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X)
    vals = (abs(sv)).mean(axis=0)
    order = vals.argsort()[::-1][:topk]
    return [(X.columns[i], float(vals[i])) for i in order]

def load_data_from_mongodb():
    """Load features, predictions, and model from MongoDB"""
    logger.info("📊 Loading data from MongoDB...")
    
    # Initialize database connection
    db_manager.create_indexes()
    
    # Load features
    features_dao = FeaturesDAO()
    feats = features_dao.get_latest_features(lookback_days=5)
    logger.info(f"✅ Loaded {len(feats)} feature records")
    
    # Load predictions
    predictions_dao = PredictionsDAO()
    preds = predictions_dao.get_latest_predictions()
    logger.info(f"✅ Loaded {len(preds)} prediction records")
    
    # Load model
    models_dao = ModelsDAO()
    model, feat_cols = models_dao.load_model_object()
    logger.info(f"✅ Loaded model with {len(feat_cols) if feat_cols else 0} features")
    
    return feats, preds, model, feat_cols

def save_evaluations_to_mongodb(evaluations_df: pd.DataFrame):
    """Save evaluations to MongoDB"""
    logger.info(f"💾 Saving {len(evaluations_df)} evaluation records to MongoDB...")
    
    evaluations_dao = EvaluationsDAO()
    records_saved = evaluations_dao.insert_evaluations(evaluations_df)
    logger.info(f"✅ Evaluations saved: {records_saved} records processed")

if __name__ == "__main__":
    pathlib.Path("data").mkdir(exist_ok=True)
    
    logger.info(f"🚀 Running evaluation and explanation (DEP_TYPE={db_config.DEP_TYPE})...")
    logger.info(f"🔧 Database: {db_config.DB_NAME}")
    
    # Load data from MongoDB
    feats, preds, model, FEATS = load_data_from_mongodb()
    
    if feats.empty:
        logger.error("❌ No feature data found. Run build_features.py first.")
        exit(1)
    
    if preds.empty:
        logger.error("❌ No prediction data found. Run predict.py first.")
        exit(1)
    
    if model is None:
        logger.error("❌ No model found. Run train_model.py first.")
        exit(1)
    
    # Check we have enough dates
    all_dates = sorted(feats["date"].unique())
    if len(all_dates) < 2:
        logger.error("❌ Need at least two dates to evaluate. Only found dates: {all_dates}")
        exit(1)
    
    nextday = all_dates[-1]
    prevday = all_dates[-2]
    
    logger.info(f"📅 Evaluating predictions from {prevday} against realized returns on {nextday}")
    
    # Get realized returns (y_true) from nextday features
    realized = feats[feats["date"]==nextday][["ticker","ret1"]].rename(columns={"ret1":"y_true"})
    
    if realized.empty:
        logger.error(f"❌ No realized returns found for {nextday}")
        exit(1)
    
    # Merge predictions with realized returns
    merged = preds.merge(realized, on="ticker", how="left")
    merged = merged.dropna(subset=["y_true"])  # Remove tickers without realized returns
    
    if merged.empty:
        logger.error("❌ No matching predictions and realized returns")
        exit(1)
    
    # Calculate gaps
    merged["abs_gap"] = (merged["y_true"] - merged["y_pred"]).abs()
    merged["signed_gap"] = merged["y_true"] - merged["y_pred"]
    
    logger.info(f"📊 Evaluation metrics for {len(merged)} predictions:")
    logger.info(f"  Mean Absolute Error: {merged['abs_gap'].mean():.6f}")
    logger.info(f"  Root Mean Squared Error: {np.sqrt((merged['signed_gap']**2).mean()):.6f}")
    logger.info(f"  Directional Accuracy: {(np.sign(merged['y_pred']) == np.sign(merged['y_true'])).mean():.3f}")
    
    # Generate SHAP explanations using previous day's data
    X_prev = feats[feats["date"]==prevday][FEATS]
    if not X_prev.empty:
        logger.info("🔍 Generating SHAP explanations...")
        try:
            top_feats = shap_top_features(model, X_prev, topk=6)
            logger.info(f"✅ Top features: {[k for k, _ in top_feats]}")
        except Exception as e:
            logger.warning(f"⚠️ SHAP explanation failed: {e}")
            top_feats = []
    else:
        logger.warning("⚠️ No previous day data for SHAP explanations")
        top_feats = []
    
    # Generate explanation text
    def mk_reason(_):
        if top_feats:
            txt = "Key drivers (global SHAP): " + ", ".join([k for k,_ in top_feats])
        else:
            txt = "Model drivers unavailable (insufficient historical data)"
        return txt
    
    merged["gap_reason_text"] = merged.apply(mk_reason, axis=1)
    merged["evaluation_date"] = datetime.now()
    merged["target_date"] = nextday
    
    # Save to MongoDB
    save_evaluations_to_mongodb(merged)
    
    # Also save to parquet for backward compatibility (remove MongoDB _id if present)
    merged_clean = merged.drop(columns=['_id'], errors='ignore')
    merged_clean.to_parquet("data/eval_explain_daily.parquet", index=False)
    logger.info("💾 Also saved to parquet for backward compatibility")
    
    logger.info(f"✅ Evaluation complete for {nextday}: {len(merged)} stocks evaluated")
    
    # Show summary of worst performers
    worst = merged.nlargest(3, "abs_gap")[["ticker", "y_pred", "y_true", "abs_gap"]]
    logger.info("📉 Worst predictions:")
    for _, row in worst.iterrows():
        logger.info(f"  {row['ticker']}: pred={row['y_pred']:.4f}, true={row['y_true']:.4f}, gap={row['abs_gap']:.4f}")
