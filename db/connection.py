"""
Stock-ML MongoDB Database Connection Manager
Handles MongoDB connections, connection pooling, and database operations.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

import pymongo
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from bson import ObjectId

from .config import db_config, Collections

# Setup logging
logger = logging.getLogger(__name__)


class DatabaseManager:
    """MongoDB connection and operations manager"""
    
    def __init__(self):
        self._sync_client = None
        self._async_client = None
        self._sync_db = None
        self._async_db = None
        self._indexes_created = False
    
    def connect_sync(self) -> MongoClient:
        """Get synchronous MongoDB client connection"""
        if self._sync_client is None:
            logger.info(f"Connecting to MongoDB: {db_config.MONGODB_URL}")
            self._sync_client = MongoClient(
                db_config.MONGODB_URL,
                **db_config.get_connection_params()
            )
            self._sync_db = self._sync_client[db_config.DB_NAME]
            logger.info(f"Connected to database: {db_config.DB_NAME}")
        return self._sync_client
    
    async def connect_async(self) -> AsyncIOMotorClient:
        """Get asynchronous MongoDB client connection"""
        if self._async_client is None:
            logger.info(f"Connecting to MongoDB (async): {db_config.MONGODB_URL}")
            self._async_client = AsyncIOMotorClient(
                db_config.MONGODB_URL,
                **db_config.get_connection_params()
            )
            self._async_db = self._async_client[db_config.DB_NAME]
            logger.info(f"Connected to database (async): {db_config.DB_NAME}")
        return self._async_client
    
    def get_sync_db(self):
        """Get synchronous database instance"""
        if self._sync_db is None:
            self.connect_sync()
        return self._sync_db
    
    async def get_async_db(self):
        """Get asynchronous database instance"""
        if self._async_db is None:
            await self.connect_async()
        return self._async_db
    
    def close_sync(self):
        """Close synchronous connection"""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
            self._sync_db = None
            logger.info("Closed synchronous MongoDB connection")
    
    def close_async(self):
        """Close asynchronous connection"""
        if self._async_client:
            self._async_client.close()
            self._async_client = None
            self._async_db = None
            logger.info("Closed asynchronous MongoDB connection")
    
    def create_indexes(self):
        """Create all required indexes for optimal performance"""
        if self._indexes_created:
            return
        
        db = self.get_sync_db()
        logger.info("Creating MongoDB indexes...")
        
        try:
            # Universe collection indexes
            universe = db[Collections.UNIVERSE]
            universe.create_index("ticker", unique=True)
            universe.create_index([("symbol", 1), ("series", 1)], unique=True)
            universe.create_index("series")
            
            # Prices collection indexes
            prices = db[Collections.PRICES]
            prices.create_index([("date", -1), ("ticker", 1)])
            prices.create_index([("ticker", 1), ("date", -1)])
            prices.create_index([("date", -1)])
            prices.create_index([("symbol", 1), ("series", 1), ("date", -1)])
            
            # News collection indexes
            news = db[Collections.NEWS]
            news.create_index([("date", -1), ("ticker", 1)])
            news.create_index([("date", -1)])
            news.create_index([("ticker", 1), ("date", -1)])
            
            # Features collection indexes
            features = db[Collections.FEATURES]
            features.create_index([("date", -1), ("ticker", 1)])
            features.create_index([("ticker", 1), ("date", -1)])
            features.create_index([("date", -1)])
            
            # Models collection indexes
            models = db[Collections.MODELS]
            models.create_index("model_id", unique=True)
            models.create_index([("is_active", 1), ("training_date", -1)])
            models.create_index([("training_date", -1)])
            
            # Predictions collection indexes
            predictions = db[Collections.PREDICTIONS]
            predictions.create_index([("prediction_date", -1), ("ticker", 1)])
            predictions.create_index([("target_date", -1), ("ticker", 1)])
            predictions.create_index([("ticker", 1), ("prediction_date", -1)])
            predictions.create_index([("model_id", 1), ("prediction_date", -1)])
            
            # Evaluations collection indexes
            evaluations = db[Collections.EVALUATIONS]
            evaluations.create_index([("evaluation_date", -1), ("ticker", 1)])
            evaluations.create_index([("ticker", 1), ("evaluation_date", -1)])
            evaluations.create_index([("model_id", 1), ("evaluation_date", -1)])
            evaluations.create_index([("prediction_date", -1)])
            
            self._indexes_created = True
            logger.info("✅ All MongoDB indexes created successfully")
            
        except Exception as e:
            logger.error(f"❌ Error creating indexes: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test MongoDB connection"""
        try:
            client = self.connect_sync()
            # Ping the database
            client.admin.command('ping')
            logger.info("✅ MongoDB connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB connection test failed: {e}")
            return False
    
    async def test_connection_async(self) -> bool:
        """Test MongoDB connection (async)"""
        try:
            client = await self.connect_async()
            # Ping the database
            await client.admin.command('ping')
            logger.info("✅ MongoDB async connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB async connection test failed: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            db = self.get_sync_db()
            stats = db.command("dbstats")
            
            # Get collection counts
            collection_stats = {}
            for collection_name in [
                Collections.UNIVERSE, Collections.PRICES, Collections.NEWS,
                Collections.FEATURES, Collections.MODELS, Collections.PREDICTIONS,
                Collections.EVALUATIONS
            ]:
                try:
                    count = db[collection_name].count_documents({})
                    collection_stats[collection_name] = count
                except Exception:
                    collection_stats[collection_name] = 0
            
            return {
                "database": db_config.DB_NAME,
                "environment": db_config.DEP_TYPE,
                "collections": stats.get("collections", 0),
                "data_size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
                "storage_size_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2),
                "index_size_mb": round(stats.get("indexSize", 0) / (1024 * 1024), 2),
                "collection_counts": collection_stats,
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {"error": str(e)}
    
    def list_all_databases(self) -> List[str]:
        """List all databases in MongoDB instance"""
        try:
            client = self.connect_sync()
            db_list = client.list_database_names()
            stock_ml_dbs = [db for db in db_list if db.startswith('stock_ml_')]
            logger.info(f"Found Stock-ML databases: {stock_ml_dbs}")
            return stock_ml_dbs
        except Exception as e:
            logger.error(f"Error listing databases: {e}")
            return []
    
    def get_environment_databases(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for both prod and mock databases"""
        try:
            client = self.connect_sync()
            environments = {}
            
            for env_type in ['prod', 'mock']:
                db_name = f"stock_ml_{env_type}"
                try:
                    db = client[db_name]
                    stats = db.command("dbstats")
                    
                    # Get collection counts
                    collection_stats = {}
                    for collection_name in [
                        Collections.UNIVERSE, Collections.PRICES, Collections.NEWS,
                        Collections.FEATURES, Collections.MODELS, Collections.PREDICTIONS,
                        Collections.EVALUATIONS
                    ]:
                        try:
                            count = db[collection_name].count_documents({})
                            collection_stats[collection_name] = count
                        except Exception:
                            collection_stats[collection_name] = 0
                    
                    environments[env_type] = {
                        "database": db_name,
                        "exists": True,
                        "collections": stats.get("collections", 0),
                        "data_size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
                        "collection_counts": collection_stats,
                        "total_documents": sum(collection_stats.values())
                    }
                    
                except Exception as e:
                    environments[env_type] = {
                        "database": db_name,
                        "exists": False,
                        "error": str(e),
                        "total_documents": 0
                    }
            
            return environments
            
        except Exception as e:
            logger.error(f"Error getting environment databases: {e}")
            return {}
    
    def clean_database(self, environment: str = None) -> bool:
        """Clean/drop database for specific environment (DANGEROUS!)"""
        if environment is None:
            environment = db_config.DEP_TYPE
            
        if environment not in ['prod', 'mock']:
            raise ValueError(f"Invalid environment '{environment}'. Must be 'prod' or 'mock'")
        
        try:
            client = self.connect_sync()
            db_name = f"stock_ml_{environment}"
            
            logger.warning(f"🚨 DROPPING DATABASE: {db_name}")
            client.drop_database(db_name)
            logger.info(f"✅ Database {db_name} dropped successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error dropping database: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


# Context managers for database connections
@asynccontextmanager
async def get_async_db():
    """Async context manager for database operations"""
    try:
        db = await db_manager.get_async_db()
        yield db
    except Exception as e:
        logger.error(f"Database operation error: {e}")
        raise
    # Connection cleanup is handled by connection pooling


def get_sync_db():
    """Get synchronous database instance"""
    return db_manager.get_sync_db()


# Utility functions
def ensure_datetime_fields(document: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure document has created_at and updated_at fields"""
    now = datetime.utcnow()
    if "created_at" not in document:
        document["created_at"] = now
    document["updated_at"] = now
    return document


def prepare_for_mongo(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for MongoDB insertion"""
    from datetime import date
    
    # Convert various date/time types to datetime for MongoDB
    for key, value in data.items():
        if isinstance(value, date) and not isinstance(value, datetime):
            # Convert date to datetime (midnight UTC)
            data[key] = datetime.combine(value, datetime.min.time())
        elif hasattr(value, 'to_pydatetime'):
            data[key] = value.to_pydatetime()
        elif hasattr(value, 'timestamp'):
            # Handle other timestamp types
            try:
                data[key] = datetime.fromtimestamp(value.timestamp())
            except:
                pass
    
    return ensure_datetime_fields(data)


if __name__ == "__main__":
    # Test database connection
    logging.basicConfig(level=logging.INFO)
    
    print("Testing MongoDB connection...")
    if db_manager.test_connection():
        print("Creating indexes...")
        db_manager.create_indexes()
        
        print("Getting database stats...")
        stats = db_manager.get_database_stats()
        print(f"Database stats: {stats}")
    else:
        print("❌ Connection failed")