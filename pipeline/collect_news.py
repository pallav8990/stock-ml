import pandas as pd, feedparser, yaml, pathlib, logging, sys, os
from datetime import datetime, timezone
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# MongoDB integration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import db_manager
from db.models import NewsDAO
from db.config import db_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def collect_news():
    """Collect news from RSS feeds and perform sentiment analysis"""
    logger.info("📰 Collecting news from RSS feeds...")
    
    cfg = yaml.safe_load(open("conf/news_sources.yaml"))
    feeds = cfg.get("rss_feeds", {})
    an = SentimentIntensityAnalyzer()
    rows = []
    
    for src, url in feeds.items():
        logger.info(f"Fetching from {src}: {url}")
        try:
            feed = feedparser.parse(url)
            articles_processed = 0
            
            for e in feed.entries[:300]:
                title = e.title
                pub = getattr(e, "published_parsed", None)
                pub_dt = datetime.now(timezone.utc) if not pub else datetime(*pub[:6], tzinfo=timezone.utc)
                sent = an.polarity_scores(title)["compound"]
                
                rows.append({
                    "date": pub_dt.date(),
                    "ticker": "_MARKET_",         # Market-wide signal; per-ticker map can be added later
                    "source": src,
                    "headline": title,
                    "sentiment": sent,
                    "published_at": pub_dt
                })
                articles_processed += 1
            
            logger.info(f"✅ {src}: Processed {articles_processed} articles")
            
        except Exception as e:
            logger.error(f"❌ Error fetching from {src}: {e}")
            continue
    
    df = pd.DataFrame(rows)
    logger.info(f"📊 Total news articles collected: {len(df)}")
    return df

def save_news_to_mongodb(df: pd.DataFrame) -> None:
    """Save news dataframe to MongoDB news collection"""
    logger.info(f"💾 Saving {len(df)} news records to MongoDB...")
    
    # Initialize database connection
    db_manager.create_indexes()
    
    # Use our news DAO to save the data
    news_dao = NewsDAO()
    records_saved = news_dao.insert_news(df)
    logger.info(f"✅ News saved: {records_saved} total records processed")

if __name__ == "__main__":
    pathlib.Path("data").mkdir(exist_ok=True)
    
    logger.info(f"🚀 Collecting news (DEP_TYPE={db_config.DEP_TYPE})...")
    logger.info(f"🔧 Database: {db_config.DB_NAME}")
    
    # Collect news data
    df = collect_news()
    
    # Save to MongoDB
    save_news_to_mongodb(df)
    
    # Also save to parquet for backward compatibility
    df.to_parquet("data/news_daily.parquet", index=False)
    logger.info(f"💾 Also saved to parquet for backward compatibility")
    
    logger.info(f"✅ News collection complete: {len(df)} articles")
