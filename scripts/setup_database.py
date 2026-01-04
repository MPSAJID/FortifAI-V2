#!/usr/bin/env python3
"""
Database Setup Script
Creates tables and initial data
"""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def get_connection_params():
    """Get database connection parameters"""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.getenv('DB_USER', 'fortifai'),
        'password': os.getenv('DB_PASSWORD', 'fortifai_secure_password'),
        'database': os.getenv('DB_NAME', 'fortifai_db')
    }

def create_database():
    """Create database if it doesn't exist"""
    params = get_connection_params()
    db_name = params.pop('database')
    
    try:
        conn = psycopg2.connect(**params, database='postgres')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        with conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if not cur.fetchone():
                cur.execute(f'CREATE DATABASE {db_name}')
                print(f"Database '{db_name}' created")
            else:
                print(f"Database '{db_name}' already exists")
        
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")
        sys.exit(1)

def run_migrations():
    """Run database migrations"""
    params = get_connection_params()
    
    try:
        conn = psycopg2.connect(**params)
        
        with conn.cursor() as cur:
            # Read and execute init.sql
            init_sql_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 'infrastructure', 'docker', 'init.sql'
            )
            
            if os.path.exists(init_sql_path):
                with open(init_sql_path, 'r') as f:
                    sql = f.read()
                cur.execute(sql)
                conn.commit()
                print("Migrations completed successfully")
            else:
                print("init.sql not found")
        
        conn.close()
    except Exception as e:
        print(f"Error running migrations: {e}")
        sys.exit(1)

def main():
    """Main function"""
    print("FortifAI Database Setup")
    print("=" * 40)
    
    create_database()
    run_migrations()
    
    print("\nDatabase setup complete!")

if __name__ == '__main__':
    main()
