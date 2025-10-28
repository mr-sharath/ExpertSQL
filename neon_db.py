from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Neon connection URL from environment variable
NEON_DB_URL = os.getenv('NEON_DB_URL')

# Create engine with pool settings optimized for serverless
engine = create_engine(
    NEON_DB_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300  # Recycle connections after 5 minutes
)

Session = sessionmaker(bind=engine)

def check_connection():
    """Check database connection and log available tables"""
    try:
        with engine.connect() as conn:
            # Test the connection
            conn.execute(text('SELECT 1'))
            
            # Get table names
            inspector = inspect(engine)
            tables = inspector.get_table_names(schema='public')
            print(f"Successfully connected to database. Available tables: {', '.join(tables) or 'No tables found'}")
            
            # Print table schemas for debugging
            for table in tables:
                print(f"\nTable: {table}")
                for column in inspector.get_columns(table, schema='public'):
                    print(f"  {column['name']}: {column['type']}")
                    
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

# Check connection when module is imported
check_connection()

def get_schema():
    """Get schema information from Neon database"""
    inspector = inspect(engine)
    schema = {}
    
    for table_name in inspector.get_table_names(schema='public'):
        columns = []
        for column in inspector.get_columns(table_name, schema='public'):
            columns.append({
                'name': column['name'],
                'type': str(column['type']),
                'nullable': column['nullable'],
                'primary_key': column.get('primary_key', False)
            })
        schema[table_name] = columns
    
    return schema

def execute_query(query, params=None):
    """Execute a read-only query on Neon database"""
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        
        # Convert rows to dictionaries, handling special types
        rows = []
        for row in result.mappings():
            row_dict = {}
            for key, value in row.items():
                # Convert UUID to string
                if hasattr(value, 'hex'):
                    value = str(value)
                # Handle other non-serializable types here if needed
                row_dict[key] = value
            rows.append(row_dict)
            
        return rows

def validate_sql(query):
    """Basic SQL validation for Neon database"""
    # Basic validation to prevent SQL injection
    forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE']
    query_upper = query.upper()
    
    # Check for forbidden keywords
    for keyword in forbidden_keywords:
        if f' {keyword} ' in f' {query_upper} ':
            return False, f"Query contains forbidden keyword: {keyword}"
    
    # Check if it's a SELECT query (we only allow read operations)
    if not query_upper.lstrip().upper().startswith('SELECT'):
        return False, "Only SELECT queries are allowed"
    
    # Skip table existence check for now to allow more flexible queries
    # This is a trade-off between security and usability
    # In production, you might want to implement a more robust whitelist
    
    return True, ""
