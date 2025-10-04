import pandas as pd, numpy as np, pathlib, logging, sys, os
from ta.momentum import RSIIndicator
from ta.trend import MACD, ADXIndicator

# MongoDB integration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import db_manager
from db.models import PricesDAO, NewsDAO, FeaturesDAO
from db.config import db_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_features(prices: pd.DataFrame, news: pd.DataFrame) -> pd.DataFrame:
    # Aggregate market-wide news sentiment per date (since we're not mapping to individual tickers yet)
    g = news.groupby(["date"]).agg(
        market_news_sent_mean=("sentiment","mean"),
        market_news_sent_max=("sentiment","max"),
        market_news_count=("sentiment","count")
    ).reset_index()

    feats = []
    for t, df in prices.groupby("ticker"):
        df = df.sort_values("date").copy()
        
        # Skip stocks with insufficient data for technical indicators
        if len(df) < 15:
            print(f"Skipping {t}: only {len(df)} rows, need 15+ for technical indicators")
            continue
            
        df["ret1"] = np.log(df["close"]).diff()
        df["ret5"] = np.log(df["close"]).diff(5)
        df["vol20"] = df["ret1"].rolling(20).std()
        
        # Use shorter windows for technical indicators if we don't have enough data
        window_rsi = min(14, len(df) - 1)
        window_adx = min(14, len(df) - 1)
        
        if window_rsi > 0:
            df["rsi14"] = RSIIndicator(df["close"], window_rsi).rsi()
        else:
            df["rsi14"] = 50.0  # neutral RSI
            
        try:
            df["macd"] = MACD(df["close"]).macd()
        except:
            df["macd"] = 0.0
            
        if window_adx > 0 and len(df) >= window_adx:
            try:
                df["adx14"] = ADXIndicator(df["high"], df["low"], df["close"], window_adx).adx()
            except:
                df["adx14"] = 25.0  # neutral ADX
        else:
            df["adx14"] = 25.0
            
        df["z_close_20"] = (df["close"]-df["close"].rolling(20).mean())/df["close"].rolling(20).std()
        feats.append(df)
        
    if not feats:
        print("Warning: No stocks had sufficient data for feature engineering")
        # Return empty dataframe with expected columns
        return pd.DataFrame(columns=["date", "ticker", "ret1", "ret5", "vol20", "rsi14", "macd", "adx14", "z_close_20", 
                                   "market_news_sent_mean", "market_news_sent_max", "market_news_count"])
    
    f = pd.concat(feats)
    
    # Don't drop all NaNs, only specific problematic ones
    f = f.dropna(subset=['ret1'])  # Only drop if return calculation failed
    
    out = f.merge(g, on="date", how="left").fillna({"market_news_sent_mean":0,"market_news_sent_max":0,"market_news_count":0})
    return out

def load_data_from_mongodb() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load prices and news data from MongoDB"""
    logger.info("📊 Loading data from MongoDB...")
    
    # Initialize database connection
    db_manager.create_indexes()
    
    # Load prices data
    prices_dao = PricesDAO()
    prices = prices_dao.get_all_prices()
    logger.info(f"✅ Loaded {len(prices)} price records")
    
    # Load news data
    news_dao = NewsDAO()
    news = news_dao.get_all_news()
    logger.info(f"✅ Loaded {len(news)} news records")
    
    return prices, news

def save_features_to_mongodb(df: pd.DataFrame) -> None:
    """Save features dataframe to MongoDB features collection"""
    logger.info(f"💾 Saving {len(df)} feature records to MongoDB...")
    
    # Use our features DAO to save the data
    features_dao = FeaturesDAO()
    records_saved = features_dao.insert_features(df)
    logger.info(f"✅ Features saved: {records_saved} total records processed")

if __name__ == "__main__":
    pathlib.Path("data").mkdir(exist_ok=True)
    
    logger.info(f"🚀 Building features (DEP_TYPE={db_config.DEP_TYPE})...")
    logger.info(f"🔧 Database: {db_config.DB_NAME}")
    
    # Load data from MongoDB
    prices, news = load_data_from_mongodb()
    
    if prices.empty:
        logger.error("❌ No price data found in MongoDB. Run collect_prices_nse.py first.")
        exit(1)
    
    if news.empty:
        logger.warning("⚠️ No news data found in MongoDB. Features will be created without news sentiment.")
    
    # Build features
    feats = build_features(prices, news)
    
    if feats.empty:
        logger.error("❌ No features could be generated. Check data quality.")
        exit(1)
    
    # Save to MongoDB
    save_features_to_mongodb(feats)
    
    # Also save to parquet for backward compatibility
    feats.to_parquet("data/features_daily.parquet", index=False)
    logger.info(f"💾 Also saved to parquet for backward compatibility")
    
    logger.info(f"✅ Feature engineering complete: {len(feats)} records")
    logger.info(f"📊 Tickers processed: {feats['ticker'].nunique()}")
