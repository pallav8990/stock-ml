# pipeline/collect_prices_nse.py
import pandas as pd, datetime as dt, pathlib, zipfile, io, time, certifi, os, logging
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# MongoDB integration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import db_manager
from db.models import PricesDAO
from db.config import db_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ARCHIVES_HOST = "https://nsearchives.nseindia.com"
HOMEPAGE = "https://www.nseindia.com/"  # for cookies
HDRS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def session_with_retries():
    s = requests.Session()
    retries = Retry(
        total=5, connect=5, read=5, backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD")
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.headers.update(HDRS)
    # Warm-up: get homepage to set cookies so the archive host trusts us
    s.get(HOMEPAGE, timeout=20, verify=certifi.where())
    return s

def bhavcopy_url(d: dt.date) -> str:
    mon = d.strftime("%b").upper()
    # archives pattern: /content/historical/EQUITIES/YYYY/MON/cmDDMONYYYYbhav.csv.zip
    return f"{ARCHIVES_HOST}/content/historical/EQUITIES/{d.year}/{mon}/cm{d:%d}{mon}{d.year}bhav.csv.zip"

def previous_trading_day(d: dt.date) -> dt.date:
    p = d - dt.timedelta(days=1)
    while p.weekday() >= 5:  # 5=Sat,6=Sun
        p -= dt.timedelta(days=1)
    return p

def fetch_bhavcopy_df(s: requests.Session, d: dt.date) -> pd.DataFrame:
    url = bhavcopy_url(d)
    r = s.get(url, timeout=60, verify=certifi.where())
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        name = [n for n in zf.namelist() if n.endswith(".csv")][0]
        with zf.open(name) as f:
            df = pd.read_csv(f)
    # standardize
    df.columns = [c.strip().upper() for c in df.columns]
    df["DATE"] = pd.to_datetime(df["TIMESTAMP"], format="%d-%b-%Y").dt.date
    return df

def generate_mock_data(target: dt.date) -> pd.DataFrame:
    """Generate mock price data for testing/development"""
    import numpy as np
    
    print("🔧 Generating mock price data for development/testing...")
    
    # Create comprehensive mock data with enough history for technical indicators
    symbols = [
        "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "ITC", "SBIN", "WIPRO",
        "LT", "BHARTIARTL", "HCLTECH", "ASIANPAINT", "MARUTI", "KOTAKBANK", "AXISBANK"
    ]
    
    # Generate 60 trading days of historical data (enough for all technical indicators)
    dates = []
    current_date = target
    for i in range(60):
        if current_date.weekday() < 5:  # Weekday only
            dates.append(current_date)
        current_date = current_date - dt.timedelta(days=1)
    dates = sorted(dates)  # Chronological order
    
    records = []
    np.random.seed(42)  # For reproducible mock data
    
    for symbol in symbols:
        base_price = np.random.uniform(100, 3000)
        prev_close = base_price
        
        for i, date in enumerate(dates):
            # Generate realistic price movement with some trend and volatility
            daily_return = np.random.normal(0.001, 0.02)  # 0.1% mean return, 2% volatility
            trend_factor = 1 + daily_return
            
            open_price = prev_close * np.random.uniform(0.995, 1.005)
            close_price = open_price * trend_factor
            high_price = max(open_price, close_price) * np.random.uniform(1.0, 1.03)
            low_price = min(open_price, close_price) * np.random.uniform(0.97, 1.0)
            volume = int(np.random.uniform(100000, 10000000))
            
            records.append({
                "date": date,
                "symbol": symbol,
                "series": "EQ",
                "open": round(open_price, 2),
                "high": round(high_price, 2), 
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": volume
            })
            
            prev_close = close_price
    
    mock_df = pd.DataFrame(records)
    mock_df['ticker'] = mock_df['symbol'] + '_' + mock_df['series']
    print(f"✅ Generated mock data: {len(mock_df)} records for {len(symbols)} symbols over {len(dates)} days")
    return mock_df

def collect_all_prices(target: dt.date) -> pd.DataFrame:
    dep_type = os.getenv('DEP_TYPE', 'prod').lower()
    
    if dep_type == 'mock':
        print(f"🔧 DEP_TYPE=mock: Using mock data for development/testing")
        return generate_mock_data(target)
    
    elif dep_type == 'prod':
        print(f"🚀 DEP_TYPE=prod: Fetching real NSE data")
        s = session_with_retries()
        last_error = None
        
        # Try target day first, then previous trading day
        for attempt_day in (target, previous_trading_day(target)):
            try:
                print(f"Attempting to fetch NSE bhavcopy for {attempt_day}...")
                df = fetch_bhavcopy_df(s, attempt_day)
                print(f"✅ Successfully fetched NSE bhavcopy for {attempt_day}")
                break
            except Exception as e:
                last_error = e
                print(f"❌ Failed to fetch bhavcopy for {attempt_day}: {type(e).__name__}: {e}")
                time.sleep(1.0)
        else:
            # No fallback in prod mode - raise clear error about NSE data unavailability
            prev_day = previous_trading_day(target)
            error_msg = f"""
NSE Bhavcopy Data Unavailable! (DEP_TYPE=prod)

Failed to fetch price data from NSE archives for:
- Target date: {target} 
- Previous trading day: {prev_day}

Last error: {type(last_error).__name__}: {last_error}

Possible reasons:
1. NSE has not yet published bhavcopy for {target}
2. Network connectivity issues to NSE archives
3. NSE server maintenance or downtime
4. SSL/TLS certificate issues

NSE typically publishes bhavcopy data with some delay after market close.
Please try again later or check NSE archives manually at:
{bhavcopy_url(target)}

To use mock data for development: export DEP_TYPE=mock
"""
            raise RuntimeError(error_msg)
    
    else:
        raise ValueError(f"Invalid DEP_TYPE='{dep_type}'. Use 'prod' for real NSE data or 'mock' for test data.")
    
    # Process the fetched data
    df = df[df["SERIES"].isin(["EQ","BE","ETF","MF","GS"])].copy()
    out = df.rename(columns={"TOTTRDQTY":"VOLUME"})[["DATE","SYMBOL","SERIES","OPEN","HIGH","LOW","CLOSE","VOLUME"]]
    out.columns = [c.lower() for c in out.columns]
    # Add ticker column for consistency
    out['ticker'] = out['symbol'] + '_' + out['series']
    return out

def save_prices_to_mongodb(df: pd.DataFrame) -> None:
    """Save prices dataframe to MongoDB prices collection"""
    logger.info(f"💾 Saving {len(df)} price records to MongoDB...")
    
    # Initialize database connection
    db_manager.create_indexes()
    
    # Use our prices DAO to save the data
    prices_dao = PricesDAO()
    records_saved = prices_dao.insert_prices(df)
    logger.info(f"✅ Prices saved: {records_saved} total records processed")

if __name__ == "__main__":
    pathlib.Path("data").mkdir(exist_ok=True)
    today = dt.date.today()
    
    logger.info(f"🚀 Collecting NSE prices (DEP_TYPE={db_config.DEP_TYPE})...")
    logger.info(f"🔧 Database: {db_config.DB_NAME}")
    
    # Collect price data
    prices = collect_all_prices(today)
    
    # Save to MongoDB
    save_prices_to_mongodb(prices)
    
    # Also save to parquet for backward compatibility
    prices.to_parquet("data/prices_daily.parquet", index=False)
    logger.info(f"💾 Also saved to parquet for backward compatibility")
    
    logger.info(f"✅ Prices collection complete for {prices['date'].max()}")
    logger.info(f"📊 Summary: {len(prices)} records, {prices['symbol'].nunique()} symbols, {prices['date'].nunique()} dates")
