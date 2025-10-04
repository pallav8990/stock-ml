"""
Stock-ML MongoDB Data Models and CRUD Operations
Provides high-level data access methods for all collections.
"""
import logging
import os
import pickle
import base64
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from bson import ObjectId
import numpy as np
import pymongo

from .connection import get_sync_db, prepare_for_mongo, ensure_datetime_fields
from .config import Collections

logger = logging.getLogger(__name__)


class DataAccessError(Exception):
    """Custom exception for data access errors"""
    pass


class UniverseDAO:
    """Data Access Object for Universe collection"""
    
    def __init__(self):
        self.collection_name = Collections.UNIVERSE
    
    def insert_securities(self, securities_df: pd.DataFrame) -> int:
        """Insert securities data from DataFrame"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            # Convert DataFrame to records
            records = securities_df.to_dict('records')
            
            # Prepare each record for MongoDB
            for record in records:
                record = prepare_for_mongo(record)
                # Create ticker if not exists
                if 'ticker' not in record and 'symbol' in record and 'series' in record:
                    record['ticker'] = f"{record['symbol']}_{record['series']}"
            
            # Upsert records (update if exists, insert if new)
            operations = []
            for record in records:
                operations.append(
                    pymongo.ReplaceOne(
                        {"ticker": record["ticker"]},
                        record,
                        upsert=True
                    )
                )
            
            if operations:
                result = collection.bulk_write(operations)
                logger.info(f"Universe: Inserted {result.upserted_count}, Modified {result.modified_count} securities")
                return result.upserted_count + result.modified_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Error inserting universe data: {e}")
            raise DataAccessError(f"Failed to insert universe data: {e}")
    
    def get_all_tickers(self) -> List[str]:
        """Get all ticker symbols"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            tickers = collection.distinct("ticker")
            return sorted(tickers)
        except Exception as e:
            logger.error(f"Error getting tickers: {e}")
            return []
    
    def get_securities_by_series(self, series: str) -> List[Dict]:
        """Get securities by series type (EQ, BE, etc.)"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            return list(collection.find({"series": series}))
        except Exception as e:
            logger.error(f"Error getting securities by series: {e}")
            return []


class PricesDAO:
    """Data Access Object for Prices collection"""
    
    def __init__(self):
        self.collection_name = Collections.PRICES
    
    def insert_prices(self, prices_df: pd.DataFrame, data_source: str = "nse_bhavcopy") -> int:
        """Insert price data from DataFrame"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            # Convert DataFrame to records
            records = prices_df.to_dict('records')
            
            # Prepare each record for MongoDB
            for record in records:
                record = prepare_for_mongo(record)
                record['data_source'] = data_source
                record['dep_type'] = os.getenv('DEP_TYPE', 'prod')
                
                # Ensure ticker exists
                if 'ticker' not in record and 'symbol' in record and 'series' in record:
                    record['ticker'] = f"{record['symbol']}_{record['series']}"
            
            # Upsert records based on date + ticker
            operations = []
            for record in records:
                operations.append(
                    pymongo.ReplaceOne(
                        {"date": record["date"], "ticker": record["ticker"]},
                        record,
                        upsert=True
                    )
                )
            
            if operations:
                result = collection.bulk_write(operations)
                logger.info(f"Prices: Inserted {result.upserted_count}, Modified {result.modified_count} records")
                return result.upserted_count + result.modified_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Error inserting price data: {e}")
            raise DataAccessError(f"Failed to insert price data: {e}")
    
    def get_prices_for_date(self, target_date: Union[date, datetime]) -> pd.DataFrame:
        """Get all prices for a specific date"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            # Convert date to datetime for MongoDB query
            if isinstance(target_date, date):
                target_date = datetime.combine(target_date, datetime.min.time())
            
            cursor = collection.find({"date": target_date})
            records = list(cursor)
            
            if records:
                return pd.DataFrame(records)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting prices for date {target_date}: {e}")
            return pd.DataFrame()
    
    def get_prices_for_ticker(self, ticker: str, days: int = 30) -> pd.DataFrame:
        """Get price history for a ticker"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            cursor = collection.find(
                {"ticker": ticker}
            ).sort("date", -1).limit(days)
            
            records = list(cursor)
            
            if records:
                df = pd.DataFrame(records)
                return df.sort_values("date")
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting prices for ticker {ticker}: {e}")
            return pd.DataFrame()
    
    def get_all_prices(self, days: int = None) -> pd.DataFrame:
        """Get all price data, optionally limited by days from latest date"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            if days:
                # Get the latest date and then filter by date range
                pipeline = [
                    {"$group": {"_id": None, "max_date": {"$max": "$date"}}},
                ]
                max_date_result = list(collection.aggregate(pipeline))
                
                if max_date_result:
                    max_date = max_date_result[0]["max_date"]
                    from datetime import timedelta
                    cutoff_date = max_date - timedelta(days=days)
                    cursor = collection.find({"date": {"$gte": cutoff_date}})
                else:
                    cursor = collection.find({})
            else:
                cursor = collection.find({})
            
            records = list(cursor)
            
            if records:
                df = pd.DataFrame(records)
                # Remove MongoDB _id field if present
                if '_id' in df.columns:
                    df = df.drop('_id', axis=1)
                return df.sort_values(["ticker", "date"])
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting all prices: {e}")
            return pd.DataFrame()


class NewsDAO:
    """Data Access Object for News collection"""
    
    def __init__(self):
        self.collection_name = Collections.NEWS
    
    def insert_news(self, news_df: pd.DataFrame, data_source: str = "rss_feeds") -> int:
        """Insert news articles from DataFrame"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            # Convert DataFrame to records
            records = news_df.to_dict('records')
            
            # Prepare each record for MongoDB
            for record in records:
                record = prepare_for_mongo(record)
                record['data_source'] = data_source
                record['dep_type'] = os.getenv('DEP_TYPE', 'prod')
            
            # Upsert records based on date + ticker + headline (to avoid duplicates)
            operations = []
            for record in records:
                operations.append(
                    pymongo.ReplaceOne(
                        {
                            "date": record["date"], 
                            "ticker": record["ticker"],
                            "headline": record["headline"]
                        },
                        record,
                        upsert=True
                    )
                )
            
            if operations:
                result = collection.bulk_write(operations)
                logger.info(f"News: Inserted {result.upserted_count}, Modified {result.modified_count} articles")
                return result.upserted_count + result.modified_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Error inserting news data: {e}")
            raise DataAccessError(f"Failed to insert news data: {e}")

    def insert_news_sentiment(self, news_data: Dict[str, Any]) -> bool:
        """Insert aggregated news sentiment data"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            # Prepare data for MongoDB
            news_data = prepare_for_mongo(news_data)
            
            # Upsert based on date + ticker
            result = collection.replace_one(
                {"date": news_data["date"], "ticker": news_data.get("ticker", "_MARKET_")},
                news_data,
                upsert=True
            )
            
            logger.info(f"News: {'Updated' if result.modified_count else 'Inserted'} sentiment for {news_data['date']}")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting news data: {e}")
            raise DataAccessError(f"Failed to insert news data: {e}")
    
    def get_market_sentiment_for_date(self, target_date: Union[date, datetime]) -> Dict[str, float]:
        """Get market sentiment for a date"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            if isinstance(target_date, date):
                target_date = datetime.combine(target_date, datetime.min.time())
            
            record = collection.find_one({
                "date": target_date, 
                "ticker": "_MARKET_"
            })
            
            if record:
                return {
                    "sentiment_mean": record.get("sentiment_mean", 0),
                    "sentiment_max": record.get("sentiment_max", 0),
                    "news_count": record.get("news_count", 0)
                }
            else:
                return {"sentiment_mean": 0, "sentiment_max": 0, "news_count": 0}
                
        except Exception as e:
            logger.error(f"Error getting market sentiment: {e}")
            return {"sentiment_mean": 0, "sentiment_max": 0, "news_count": 0}
    
    def get_all_news(self, days: int = None) -> pd.DataFrame:
        """Get all news data, optionally limited by days from latest date"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            if days:
                # Get the latest date and then filter by date range
                pipeline = [
                    {"$group": {"_id": None, "max_date": {"$max": "$date"}}},
                ]
                max_date_result = list(collection.aggregate(pipeline))
                
                if max_date_result:
                    max_date = max_date_result[0]["max_date"]
                    from datetime import timedelta
                    cutoff_date = max_date - timedelta(days=days)
                    cursor = collection.find({"date": {"$gte": cutoff_date}})
                else:
                    cursor = collection.find({})
            else:
                cursor = collection.find({})
            
            records = list(cursor)
            
            if records:
                df = pd.DataFrame(records)
                # Remove MongoDB _id field if present
                if '_id' in df.columns:
                    df = df.drop('_id', axis=1)
                return df.sort_values("date")
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting all news: {e}")
            return pd.DataFrame()


class FeaturesDAO:
    """Data Access Object for Features collection"""
    
    def __init__(self):
        self.collection_name = Collections.FEATURES
    
    def insert_features(self, features_df: pd.DataFrame) -> int:
        """Insert features data from DataFrame"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            # Convert DataFrame to records
            records = features_df.to_dict('records')
            
            # Prepare each record for MongoDB
            for record in records:
                # Handle NaN values (MongoDB doesn't support NaN)
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
                
                record = prepare_for_mongo(record)
            
            # Upsert records based on date + ticker
            operations = []
            for record in records:
                operations.append(
                    pymongo.ReplaceOne(
                        {"date": record["date"], "ticker": record["ticker"]},
                        record,
                        upsert=True
                    )
                )
            
            if operations:
                result = collection.bulk_write(operations)
                logger.info(f"Features: Inserted {result.upserted_count}, Modified {result.modified_count} records")
                return result.upserted_count + result.modified_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Error inserting features data: {e}")
            raise DataAccessError(f"Failed to insert features data: {e}")
    
    def get_latest_features(self, lookback_days: int = 5) -> pd.DataFrame:
        """Get latest features for all tickers"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            # Get features from last N days
            cursor = collection.find({}).sort("date", -1).limit(lookback_days * 1000)  # Approximate
            records = list(cursor)
            
            if records:
                df = pd.DataFrame(records)
                # Handle None values back to NaN
                df = df.where(pd.notnull(df), np.nan)
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting latest features: {e}")
            return pd.DataFrame()


class ModelsDAO:
    """Data Access Object for Models collection"""
    
    def __init__(self):
        self.collection_name = Collections.MODELS
    
    def save_model(self, model_data: Dict[str, Any]) -> str:
        """Save trained model to MongoDB"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            # Generate model ID
            model_id = f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            model_data['model_id'] = model_id
            
            # Prepare data for MongoDB
            model_data = prepare_for_mongo(model_data)
            
            # Deactivate any existing active models
            collection.update_many(
                {"is_active": True},
                {"$set": {"is_active": False}}
            )
            
            # Insert new model
            result = collection.insert_one(model_data)
            logger.info(f"Model saved with ID: {model_id}")
            
            return model_id
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise DataAccessError(f"Failed to save model: {e}")
    
    def get_active_model(self) -> Dict[str, Any]:
        """Get the currently active model"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            model = collection.find_one({"is_active": True})
            
            if model:
                return model
            else:
                logger.warning("No active model found")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting active model: {e}")
            return {}
    
    def load_model_object(self, model_id: str = None):
        """Load and deserialize model object"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            if model_id:
                model_record = collection.find_one({"model_id": model_id})
            else:
                model_record = collection.find_one({"is_active": True})
            
            if model_record and 'model_data' in model_record:
                # Decode base64 and deserialize
                model_bytes = base64.b64decode(model_record['model_data'].encode('utf-8'))
                model_obj, feat_cols = pickle.loads(model_bytes)
                return model_obj, feat_cols
            else:
                logger.warning(f"No model found: {model_id}")
                return None, None
                
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None, None


class PredictionsDAO:
    """Data Access Object for Predictions collection"""
    
    def __init__(self):
        self.collection_name = Collections.PREDICTIONS
    
    def insert_predictions(self, predictions_df: pd.DataFrame, model_id: str) -> int:
        """Insert predictions from DataFrame"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            # Convert DataFrame to records
            records = predictions_df.to_dict('records')
            
            # Prepare each record for MongoDB
            for record in records:
                record = prepare_for_mongo(record)
                record['model_id'] = model_id
                
                # Set prediction_date and target_date
                if 'date' in record:
                    record['prediction_date'] = record['date']
                    # Target date is the next day (what we're predicting)
                    next_day = record['date'] + pd.Timedelta(days=1)
                    record['target_date'] = next_day
            
            # Upsert records
            operations = []
            for record in records:
                operations.append(
                    pymongo.ReplaceOne(
                        {
                            "prediction_date": record["prediction_date"],
                            "ticker": record["ticker"],
                            "model_id": model_id
                        },
                        record,
                        upsert=True
                    )
                )
            
            if operations:
                result = collection.bulk_write(operations)
                logger.info(f"Predictions: Inserted {result.upserted_count}, Modified {result.modified_count} records")
                return result.upserted_count + result.modified_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Error inserting predictions: {e}")
            raise DataAccessError(f"Failed to insert predictions: {e}")
    
    def get_latest_predictions(self) -> pd.DataFrame:
        """Get latest predictions for all tickers"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            # Get latest predictions
            cursor = collection.find({}).sort("prediction_date", -1).limit(1000)
            records = list(cursor)
            
            if records:
                df = pd.DataFrame(records)
                # Remove MongoDB _id field if present
                if '_id' in df.columns:
                    df = df.drop('_id', axis=1)
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting latest predictions: {e}")
            return pd.DataFrame()


class EvaluationsDAO:
    """Data Access Object for Evaluations collection"""
    
    def __init__(self):
        self.collection_name = Collections.EVALUATIONS
    
    def insert_evaluations(self, evaluations_df: pd.DataFrame) -> int:
        """Insert evaluation results from DataFrame"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            # Convert DataFrame to records
            records = evaluations_df.to_dict('records')
            
            # Prepare each record for MongoDB
            for record in records:
                record = prepare_for_mongo(record)
                record['dep_type'] = os.getenv('DEP_TYPE', 'prod')
            
            # Upsert records based on target_date + ticker
            operations = []
            for record in records:
                operations.append(
                    pymongo.ReplaceOne(
                        {
                            "target_date": record["target_date"],
                            "ticker": record["ticker"]
                        },
                        record,
                        upsert=True
                    )
                )
            
            if operations:
                result = collection.bulk_write(operations)
                logger.info(f"Evaluations: Inserted {result.upserted_count}, Modified {result.modified_count} records")
                return result.upserted_count + result.modified_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Error inserting evaluation data: {e}")
            raise DataAccessError(f"Failed to insert evaluation data: {e}")
    
    def get_latest_evaluations(self, days: int = 30) -> pd.DataFrame:
        """Get recent evaluation results"""
        try:
            db = get_sync_db()
            collection = db[self.collection_name]
            
            cursor = collection.find({}).sort("target_date", -1).limit(days * 100)  # Approximate
            records = list(cursor)
            
            if records:
                df = pd.DataFrame(records)
                # Remove MongoDB _id field
                if '_id' in df.columns:
                    df = df.drop('_id', axis=1)
                return df.sort_values("target_date", ascending=False)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting latest evaluations: {e}")
            return pd.DataFrame()


# Global DAO instances
universe_dao = UniverseDAO()
prices_dao = PricesDAO()
news_dao = NewsDAO()
features_dao = FeaturesDAO()
predictions_dao = PredictionsDAO()
evaluations_dao = EvaluationsDAO()


# Import pymongo for bulk operations
import pymongo
import os