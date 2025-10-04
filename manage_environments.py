#!/usr/bin/env python3
"""
Stock-ML Environment Management
Manage separate MongoDB databases for production and mock environments.
"""
import os, sys, pathlib

# Add project root to path  
project_root = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from db import db_manager, db_config, verify_environment, switch_environment


def show_environment_status():
    """Show detailed status of both environments"""
    print("\n" + "="*60)
    print("🔧 STOCK-ML ENVIRONMENT STATUS")
    print("="*60)
    
    # Current environment
    current_env = verify_environment()
    
    # Get both environments
    print("\n📊 DATABASE OVERVIEW:")
    print("-" * 40)
    
    env_dbs = db_manager.get_environment_databases()
    
    for env_type, info in env_dbs.items():
        status = "✅ EXISTS" if info.get('exists', False) else "❌ MISSING"
        total_docs = info.get('total_documents', 0)
        
        print(f"\n{env_type.upper()} Environment:")
        print(f"  Database: {info['database']}")
        print(f"  Status: {status}")
        print(f"  Total Documents: {total_docs:,}")
        
        if info.get('exists', False):
            print(f"  Collections: {info.get('collections', 0)}")
            print(f"  Data Size: {info.get('data_size_mb', 0)} MB")
            
            # Collection breakdown
            collection_counts = info.get('collection_counts', {})
            for collection, count in collection_counts.items():
                if count > 0:
                    print(f"    - {collection}: {count:,} documents")
    
    print("\n" + "="*60)


def create_environment(env_type: str):
    """Create and initialize a new environment"""
    if env_type not in ['prod', 'mock']:
        print(f"❌ Invalid environment '{env_type}'. Use 'prod' or 'mock'")
        return False
    
    print(f"\n🔧 Creating {env_type.upper()} environment...")
    
    # Switch to the environment
    switch_environment(env_type)
    
    # Initialize database (creates indexes)
    from db import initialize_database
    initialize_database()
    
    print(f"✅ {env_type.upper()} environment created successfully!")
    return True


def populate_mock_environment():
    """Populate mock environment with sample data"""
    print("\n🔧 Populating MOCK environment with sample data...")
    
    # Switch to mock environment
    switch_environment('mock')
    
    # Run universe builder
    try:
        from pipeline.build_universe_mongo import build_and_save_universe
        universe_df = build_and_save_universe()
        print(f"✅ Mock universe created: {len(universe_df)} securities")
        return True
    except Exception as e:
        print(f"❌ Error populating mock environment: {e}")
        return False


def clean_environment(env_type: str, confirm: bool = False):
    """Clean/drop environment database"""
    if env_type not in ['prod', 'mock']:
        print(f"❌ Invalid environment '{env_type}'. Use 'prod' or 'mock'")
        return False
    
    if not confirm:
        print(f"🚨 WARNING: This will DELETE ALL data in {env_type.upper()} environment!")
        response = input(f"Type 'DELETE {env_type.upper()}' to confirm: ")
        if response != f"DELETE {env_type.upper()}":
            print("❌ Operation cancelled")
            return False
    
    print(f"\n🚨 Cleaning {env_type.upper()} environment...")
    success = db_manager.clean_database(env_type)
    
    if success:
        print(f"✅ {env_type.upper()} environment cleaned successfully!")
    else:
        print(f"❌ Failed to clean {env_type.upper()} environment")
    
    return success


def switch_to_environment(env_type: str):
    """Switch active environment"""
    if env_type not in ['prod', 'mock']:
        print(f"❌ Invalid environment '{env_type}'. Use 'prod' or 'mock'")
        return False
    
    print(f"\n🔄 Switching to {env_type.upper()} environment...")
    switch_environment(env_type)
    
    # Verify switch
    verify_environment()
    return True


def main():
    """Main environment management interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Stock-ML Environment Management")
    parser.add_argument('command', choices=[
        'status', 'create', 'switch', 'clean', 'populate-mock'
    ], help='Command to execute')
    parser.add_argument('--env', choices=['prod', 'mock'], 
                       help='Environment to operate on')
    parser.add_argument('--confirm', action='store_true',
                       help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'status':
            show_environment_status()
        
        elif args.command == 'create':
            if not args.env:
                print("❌ --env required for create command")
                return
            create_environment(args.env)
        
        elif args.command == 'switch':
            if not args.env:
                print("❌ --env required for switch command")
                return
            switch_to_environment(args.env)
        
        elif args.command == 'clean':
            if not args.env:
                print("❌ --env required for clean command")
                return
            clean_environment(args.env, args.confirm)
        
        elif args.command == 'populate-mock':
            populate_mock_environment()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())