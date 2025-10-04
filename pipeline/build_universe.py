import pandas as pd, requests, io, pathlib
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        # ETFs
        ("NIFTYBEES", "Nippon India ETF Nifty BeES", "ETF", "INF204KB17I5", "2002-01-08"),
        ("JUNIORBEES", "Nippon India ETF Junior BeES", "ETF", "INF204KB14I2", "2003-01-01"),
        ("BANKBEES", "Nippon India ETF Bank BeES", "ETF", "INF204KB1BK8", "2004-01-01"),
        # Mutual Funds
        ("HDFCMFGETF", "HDFC Mutual Fund Gold ETF", "MF", "INF179K01134", "2010-03-15"),
        ("ICICIMF", "ICICI Prudential Mutual Fund", "MF", "INF109K01242", "2008-06-12"),
        # Government Securities
        ("GSEC2030", "Government Security 2030", "GS", "IN0020240051", "2020-04-01"),
        ("GSEC2035", "Government Security 2035", "GS", "IN0020350049", "2021-02-15"),
    ]
    
    rows = []
    for symbol, name, series, isin, listing_date in stocks_data:
        rows.append({
            "symbol": symbol,
            "name_of_company": name,
            "series": series,
            "isin_number": isin,
            "date_of_listing": pd.to_datetime(listing_date).date(),
            "paid_up_value": 1,
            "market_lot": 1,
            "face_value": 1
        })
    
    df = pd.DataFrame(rows)
    print(f"Created mock universe with {len(df)} stocks")
    return df

def fetch_equity_master() -> pd.DataFrame:
    print(f"🚀 Fetching real NSE equity master from: {EQUITY_MASTER_URL}")
    
    enhanced_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }
    
    try:
        session = requests.Session()
        session.headers.update(enhanced_headers)
        
        print("📡 Downloading NSE equity master list...")
        r = session.get(EQUITY_MASTER_URL, timeout=20, verify=False)
        r.raise_for_status()
        
        print(f"📦 Downloaded {len(r.text)} characters")
        df = pd.read_csv(io.StringIO(r.text))
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        
        print(f"✅ Successfully fetched {len(df)} real NSE equity records!")
        
        # Show series distribution
        print("📊 Series distribution in master data:")
        for series, count in df['series'].value_counts().items():
            print(f"  {series}: {count} securities")
        
        session.close()
        return df
        
    except requests.exceptions.SSLError as e:
        error_msg = f"SSL Error accessing NSE archives: {str(e)[:100]}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)
    except requests.exceptions.Timeout as e:
        error_msg = f"Timeout accessing NSE archives: {str(e)[:100]}" 
        print(f"❌ {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Failed to fetch real NSE equity master: {str(e)[:100]}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)

def fetch_live_equity_list() -> pd.DataFrame:
    try:
        s = requests.Session()
        html = s.get(LIVE_EQ_URL, headers=HDRS, timeout=10, verify=False).text
        soup = BeautifulSoup(html, "html.parser")
        link = None
        for a in soup.find_all("a"):
            if a.text.strip().lower().startswith("securities available for equity segment"):
                link = a.get("href")
                break
        if not link:
            print("Warning: Could not find live equity list link, using master list only")
            return pd.DataFrame()
        
        # Handle both relative and absolute URLs
        if link.startswith('http'):
            csv_url = link
        else:
            # Ensure the link starts with '/' for proper URL construction
            if not link.startswith('/'):
                link = '/' + link
            csv_url = "https://www.nseindia.com" + link
        print(f"Fetching live equity list from: {csv_url}")
        csv = s.get(csv_url, headers=HDRS, timeout=10, verify=False)
        csv.raise_for_status()
        df = pd.read_csv(io.StringIO(csv.text))
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        return df
    except Exception as e:
        print(f"Warning: Failed to fetch live equity list: {e}")
        print("Falling back to master list only")
        return pd.DataFrame()

def make_universe() -> pd.DataFrame:
    print("🌍 Building NSE universe with real data...")
    
    # Fetch master equity list (required)
    master = fetch_equity_master()
    
    # Try to fetch live equity list (optional enhancement)
    live = fetch_live_equity_list()
    
    if not live.empty:
        print(f"🔗 Merging master ({len(master)}) with live equity list ({len(live)})")
        uni = master.merge(live[["symbol","series"]].drop_duplicates(), on=["symbol","series"], how="inner")
        print(f"📊 After merge: {len(uni)} securities")
    else:
        print("⚠️  Using master list only (live list unavailable)")
        uni = master[master["series"].isin(SUPPORTED_SERIES)].copy()
        print(f"📊 After filtering for supported series: {len(uni)} securities")
    
    # Clean up symbols
    uni["symbol"] = uni["symbol"].str.upper()
    
    # Show final distribution
    print(f"\n🎯 Final Universe Composition:")
    for series in SUPPORTED_SERIES:
        count = len(uni[uni["series"] == series])
        if count > 0:
            print(f"  {series}: {count} securities")
    
    # Save to file
    pathlib.Path("data").mkdir(exist_ok=True)
    uni.to_parquet("data/universe.parquet", index=False)
    print(f"\n💾 Saved universe with {len(uni)} real NSE securities!")
    
    return uni

if __name__ == "__main__":
    make_universe()
