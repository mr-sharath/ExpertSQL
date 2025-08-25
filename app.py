from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import openai
import json

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database configuration
DATABASE_URL = 'sqlite:///ecommerce.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# OpenAI configuration
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Get database schema for context
def get_database_schema():
    inspector = inspect(engine)
    schema = {}
    
    for table_name in inspector.get_table_names():
        columns = []
        for column in inspector.get_columns(table_name):
            columns.append({
                'name': column['name'],
                'type': str(column['type']),
                'nullable': column['nullable'],
                'primary_key': column.get('primary_key', False)
            })
        schema[table_name] = columns
    
    return schema

# Validate SQL query
def validate_sql(query):
    # Basic validation to prevent SQL injection
    forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE']
    query_upper = query.upper()
    
    for keyword in forbidden_keywords:
        if f' {keyword} ' in f' {query_upper} ':
            return False, f"Query contains forbidden keyword: {keyword}"
    
    # Check if query only uses existing tables
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    
    # This is a simple check and might need to be enhanced
    used_tables = set()
    for table in existing_tables:
        if table.upper() in query_upper:
            used_tables.add(table)
    
    if not used_tables:
        return False, "Query doesn't reference any existing tables"
    
    return True, ""

# Generate SQL from natural language
def generate_sql(natural_language):
    schema = get_database_schema()
    
    prompt = f"""
    You are a SQL expert. Given the following database schema:
    {json.dumps(schema, indent=2)}
    
    Convert the following natural language query into a SQL query:
    "{natural_language}"
    
    Return ONLY the SQL query, nothing else. The query should be compatible with SQLite.
    """
    
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that converts natural language to SQL queries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        sql_query = response.choices[0].message.content.strip()
        # Clean up the SQL query (remove code blocks if present)
        if sql_query.startswith('```sql'):
            sql_query = sql_query[6:]
        if sql_query.endswith('```'):
            sql_query = sql_query[:-3]
        
        return sql_query.strip()
    except Exception as e:
        raise Exception(f"Error generating SQL: {str(e)}")

# API endpoint for processing queries
@app.route('/query', methods=['POST'])
def process_query():
    try:
        data = request.json
        natural_language = data.get('query')
        
        if not natural_language:
            return jsonify({"error": "No query provided"}), 400
        
        # Generate SQL from natural language
        sql_query = generate_sql(natural_language)
        
        # Validate the generated SQL
        is_valid, error_message = validate_sql(sql_query)
        if not is_valid:
            return jsonify({
                "error": f"Invalid SQL query: {error_message}",
                "generated_sql": sql_query
            }), 400
        
        # Execute the query
        try:
            with engine.connect() as connection:
                result = connection.execute(text(sql_query))
                
                # Convert result to list of dictionaries
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                
                return jsonify({
                    "success": True,
                    "query": natural_language,
                    "sql": sql_query,
                    "results": rows
                })
        except Exception as e:
            return jsonify({
                "error": f"Error executing query: {str(e)}",
                "generated_sql": sql_query
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve the frontend
@app.route('/')
def index():
    return render_template('index.html')

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    # Initialize the database if it doesn't exist
    from init_db import init_db
    init_db()
    
    # Run the Flask app
    app.run(debug=True, port=5000)
