#!/usr/bin/env python3
"""
Load existing parquet data into MongoDB for Stock-ML application.
This script transfers data from parquet files to MongoDB collections.
"""

import os
import pandas as pd
import logging
from datetime import datetime
from db.connection import db_manager
from db.config import Collections

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data_to_mongodb():
    """Load existing parquet data into MongoDB collections."""
    
    # Use the global database manager instance
    
    data_dir = "data"
    
    # Check if data files exist
    required_files = [
        "predictions_daily.parquet",
        "eval_explain_daily.parquet", 
        "universe.parquet",
        "prices_daily.parquet"
    ]
    
    for file in required_files:
        filepath = os.path.join(data_dir, file)
        if not os.path.exists(filepath):
            logger.error(f"❌ Required file not found: {filepath}")
            return False
    
    try:
        # Get database connection
        db = db_manager.get_sync_db()
        
        # Load predictions
        logger.info("📊 Loading predictions data...")
        predictions_df = pd.read_parquet(os.path.join(data_dir, "predictions_daily.parquet"))
        
        if len(predictions_df) > 0:
            # Convert date columns to datetime for MongoDB compatibility
            for col in predictions_df.columns:
                if 'date' in col.lower() and predictions_df[col].dtype == 'object':
                    predictions_df[col] = pd.to_datetime(predictions_df[col])
                elif predictions_df[col].dtype.name == 'date':
                    predictions_df[col] = pd.to_datetime(predictions_df[col])
            
            # Convert DataFrame to records and insert
            predictions_records = predictions_df.to_dict('records')
            
            # Clear existing predictions
            db[Collections.PREDICTIONS].delete_many({})
            
            # Insert new predictions
            result = db[Collections.PREDICTIONS].insert_many(predictions_records)
            logger.info(f"✅ Inserted {len(result.inserted_ids)} predictions")
        else:
            logger.warning("⚠️  No predictions data found in parquet file")
        
        # Load evaluation/explanation data
        logger.info("📊 Loading evaluation data...")
        eval_df = pd.read_parquet(os.path.join(data_dir, "eval_explain_daily.parquet"))
        
        if len(eval_df) > 0:
            # Convert date columns to datetime for MongoDB compatibility
            for col in eval_df.columns:
                if 'date' in col.lower() and eval_df[col].dtype == 'object':
                    eval_df[col] = pd.to_datetime(eval_df[col])
                elif eval_df[col].dtype.name == 'date':
                    eval_df[col] = pd.to_datetime(eval_df[col])
            
            eval_records = eval_df.to_dict('records')
            
            # Clear existing evaluations
            db[Collections.EVALUATIONS].delete_many({})
            
            # Insert new evaluations
            result = db[Collections.EVALUATIONS].insert_many(eval_records)
            logger.info(f"✅ Inserted {len(result.inserted_ids)} evaluation records")
        
        # Load universe data
        logger.info("📊 Loading universe data...")
        universe_df = pd.read_parquet(os.path.join(data_dir, "universe.parquet"))
        
        if len(universe_df) > 0:
            # Filter out records with null tickers to avoid duplicate key errors
            universe_df_clean = universe_df.dropna(subset=['ticker']) if 'ticker' in universe_df.columns else universe_df.dropna(subset=['symbol'])
            
            # Also create a ticker column if it doesn't exist
            if 'ticker' not in universe_df_clean.columns and 'symbol' in universe_df_clean.columns:
                universe_df_clean = universe_df_clean.copy()
                universe_df_clean['ticker'] = universe_df_clean['symbol']
            
            universe_records = universe_df_clean.to_dict('records')
            
            # Clear existing universe
            db[Collections.UNIVERSE].delete_many({})
            
            # Insert new universe
            result = db[Collections.UNIVERSE].insert_many(universe_records)
            logger.info(f"✅ Inserted {len(result.inserted_ids)} universe records")
        
        # Load prices data (sample for accuracy calculations)
        logger.info("📊 Loading prices data...")
        prices_df = pd.read_parquet(os.path.join(data_dir, "prices_daily.parquet"))
        
        if len(prices_df) > 0:
            # Convert date columns to datetime for MongoDB compatibility
            for col in prices_df.columns:
                if 'date' in col.lower() and prices_df[col].dtype == 'object':
                    prices_df[col] = pd.to_datetime(prices_df[col])
                elif prices_df[col].dtype.name == 'date':
                    prices_df[col] = pd.to_datetime(prices_df[col])
            
            # Take recent data only to avoid large insertions
            recent_prices = prices_df.tail(1000)  # Last 1k records to be faster
            prices_records = recent_prices.to_dict('records')
            
            # Clear existing prices
            db[Collections.PRICES].delete_many({})
            
            # Insert prices
            result = db[Collections.PRICES].insert_many(prices_records)
            logger.info(f"✅ Inserted {len(result.inserted_ids)} price records")
        
        logger.info("🎉 Successfully loaded all data into MongoDB!")
        
        # Print summary
        logger.info("\n📈 Database Summary:")
        logger.info(f"   Predictions: {db[Collections.PREDICTIONS].count_documents({})}")
        logger.info(f"   Evaluations: {db[Collections.EVALUATIONS].count_documents({})}")  
        logger.info(f"   Universe: {db[Collections.UNIVERSE].count_documents({})}")
        logger.info(f"   Prices: {db[Collections.PRICES].count_documents({})}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading data: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Loading existing parquet data into MongoDB...")
    success = load_data_to_mongodb()
    
    if success:
        logger.info("✅ Data loading completed successfully!")
        exit(0)
    else:
        logger.error("❌ Data loading failed!")
        exit(1)