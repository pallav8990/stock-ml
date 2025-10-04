import pandas as pd, requests, io, pathlib, logging, os, sys

# Add project root to path  
project_root = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bs4 import BeautifulSoup
import urllib3
from db import universe_dao, initialize_database

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EQUITY_MASTER_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
LIVE_EQ_URL = "https://www.nseindia.com/market-data/securities-available-for-trading"

# Supported NSE Series Types
SUPPORTED_SERIES = ["EQ", "BE", "MF", "ETF", "GS"]

HDRS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def create_mock_universe() -> pd.DataFrame:
    """Create mock universe data when NSE APIs are unavailable"""
    import datetime as dt
    
    # Popular NSE stocks for testing - including multiple series types
    stocks_data = [
        # Equity stocks
        ("RELIANCE", "Reliance Industries Limited", "EQ", "INE002A01018", "1977-11-29"),
        ("TCS", "Tata Consultancy Services Limited", "EQ", "INE467B01029", "2004-08-25"),
        ("HDFCBANK", "HDFC Bank Limited", "EQ", "INE040A01034", "1995-11-08"),
        ("INFY", "Infosys Limited", "EQ", "INE009A01021", "1993-02-08"),
        ("HDFC", "Housing Development Finance Corporation Limited", "BE", "INE001A01036", "1978-05-14"),
        ("ICICIBANK", "ICICI Bank Limited", "BE", "INE090A01021", "1997-09-17"),
        ("SBIN", "State Bank of India", "EQ", "INE062A01020", "1997-03-03"),
        ("BHARTIARTL", "Bharti Airtel Limited", "EQ", "INE397D01024", "2002-02-05"),
        ("LT", "Larsen & Toubro Limited", "EQ", "INE018A01030", "1995-07-17"),
        ("HCLTECH", "HCL Technologies Limited", "EQ", "INE860A01027", "2000-01-06"),
        ("ITC", "ITC Limited", "EQ", "INE154A01025", "1996-08-23"),
        ("WIPRO", "Wipro Limited", "EQ", "INE075A01022", "1980-11-07"),
        ("ASIANPAINT", "Asian Paints Limited", "EQ", "INE021A01026", "1982-02-03"),
        ("MARUTI", "Maruti Suzuki India Limited", "EQ", "INE585B01010", "2003-07-09"),
        ("KOTAKBANK", "Kotak Mahindra Bank Limited", "EQ", "INE237A01028", "1996-12-20"),
        
        # ETF samples  
        ("NIFTYBEES", "Nippon India ETF Nifty BeES", "ETF", "INF204KB17I5", "2002-01-08"),
        ("JUNIORBEES", "Nippon India ETF Junior BeES", "ETF", "INF204KB14I2", "2003-06-12"),
        
        # Mutual Fund samples
        ("NIFTYNEXT50", "ICICI Prudential Nifty Next 50 Index Fund", "MF", "INF109K01231", "2010-09-29"),
        
        # Government Securities (sample)
        ("GS2030", "Government of India Bond 2030", "GS", "IN0020160047", "2020-05-15")
    ]
    
    # Create DataFrame
    mock_data = []
    for symbol, name, series, isin, listing_date in stocks_data:
        mock_data.append({
            "symbol": symbol,
            "name_of_company": name,
            "series": series,
            "date_of_listing": pd.to_datetime(listing_date).date(),
            "paid_up_value": 10.0,  # Mock value
            "market_lot": 1,
            "isin_number": isin,
            "face_value": 10.0,  # Mock value
            "ticker": f"{symbol}_{series}"
        })
    
    df = pd.DataFrame(mock_data)
    logger.info(f"Created mock universe: {len(df)} securities across series {df['series'].value_counts().to_dict()}")
    return df

def fetch_nse_universe() -> pd.DataFrame:
    """Fetch real NSE universe data"""
    try:
        # First try master equity list
        logger.info(f"Fetching NSE master equity list from: {EQUITY_MASTER_URL}")
        response = requests.get(EQUITY_MASTER_URL, headers=HDRS, verify=False, timeout=30)
        response.raise_for_status()
        
        # Read CSV data
        df_master = pd.read_csv(io.StringIO(response.text))
        logger.info(f"✅ Fetched {len(df_master)} securities from master list")
        
        # Clean column names
        df_master.columns = [col.strip().upper() for col in df_master.columns]
        
        # Filter supported series
        df_filtered = df_master[df_master["SERIES"].isin(SUPPORTED_SERIES)].copy()
        logger.info(f"Filtered to {len(df_filtered)} securities in supported series: {SUPPORTED_SERIES}")
        
        # Standardize column names to match schema
        column_mapping = {
            "SYMBOL": "symbol",
            "NAME OF COMPANY": "name_of_company", 
            "SERIES": "series",
            "DATE OF LISTING": "date_of_listing",
            "PAID UP VALUE": "paid_up_value",
            "MARKET LOT": "market_lot",
            "ISIN NUMBER": "isin_number",
            "FACE VALUE": "face_value"
        }
        
        # Rename columns that exist
        existing_columns = {k: v for k, v in column_mapping.items() if k in df_filtered.columns}
        df_filtered = df_filtered.rename(columns=existing_columns)
        
        # Add missing columns with default values
        required_columns = list(column_mapping.values())
        for col in required_columns:
            if col not in df_filtered.columns:
                if col == "paid_up_value":
                    df_filtered[col] = 10.0
                elif col == "market_lot":
                    df_filtered[col] = 1
                elif col == "face_value":
                    df_filtered[col] = 10.0
                else:
                    df_filtered[col] = ""
        
        # Create ticker column
        df_filtered["ticker"] = df_filtered["symbol"] + "_" + df_filtered["series"]
        
        # Convert date column
        if "date_of_listing" in df_filtered.columns:
            df_filtered["date_of_listing"] = pd.to_datetime(df_filtered["date_of_listing"], errors='coerce').dt.date
        
        # Select final columns
        final_columns = required_columns + ["ticker"]
        df_final = df_filtered[final_columns].copy()
        
        logger.info(f"✅ NSE Universe processed: {len(df_final)} securities")
        logger.info(f"Series distribution: {df_final['series'].value_counts().to_dict()}")
        
        return df_final
        
    except Exception as e:
        logger.error(f"❌ Error fetching NSE universe: {e}")
        raise

def build_and_save_universe():
    """Build universe data and save to MongoDB"""
    dep_type = os.getenv('DEP_TYPE', 'prod').lower()
    
    logger.info(f"🚀 Building universe data (DEP_TYPE={dep_type})...")
    
    # Initialize database
    initialize_database()
    
    try:
        if dep_type == 'mock':
            # Use mock data
            logger.info("🔧 Using mock universe data")
            universe_df = create_mock_universe()
        else:
            # Try to fetch real NSE data
            try:
                universe_df = fetch_nse_universe()
            except Exception as e:
                logger.error(f"❌ Failed to fetch real NSE data: {e}")
                raise
        
        # Save to MongoDB
        logger.info("💾 Saving universe data to MongoDB...")
        count = universe_dao.insert_securities(universe_df)
        
        logger.info(f"✅ Successfully saved {count} securities to MongoDB")
        logger.info(f"📊 Series distribution: {universe_df['series'].value_counts().to_dict()}")
        
        # Also save to parquet for backward compatibility (optional)
        pathlib.Path("data").mkdir(exist_ok=True) 
        universe_df.to_parquet("data/universe.parquet", index=False)
        logger.info("💾 Also saved to parquet file for backward compatibility")
        
        return universe_df
        
    except Exception as e:
        logger.error(f"❌ Failed to build universe: {e}")
        raise

if __name__ == "__main__":
    universe_df = build_and_save_universe()
    print(f"Universe built: {len(universe_df)} securities")