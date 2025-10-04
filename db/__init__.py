"""
Stock-ML Database Module
MongoDB integration for Stock-ML pipeline.
"""

from .config import db_config, Collections, print_env_help, verify_environment, switch_environment
from .connection import db_manager, get_sync_db, get_async_db, ensure_datetime_fields, prepare_for_mongo
from .models import (
    universe_dao, prices_dao, news_dao, features_dao, predictions_dao,
    UniverseDAO, PricesDAO, NewsDAO, FeaturesDAO, PredictionsDAO,
    DataAccessError
)

__all__ = [
    # Configuration
    'db_config',
    'Collections',
    'print_env_help',
    'verify_environment', 
    'switch_environment',
    
    # Connection management
    'db_manager',
    'get_sync_db',
    'get_async_db',
    'ensure_datetime_fields',
    'prepare_for_mongo',
    
    # Data Access Objects (instances)
    'universe_dao',
    'prices_dao', 
    'news_dao',
    'features_dao',
    'predictions_dao',
    
    # Data Access Classes
    'UniverseDAO',
    'PricesDAO',
    'NewsDAO', 
    'FeaturesDAO',
    'PredictionsDAO',
    
    # Exceptions
    'DataAccessError'
]


def initialize_database():
    """Initialize database connection and create indexes"""
    print("🔧 Initializing MongoDB connection...")
    
    # Test connection
    if not db_manager.test_connection():
        raise ConnectionError("Failed to connect to MongoDB")
    
    # Create indexes
    db_manager.create_indexes()
    
    print(f"✅ Database initialized: {db_config.DB_NAME}")
    print(f"📊 Connection: {db_config.MONGODB_URL}")


def get_database_info():
    """Get current database configuration and stats"""
    return {
        'config': str(db_config),
        'stats': db_manager.get_database_stats()
    }