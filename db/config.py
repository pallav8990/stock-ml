"""
Stock-ML Database Configuration
MongoDB connection settings and environment configuration.
"""
import os
from typing import Optional

# Database configuration
class DatabaseConfig:
    """MongoDB connection and database settings"""
    
    def __init__(self):
        # MongoDB connection settings
        self.MONGODB_URL = os.getenv(
            'MONGODB_URL', 
            'mongodb://localhost:27017'
        )
        
        # Environment type - critical for database separation
        self.DEP_TYPE = os.getenv('DEP_TYPE', 'prod').lower()
        
        # Validate DEP_TYPE
        if self.DEP_TYPE not in ['prod', 'mock']:
            raise ValueError(f"Invalid DEP_TYPE '{self.DEP_TYPE}'. Must be 'prod' or 'mock'")
        
        # Database name based on environment - STRICT separation
        self.DB_NAME = os.getenv(
            'DB_NAME', 
            f"stock_ml_{self.DEP_TYPE}"
        )
        
        # Ensure database names are always environment-specific
        if not self.DB_NAME.endswith('_prod') and not self.DB_NAME.endswith('_mock'):
            self.DB_NAME = f"{self.DB_NAME}_{self.DEP_TYPE}"
        
        # Connection pool settings
        self.MAX_POOL_SIZE = int(os.getenv('MONGO_MAX_POOL_SIZE', '10'))
        self.MIN_POOL_SIZE = int(os.getenv('MONGO_MIN_POOL_SIZE', '1'))
        self.MAX_IDLE_TIME = int(os.getenv('MONGO_MAX_IDLE_TIME', '30000'))  # ms
        
        # Connection timeouts
        self.CONNECT_TIMEOUT = int(os.getenv('MONGO_CONNECT_TIMEOUT', '10000'))  # ms
        self.SERVER_SELECTION_TIMEOUT = int(os.getenv('MONGO_SERVER_TIMEOUT', '5000'))  # ms
        
        # Data retention settings (days)
        self.PRICE_DATA_RETENTION_DAYS = int(os.getenv('PRICE_RETENTION_DAYS', '365'))
        self.PREDICTION_RETENTION_DAYS = int(os.getenv('PREDICTION_RETENTION_DAYS', '90'))
        self.EVALUATION_RETENTION_DAYS = int(os.getenv('EVALUATION_RETENTION_DAYS', '180'))
        
    def get_connection_params(self) -> dict:
        """Get MongoDB connection parameters"""
        return {
            'maxPoolSize': self.MAX_POOL_SIZE,
            'minPoolSize': self.MIN_POOL_SIZE,
            'maxIdleTimeMS': self.MAX_IDLE_TIME,
            'connectTimeoutMS': self.CONNECT_TIMEOUT,
            'serverSelectionTimeoutMS': self.SERVER_SELECTION_TIMEOUT,
            'retryWrites': True,
            'retryReads': True
        }
    
    def get_environment_info(self) -> dict:
        """Get detailed environment information"""
        return {
            'dep_type': self.DEP_TYPE,
            'database_name': self.DB_NAME,
            'mongodb_url': self.MONGODB_URL,
            'is_production': self.DEP_TYPE == 'prod',
            'is_mock': self.DEP_TYPE == 'mock'
        }
    
    def __str__(self) -> str:
        return f"DatabaseConfig(env='{self.DEP_TYPE}', url='{self.MONGODB_URL}', db='{self.DB_NAME}')"


# Global config instance
db_config = DatabaseConfig()

# Collection names
class Collections:
    """MongoDB collection names"""
    UNIVERSE = "universe"
    PRICES = "prices"
    NEWS = "news"
    FEATURES = "features"
    MODELS = "models"
    PREDICTIONS = "predictions"
    EVALUATIONS = "evaluations"


# Environment variables help text
def print_env_help():
    """Print environment variables help"""
    print("""
MongoDB Environment Variables:
==============================

Required:
  MONGODB_URL          MongoDB connection string (default: mongodb://localhost:27017)
  
Optional:
  DB_NAME              Database name (default: stock_ml_{DEP_TYPE})
  DEP_TYPE             Environment type: prod/mock (default: prod)
  
Connection Pool:
  MONGO_MAX_POOL_SIZE  Maximum connections (default: 10)
  MONGO_MIN_POOL_SIZE  Minimum connections (default: 1)
  MONGO_MAX_IDLE_TIME  Max idle time in ms (default: 30000)
  MONGO_CONNECT_TIMEOUT    Connection timeout in ms (default: 10000)
  MONGO_SERVER_TIMEOUT     Server selection timeout in ms (default: 5000)
  
Data Retention:
  PRICE_RETENTION_DAYS      Price data retention (default: 365)
  PREDICTION_RETENTION_DAYS Prediction retention (default: 90)
  EVALUATION_RETENTION_DAYS Evaluation retention (default: 180)

Example:
  export MONGODB_URL="mongodb://localhost:27017"
  export DB_NAME="stock_ml_dev"
  export DEP_TYPE="mock"
""")


def switch_environment(new_dep_type: str) -> None:
    """
    Switch to a different environment (prod/mock) - DANGEROUS OPERATION
    This will change the global database configuration
    """
    global db_config
    
    if new_dep_type.lower() not in ['prod', 'mock']:
        raise ValueError(f"Invalid environment '{new_dep_type}'. Must be 'prod' or 'mock'")
    
    # Update environment variable
    os.environ['DEP_TYPE'] = new_dep_type.lower()
    
    # Force database manager to refresh connections
    from .connection import db_manager
    db_manager.close_sync()
    db_manager.close_async()
    db_manager._indexes_created = False
    
    # Recreate config instance - this must be after closing connections
    db_config = DatabaseConfig()
    
    print(f"🔄 Environment switched to: {db_config.DEP_TYPE}")
    print(f"📊 New database: {db_config.DB_NAME}")


def verify_environment() -> dict:
    """Verify current environment setup and database separation"""
    current_env = db_config.get_environment_info()
    
    print(f"""
🔧 Environment Verification:
============================
🎯 Current Environment: {current_env['dep_type'].upper()}
📊 Database Name: {current_env['database_name']}
🌐 MongoDB URL: {current_env['mongodb_url']}
✅ Production Mode: {current_env['is_production']}
🔧 Mock Mode: {current_env['is_mock']}

Expected Database Names:
- Production: stock_ml_prod
- Mock/Development: stock_ml_mock
""")
    
    return current_env


if __name__ == "__main__":
    print("MongoDB Environment Configuration:")
    print("=" * 50)
    verify_environment()
    print_env_help()